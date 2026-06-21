"""Import reviewed annotation workbook -> data/tau2/domains/{d}/{lang}_loc/.

Each artefact sheet maps 1:1 to one file under ``{lang}_loc/``, preserving
the source filename + format + structure so the runtime loader picks it up
without any code change.

See ``seatau/annotation/README.md`` for the full workflow.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from seatau.annotation import addresses, manifests, markdown, validators
from seatau.annotation.python_tools import extract_tool_docstrings
from seatau.constants import DATA_DIR
from seatau.experiment_matrix import list_supported_domains
from seatau.translation.extractors import (
    apply_json_updates,
    apply_toml_updates,
    extract_files,
)
from seatau.translation.models import DomainFile

OUT_ROOT = DATA_DIR / "tau2" / "domains"
SRC_ROOT = Path("src/tau2/domains")
META_SHEETS = frozenset({"Annotation guideline", "Examples"})
DOMAINS = tuple(list_supported_domains())


@dataclass
class ImportReport:
    """Summary of one ``import_reviewed()`` run."""

    workbook: Path
    lang: str
    written: list[tuple[str, Path, int]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manifest_path: Path | None = None

    def summary(self) -> str:
        lines = [f"=== Written: {len(self.written)} files ==="]
        for sheet, path, n in self.written:
            lines.append(f"  {sheet:<40} -> {path}  ({n} rows)")
        if self.skipped:
            lines.append(f"\n=== Skipped: {len(self.skipped)} ===")
            for s in self.skipped:
                lines.append(f"  {s}")
        if self.warnings:
            lines.append(f"\n=== Warnings: {len(self.warnings)} ===")
            for w in self.warnings:
                lines.append(f"  {w}")
        if self.errors:
            lines.append(f"\n=== Errors: {len(self.errors)} ===")
            for e in self.errors:
                lines.append(f"  {e}")
        if self.manifest_path:
            lines.append(f"\nManifest: {self.manifest_path}")
        return "\n".join(lines)


@dataclass(frozen=True)
class _Resolved:
    domain: str
    kind: str  # "markdown" | "json" | "toml" | "python"
    src: Path
    out: Path


def _resolve(sheet: str, addr_filename: str, lang: str) -> _Resolved | None:
    """Map ``(sheet, first-row filename) -> (domain, source path, output path)``."""
    domain = next((d for d in DOMAINS if sheet.startswith(d + "_")), None)
    if domain is None:
        return None
    if addr_filename.endswith(".py"):
        src = SRC_ROOT / domain / addr_filename
        kind = "python"
        output_name = Path(addr_filename).stem + ".json"
    else:
        src = OUT_ROOT / domain / addr_filename
        kind = addresses.file_kind(addr_filename)
        output_name = addr_filename
    return _Resolved(
        domain=domain,
        kind=kind,
        src=src,
        out=OUT_ROOT / domain / f"{lang}_loc" / output_name,
    )


def _collect_translations(
    df: pd.DataFrame,
    seg_by_address_body: dict[str, str],  # body -> segment_id
    *,
    lang: str,
    allow_machine_fallback: bool,
) -> dict[str, str]:
    """Build ``{segment_id: final_text}`` from the workbook rows."""
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        addr = addresses.parse(row["address"])
        seg_id = seg_by_address_body.get(addr.body)
        if seg_id is None:
            continue
        value = addresses.take_final(
            row, lang, allow_machine_fallback=allow_machine_fallback
        )
        if value is None:
            continue
        out[seg_id] = str(value)
    return out


def _write_markdown(
    df: pd.DataFrame, src: Path, out: Path, lang: str, *, allow_machine_fallback: bool
) -> int:
    """Rebuild a ``.md`` file by replacing each section's body with ``name.{lang}.final``."""
    section_id_to_final: dict[str, str | None] = {}
    for _, row in df.iterrows():
        addr = addresses.parse(row["address"])
        value = addresses.take_final(
            row, lang, allow_machine_fallback=allow_machine_fallback
        )
        section_id_to_final[addr.body] = None if value is None else str(value)
    rebuilt = markdown.rejoin(
        src.read_text(encoding="utf-8"),
        {k: v for k, v in section_id_to_final.items() if v is not None},
    )
    out.write_text(rebuilt, encoding="utf-8")
    return len(df)


def _write_structured(
    df: pd.DataFrame,
    src: Path,
    out: Path,
    lang: str,
    kind: str,
    domain: str,
    *,
    allow_machine_fallback: bool,
) -> int:
    """Write a json/toml file by applying tuple-path updates to the source."""
    f = DomainFile(domain=domain, path=src, relative_path=src, kind=kind)
    res = extract_files([f])
    seg_by_body = {
        addresses.body_from_segment(s.address): s.segment_id
        for s in res.segments
        if isinstance(s.address, tuple)
    }
    translated = _collect_translations(
        df, seg_by_body, lang=lang, allow_machine_fallback=allow_machine_fallback
    )
    apply = apply_json_updates if kind == "json" else apply_toml_updates
    out.write_text(
        apply(src.read_text(encoding="utf-8"), res.segments, translated),
        encoding="utf-8",
    )
    return len(df)


def _write_python_tools(
    df: pd.DataFrame, src: Path, out: Path, lang: str, *, allow_machine_fallback: bool
) -> int:
    """Write a flat ``{function_name: docstring}`` JSON for tools.py / user_tools.py.

    Filters to the public-tool set produced by :func:`extract_tool_docstrings`,
    so the output matches what the translation pipeline would emit (no
    ``assert_*`` helpers leaking into the runtime view).
    """
    public = set(extract_tool_docstrings(src))
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        addr = addresses.parse(row["address"])
        if addr.body not in public:
            continue
        value = addresses.take_final(
            row, lang, allow_machine_fallback=allow_machine_fallback
        )
        if value is None:
            continue
        mapping[addr.body] = str(value)
    out.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(mapping)


def _write_python_schema(
    df: pd.DataFrame,
    src: Path,
    out: Path,
    lang: str,
    domain: str,
    *,
    allow_machine_fallback: bool,
) -> int:
    """Apply tuple-path updates to the baseline ``{lang}/data_model.json``.

    The schema source-of-truth is the ``.py`` file; the runtime reads JSON.
    Address tuples come from the ``.py`` extractor and resolve into the
    JSON baseline produced by the translation pipeline.
    """
    baseline = OUT_ROOT / domain / lang / out.name
    if not baseline.exists():
        raise FileNotFoundError(
            f"Schema import for {out.name} requires baseline at {baseline}. "
            f"Run `python -m seatau.translation.cli --domains {domain} --lang-id {lang} "
            "--components schema` first."
        )
    f = DomainFile(domain=domain, path=src, relative_path=src, kind="python")
    res = extract_files([f])
    tuple_segs = [s for s in res.segments if isinstance(s.address, tuple)]
    seg_by_body = {
        addresses.body_from_segment(s.address): s.segment_id for s in tuple_segs
    }
    translated = _collect_translations(
        df, seg_by_body, lang=lang, allow_machine_fallback=allow_machine_fallback
    )
    out.write_text(
        apply_json_updates(
            baseline.read_text(encoding="utf-8"), tuple_segs, translated
        ),
        encoding="utf-8",
    )
    return len(df)


def _copy_empty_sheet_source(src: Path, out: Path) -> None:
    """For sheets with 0 translatable segments, copy English source verbatim.

    Ensures ``{lang}_loc/`` is a complete overlay so the runtime sees a
    consistent directory.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, out)


def import_reviewed(
    workbook: Path,
    *,
    lang: str,
    allow_machine_fallback: bool = False,
    require_canonical_tokens: bool = True,
    require_manifest: bool = True,
) -> ImportReport:
    """Import a reviewed annotation workbook into ``data/tau2/domains/*/{lang}_loc/``.

    Args:
        workbook: Reviewer's ``annotation_{lang}.xlsx`` path.
        lang: Target language code (e.g. ``"vi"``); must match the workbook's
            column suffix.
        allow_machine_fallback: When True, rows with empty ``name.{lang}.final``
            fall back to ``name.{lang}``. Default False (production).
        require_canonical_tokens: Run the canonical-ID preservation check
            and add violations to ``report.errors``.
        require_manifest: Cross-check the annotation manifest's ``git_commit``
            against HEAD; warns on drift.

    Returns:
        :class:`ImportReport` with per-sheet outcomes plus errors/warnings
        and the path to the new ``{lang}_loc/translation_manifest.json``.
    """
    xls = pd.ExcelFile(workbook)
    report = ImportReport(workbook=workbook, lang=lang)

    if require_manifest:
        annotation_manifest = manifests.load_annotation_manifest(workbook)
        drift = validators.manifest_drift(
            annotation_manifest,
            current_git_commit=manifests.current_git_commit(),
        )
        report.warnings.extend(drift)

    # Per-domain accumulator: which output files were written, mapped to
    # their English source paths (for manifest fingerprinting).
    by_domain: dict[str, dict[str, list[Path]]] = {}

    for sheet in xls.sheet_names:
        if sheet in META_SHEETS:
            continue
        df = pd.read_excel(workbook, sheet_name=sheet)
        if len(df) == 0:
            # Empty sheet (e.g. user_db.toml has no translatable rows). Copy source verbatim.
            domain = next((d for d in DOMAINS if sheet.startswith(d + "_")), None)
            stem = sheet[len(domain) + 1 :] if domain else None
            if domain and stem:
                # Try common extensions; the translation manifest of {lang}/ tells us which.
                src_candidates = [
                    OUT_ROOT / domain / f"{stem}.toml",
                    OUT_ROOT / domain / f"{stem}.json",
                    OUT_ROOT / domain / f"{stem}.md",
                ]
                src = next((p for p in src_candidates if p.exists()), None)
                if src is not None:
                    out = OUT_ROOT / domain / f"{lang}_loc" / src.name
                    _copy_empty_sheet_source(src, out)
                    by_domain.setdefault(domain, {}).setdefault(out.name, []).append(
                        src
                    )
                    report.skipped.append(
                        f"{sheet} (0 rows; copied {src.name} from English source)"
                    )
                    continue
            report.skipped.append(f"{sheet} (0 rows; no English source resolved)")
            continue

        first_addr = addresses.parse(df.iloc[0]["address"])
        resolved = _resolve(sheet, first_addr.filename, lang)
        if resolved is None:
            report.skipped.append(f"{sheet} (cannot resolve domain)")
            continue
        if not resolved.src.exists():
            report.skipped.append(f"{sheet} (source missing: {resolved.src})")
            continue

        if not allow_machine_fallback:
            missing = validators.empty_finals(df.to_dict("records"), lang)
            if missing:
                report.errors.append(
                    f"{sheet}: {len(missing)} row(s) have empty name.{lang}.final "
                    f"(first: {missing[0]!r}). "
                    "Pass allow_machine_fallback=True to accept machine translation."
                )
                continue

        resolved.out.parent.mkdir(parents=True, exist_ok=True)
        if resolved.kind == "markdown":
            n = _write_markdown(
                df,
                resolved.src,
                resolved.out,
                lang,
                allow_machine_fallback=allow_machine_fallback,
            )
        elif resolved.kind in ("json", "toml"):
            n = _write_structured(
                df,
                resolved.src,
                resolved.out,
                lang,
                resolved.kind,
                resolved.domain,
                allow_machine_fallback=allow_machine_fallback,
            )
        elif resolved.kind == "python":
            if "data_model" in resolved.src.name:
                n = _write_python_schema(
                    df,
                    resolved.src,
                    resolved.out,
                    lang,
                    resolved.domain,
                    allow_machine_fallback=allow_machine_fallback,
                )
            else:
                n = _write_python_tools(
                    df,
                    resolved.src,
                    resolved.out,
                    lang,
                    allow_machine_fallback=allow_machine_fallback,
                )
        else:
            report.skipped.append(f"{sheet} (unsupported kind {resolved.kind})")
            continue

        if require_canonical_tokens:
            violations = validators.canonical_tokens_preserved(
                resolved.src.read_text(encoding="utf-8"),
                resolved.out.read_text(encoding="utf-8"),
                sheet=sheet,
            )
            report.errors.extend(violations)

        report.written.append((sheet, resolved.out, n))
        by_domain.setdefault(resolved.domain, {}).setdefault(
            resolved.out.name, []
        ).append(resolved.src)

    # Write per-language translation manifests, one per domain touched.
    annotation_meta = manifests.load_annotation_manifest(workbook) or {}
    reviewer = (
        (annotation_meta.get("reviewer") or {}).get("id") if annotation_meta else None
    )
    round_id = (
        (annotation_meta.get("localization_round") or {}).get("id")
        if annotation_meta
        else None
    )
    last_path: Path | None = None
    for domain, asset_to_sources in by_domain.items():
        out_dir = OUT_ROOT / domain / f"{lang}_loc"
        last_path = manifests.write_translation_manifest(
            out_dir,
            domain=domain,
            lang=lang,
            asset_to_sources=asset_to_sources,
            reviewer=reviewer,
            round_id=round_id,
        )
    report.manifest_path = last_path

    return report
