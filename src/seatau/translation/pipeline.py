from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from docstring_parser import DocstringStyle
from docstring_parser import parse as parse_docstring

from seatau.constants import to_project_relative_path
from seatau.translation.config import (
    DB_FILE_NAMES,
    DEFAULT_VERTEX_MODEL,
    SCHEMA_PYTHON_FILES,
    TOOL_DOC_PROTECTED_TERMS,
    TOOL_RETURN_FILE_NAMES,
)
from seatau.translation.extractors import (
    _template_to_pattern,
    apply_json_updates,
    apply_toml_updates,
    build_schema_artifact,
    discover_domain_files,
    extract_files,
)
from seatau.translation.language import TRANSLATION_MANIFEST_NAME
from seatau.translation.litellm_translator import LiteLLMTranslator
from seatau.translation.models import (
    DomainFile,
    PipelineConfig,
    Segment,
    TranslationRequest,
)
from seatau.translation.protect import (
    mask_segment_protected_tokens,
    mask_terms_with_replacements,
    unmask_protected_tokens,
)

T = TypeVar("T")


def _chunked(items: list[T], size: int) -> list[list[T]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _iter_with_progress(items: list[T], label: str):
    total = len(items)
    width = 24
    for idx, item in enumerate(items, start=1):
        filled = int((idx / total) * width) if total else width
        bar = "#" * filled + "-" * (width - filled)
        print(f"{label} [{bar}] {idx}/{total}", end="\r", flush=True)
        yield item
    print(f"{label} [{'#' * width}] {total}/{total}")


def _iter_completed_with_progress(futures, label: str, total: int):
    width = 24
    for idx, future in enumerate(as_completed(futures), start=1):
        filled = int((idx / total) * width) if total else width
        bar = "#" * filled + "-" * (width - filled)
        print(f"{label} [{bar}] {idx}/{total}", end="\r", flush=True)
        yield future
    print(f"{label} [{'#' * width}] {total}/{total}")


def _build_translation_map(
    segments: list[Segment],
    protected_terms: set[str],
    source_language: str,
    target_language: str,
    translator: LiteLLMTranslator,
    batch_size: int,
    max_concurrency: int = 1,
    domain_literal_maps: dict[str, dict[str, str]] | None = None,
) -> dict[str, str]:
    domain_literal_maps = domain_literal_maps or {}

    def literal_map_for_segment(segment: Segment) -> dict[str, str]:
        if segment.translate_runtime_labels:
            return {}
        return domain_literal_maps.get(segment.domain, {})

    def dedup_id(segment: Segment, masked_text: str) -> str:
        if segment.domain != "telecom" or segment.file_path.name != "tasks.json":
            return segment.segment_id
        address = segment.address
        if isinstance(address, tuple):
            if address and address[0].isdigit():
                pattern = "/".join(address[1:])
            else:
                pattern = "/".join(address)
        else:
            pattern = str(address)
        digest = hashlib.sha256(f"{pattern}\n{masked_text}".encode("utf-8")).hexdigest()
        return f"telecom_tasks::{digest}"

    translated: dict[str, str] = {}
    masked_lookup = {}
    request_to_segments: dict[str, list[str]] = defaultdict(list)
    request_map: dict[str, TranslationRequest] = {}
    request_modes: dict[str, bool] = {}

    for segment in segments:
        literal_map = literal_map_for_segment(segment)

        effective_protected_terms = (
            set() if segment.translate_runtime_labels else protected_terms
        )
        if _component_for_segment(segment) == "tools":
            effective_protected_terms = set(effective_protected_terms) | set(
                TOOL_DOC_PROTECTED_TERMS
            )
        if literal_map:
            literal_masked = mask_terms_with_replacements(segment.text, literal_map)
            masked_segment = Segment(
                segment_id=segment.segment_id,
                domain=segment.domain,
                file_path=segment.file_path,
                relative_path=segment.relative_path,
                kind=segment.kind,
                address=segment.address,
                text=literal_masked.text,
                name=segment.name,
                source_text=segment.source_text,
                python_doc_key=segment.python_doc_key,
                translate_runtime_labels=segment.translate_runtime_labels,
            )
            masked = mask_segment_protected_tokens(
                masked_segment,
                protected_terms=effective_protected_terms - set(literal_map),
                initial_placeholders=literal_masked.placeholders,
                initial_restorations=literal_masked.restorations,
            )
        else:
            masked = mask_segment_protected_tokens(
                segment,
                protected_terms=effective_protected_terms,
            )
        masked_lookup[segment.segment_id] = masked
        mode_prefix = "literal" if segment.translate_runtime_labels else "standard"
        request_id = f"{mode_prefix}::{dedup_id(segment, masked.text)}"
        request_to_segments[request_id].append(segment.segment_id)
        if request_id not in request_map:
            request_map[request_id] = TranslationRequest(
                segment_id=request_id,
                text=masked.text,
                literal_map=literal_map,
            )
            request_modes[request_id] = segment.translate_runtime_labels

    requests = list(request_map.values())
    if len(requests) < len(segments):
        print(f"Deduplicated translation requests: {len(segments)} -> {len(requests)}")

    def translate_requests_group(
        grouped_requests: list[TranslationRequest],
        *,
        batch_protected_terms: set[str],
        translate_runtime_labels: bool,
    ) -> None:
        if not grouped_requests:
            return
        batches = _chunked(grouped_requests, size=batch_size)
        label = (
            "Translating literal batches"
            if translate_runtime_labels
            else "Translating batches"
        )

        def restore_request_output(
            request: TranslationRequest,
            translated_masked_text: str,
        ) -> None:
            segment_ids = request_to_segments[request.segment_id]

            def restore_from_masked_output(masked_text: str) -> None:
                for segment_id in segment_ids:
                    translated_text = unmask_protected_tokens(
                        masked_text,
                        masked_lookup[segment_id],
                    )
                    translated[segment_id] = translated_text

            try:
                restore_from_masked_output(translated_masked_text)
            except ValueError as exc:
                single_out = translator.translate_batch(
                    requests=[request],
                    source_language=source_language,
                    target_language=target_language,
                    protected_terms=batch_protected_terms,
                    translate_runtime_labels=translate_runtime_labels,
                )
                retried_masked_text = single_out[request.segment_id]
                try:
                    restore_from_masked_output(retried_masked_text)
                    print(
                        "Recovered placeholder-loss by retrying request individually: "
                        f"{request.segment_id} ({exc})"
                    )
                except ValueError as retry_exc:
                    exemplar_segment_id = segment_ids[0]
                    localized_source_text = unmask_protected_tokens(
                        request.text,
                        masked_lookup[exemplar_segment_id],
                    )
                    fallback_out = translator.translate_batch(
                        requests=[
                            TranslationRequest(
                                segment_id=request.segment_id,
                                text=localized_source_text,
                            )
                        ],
                        source_language=source_language,
                        target_language=target_language,
                        protected_terms=batch_protected_terms,
                        translate_runtime_labels=translate_runtime_labels,
                    )
                    fallback_text = fallback_out[request.segment_id]
                    for segment_id in segment_ids:
                        translated[segment_id] = fallback_text
                    print(
                        "Recovered placeholder-loss by retrying request with "
                        "localized source text: "
                        f"{request.segment_id} ({retry_exc})"
                    )

        if max_concurrency <= 1:
            batch_iter = (
                (
                    batch,
                    translator.translate_batch(
                        requests=batch,
                        source_language=source_language,
                        target_language=target_language,
                        protected_terms=batch_protected_terms,
                        translate_runtime_labels=translate_runtime_labels,
                    ),
                )
                for batch in _iter_with_progress(batches, label=label)
            )
        else:
            worker_count = min(max_concurrency, len(batches))
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                future_to_batch = {
                    executor.submit(
                        translator.translate_batch,
                        requests=batch,
                        source_language=source_language,
                        target_language=target_language,
                        protected_terms=batch_protected_terms,
                        translate_runtime_labels=translate_runtime_labels,
                    ): batch
                    for batch in batches
                }
                batch_iter = (
                    (future_to_batch[future], future.result())
                    for future in _iter_completed_with_progress(
                        future_to_batch,
                        label=label,
                        total=len(future_to_batch),
                    )
                )

        for batch, batch_out in batch_iter:
            for request in batch:
                restore_request_output(
                    request,
                    batch_out[request.segment_id],
                )

    translate_requests_group(
        [request for request in requests if not request_modes[request.segment_id]],
        batch_protected_terms=protected_terms,
        translate_runtime_labels=False,
    )
    translate_requests_group(
        [request for request in requests if request_modes[request.segment_id]],
        batch_protected_terms=set(),
        translate_runtime_labels=True,
    )

    return translated


def _iter_localized_value_entries(node: Any):
    if isinstance(node, dict):
        value_sets = node.get("value_sets")
        if isinstance(value_sets, dict):
            for value_set in value_sets.values():
                if not isinstance(value_set, dict):
                    continue
                values = value_set.get("values")
                if not isinstance(values, list):
                    continue
                for entry in values:
                    if isinstance(entry, dict):
                        yield entry


def _literal_aliases(canonical: str) -> set[str]:
    aliases = {canonical}
    if "_" not in canonical:
        return aliases

    spaced = canonical.replace("_", " ")
    hyphenated = canonical.replace("_", "-")
    aliases.update({spaced, hyphenated, spaced.title(), hyphenated.title()})
    return aliases


def _extract_literal_map_from_schema_artifact(
    artifact: dict[str, Any],
) -> dict[str, str]:
    literal_map: dict[str, str] = {}
    for entry in _iter_localized_value_entries(artifact):
        canonical = entry.get("canonical")
        localized = entry.get("localized")
        if (
            isinstance(canonical, str)
            and isinstance(localized, str)
            and canonical.strip()
            and localized.strip()
            and canonical != localized
        ):
            for alias in _literal_aliases(canonical):
                literal_map.setdefault(alias, localized)
    return literal_map


def _build_literal_maps_from_schema_translation(
    *,
    schema_files: list[DomainFile],
    schema_segments: list[Segment],
    translated: dict[str, str],
) -> dict[str, dict[str, str]]:
    literal_maps: dict[str, dict[str, str]] = {}
    segments_by_file: dict[Path, list[Segment]] = defaultdict(list)
    for segment in schema_segments:
        segments_by_file[segment.file_path].append(segment)

    for schema_file in schema_files:
        schema_artifact, _ = build_schema_artifact(schema_file)
        localized_artifact = json.loads(
            apply_json_updates(
                json.dumps(schema_artifact, ensure_ascii=False, indent=2) + "\n",
                segments_by_file.get(schema_file.path, []),
                translated,
            )
        )
        literal_map = _extract_literal_map_from_schema_artifact(localized_artifact)
        if literal_map:
            literal_maps[schema_file.domain] = literal_map
    return literal_maps


def _load_existing_literal_maps(
    *,
    domains: list[str],
    data_domains_root: Path,
    lang_id: str,
) -> dict[str, dict[str, str]]:
    literal_maps: dict[str, dict[str, str]] = {}
    for domain in domains:
        domain_map: dict[str, str] = {}
        for filename in ("data_model.json", "user_data_model.json"):
            path = data_domains_root / domain / lang_id / filename
            if not path.exists():
                continue
            artifact = json.loads(path.read_text(encoding="utf-8"))
            domain_map.update(_extract_literal_map_from_schema_artifact(artifact))
        if domain_map:
            literal_maps[domain] = domain_map
    return literal_maps


def _validate_vertex_environment(model: str) -> None:
    if model.strip() != DEFAULT_VERTEX_MODEL:
        raise RuntimeError(
            "Translation must use the Vertex AI route "
            f"{DEFAULT_VERTEX_MODEL}. Do not pass provider aliases or alternate "
            "Gemini model spellings."
        )
    if importlib.util.find_spec("google.auth") is None:
        raise RuntimeError(
            "Vertex translation requires the Google auth runtime packages. "
            "Run `uv sync` after installing project dependencies, then authenticate "
            "with gcloud/ADC."
        )
    missing = [
        name
        for name in ("VERTEXAI_PROJECT", "VERTEXAI_LOCATION")
        if not os.getenv(name, "").strip()
    ]
    if missing:
        raise RuntimeError(
            "Missing Vertex AI environment variable(s): "
            + ", ".join(missing)
            + ". Authenticate with gcloud/ADC and set VERTEXAI_PROJECT and "
            "VERTEXAI_LOCATION before running translation."
        )


def _component_for_segment(segment: Segment) -> str:
    if segment.kind == "tool_returns":
        return "tools"
    if segment.kind == "python":
        if segment.file_path.name in {"tools.py", "user_tools.py"}:
            return "tools"
        return "schema"
    if segment.file_path.name in TOOL_RETURN_FILE_NAMES:
        return "tools"
    if segment.kind == "markdown":
        return "policy"
    if segment.file_path.name.startswith("tasks"):
        return "tasks"
    return "db"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {"assets": {}}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _build_asset_metadata(
    src_path: Path,
    dst_path: Path,
    component: str,
    config: PipelineConfig,
) -> dict:
    return {
        "component": component,
        "output_file": dst_path.name,
        "model": config.model,
        "source_language": config.source_language,
        "target_language": config.target_language,
        "translated_at": datetime.now(UTC).isoformat(),
        "source_files": [
            {
                "path": to_project_relative_path(src_path).as_posix(),
                "sha256": _sha256(src_path),
            }
        ],
    }


def _split_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.strip().splitlines()]


def _format_keyed_entry(key: str, description: str) -> list[str]:
    lines = _split_lines(description)
    if not lines:
        return [f"    {key}:"]
    rendered = [f"    {key}: {lines[0]}"]
    rendered.extend(f"        {line}" for line in lines[1:])
    return rendered


def _format_indented_block(description: str) -> list[str]:
    lines = _split_lines(description)
    if not lines:
        return ["    "]
    return [f"    {line}" for line in lines]


def _reconstruct_tool_docstring(
    source_docstring: str,
    translated_parts: dict[str, str],
) -> str:
    if not source_docstring.strip():
        return ""

    doc = parse_docstring(source_docstring, style=DocstringStyle.GOOGLE)
    sections: list[str] = []

    short = translated_parts.get("short", doc.short_description or "").strip()
    long = translated_parts.get("long", doc.long_description or "").strip()
    if short:
        sections.append(short)
    if long:
        sections.append(long)

    args_lines: list[str] = []
    for param in doc.params:
        original_desc = (param.description or "").strip()
        desc = translated_parts.get(f"param:{param.arg_name}", original_desc).strip()
        if not desc:
            continue
        label = (
            f"{param.arg_name} ({param.type_name})"
            if param.type_name
            else param.arg_name
        )
        args_lines.extend(_format_keyed_entry(label, desc))
    if args_lines:
        sections.append("\n".join(["Args:", *args_lines]))

    if doc.returns:
        original_desc = (doc.returns.description or "").strip()
        desc = translated_parts.get("returns", original_desc).strip()
        if desc:
            if doc.returns.type_name:
                returns_lines = _format_keyed_entry(doc.returns.type_name, desc)
            else:
                returns_lines = _format_indented_block(desc)
            sections.append("\n".join(["Returns:", *returns_lines]))

    raises_lines: list[str] = []
    for idx, exc in enumerate(doc.raises):
        original_desc = (exc.description or "").strip()
        desc = translated_parts.get(f"raises:{idx}", original_desc).strip()
        if not desc:
            continue
        label = exc.type_name or "Exception"
        raises_lines.extend(_format_keyed_entry(label, desc))
    if raises_lines:
        sections.append("\n".join(["Raises:", *raises_lines]))

    return "\n\n".join(section for section in sections if section.strip())


def _write_manifest(
    manifest_updates: dict[Path, dict[str, dict]],
) -> list[Path]:
    manifest_paths: list[Path] = []
    for manifest_path, asset_updates in manifest_updates.items():
        manifest = _load_manifest(manifest_path)
        assets = manifest.setdefault("assets", {})
        assets.update(asset_updates)
        manifest["generated_at"] = datetime.now(UTC).isoformat()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest_paths.append(manifest_path)
    return manifest_paths


def _write_outputs(
    segments: list[Segment],
    translated: dict[str, str],
    data_domains_root: Path,
    lang_id: str,
    config: PipelineConfig,
    all_files: list[DomainFile] | None = None,
) -> tuple[list[Path], dict[Path, dict[str, dict]]]:
    by_file: dict[Path, list[Segment]] = defaultdict(list)
    for segment in segments:
        by_file[segment.file_path].append(segment)

    written: list[Path] = []
    manifest_updates: dict[Path, dict[str, dict]] = defaultdict(dict)
    file_items = list(by_file.items())
    for src_path, file_segments in _iter_with_progress(
        file_items, label="Writing files"
    ):
        domain = file_segments[0].domain
        filename = src_path.name
        dst_dir = data_domains_root / domain / lang_id
        manifest_path = dst_dir / TRANSLATION_MANIFEST_NAME

        # tool_returns segments (from TOOL_RETURN_MESSAGES in tools.py) may be
        # mixed with python docstring segments; handle them as a separate output.
        tool_return_segs = [s for s in file_segments if s.kind == "tool_returns"]
        regular_segs = [s for s in file_segments if s.kind != "tool_returns"]

        if tool_return_segs:
            tr_dst = dst_dir / "tool_returns.json"
            tr_dst.parent.mkdir(parents=True, exist_ok=True)
            exact_section: dict[str, dict[str, str]] = {}
            templates_section: dict[str, Any] = {}
            for seg in tool_return_segs:
                assert isinstance(seg.address, tuple) and len(seg.address) == 2
                section_key, msg_key = seg.address[0], seg.address[1]
                localized_text = translated.get(seg.segment_id, seg.text)
                if section_key == "exact":
                    exact_section[msg_key] = {
                        "source": seg.text,
                        "localized": localized_text,
                    }
                elif section_key == "templates":
                    templates_section[msg_key] = {
                        "pattern": _template_to_pattern(seg.text),
                        "source": seg.text,
                        "localized": localized_text,
                    }
            tr_output: dict[str, Any] = {}
            if exact_section:
                tr_output["exact"] = exact_section
            if templates_section:
                tr_output["templates"] = templates_section
            tr_dst.write_text(
                json.dumps(tr_output, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written.append(tr_dst)
            manifest_updates[manifest_path][tr_dst.name] = _build_asset_metadata(
                src_path=src_path,
                dst_path=tr_dst,
                component="tools",
                config=config,
            )

        if not regular_segs:
            continue

        source_text = src_path.read_text(encoding="utf-8")
        kind = regular_segs[0].kind
        component = _component_for_segment(regular_segs[0])
        if filename in TOOL_RETURN_FILE_NAMES:
            component = "tools"

        dst_path: Path
        if kind == "markdown":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            seg = regular_segs[0]
            dst_path.write_text(
                translated.get(seg.segment_id, seg.text), encoding="utf-8"
            )
        elif kind == "json":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            content = apply_json_updates(source_text, regular_segs, translated)
            dst_path.write_text(content, encoding="utf-8")
        elif kind == "toml":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            content = apply_toml_updates(source_text, regular_segs, translated)
            dst_path.write_text(content, encoding="utf-8")
        elif kind == "python":
            dst_path = dst_dir / (src_path.stem + ".json")
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.name in {"tools.py", "user_tools.py"}:
                tools_by_name: dict[str, list[Segment]] = defaultdict(list)
                for seg in regular_segs:
                    if (
                        seg.name is None
                        or not seg.name[0].islower()
                        or seg.name.startswith("_")
                    ):
                        continue
                    tools_by_name[seg.name].append(seg)

                doc_map: dict[str, str] = {}
                for tool_name, tool_segments in tools_by_name.items():
                    structured_segments = [
                        seg for seg in tool_segments if seg.python_doc_key is not None
                    ]
                    if structured_segments:
                        source_doc = next(
                            (
                                seg.source_text
                                for seg in structured_segments
                                if seg.source_text is not None
                            ),
                            "",
                        )
                        translated_parts = {
                            seg.python_doc_key: translated.get(seg.segment_id, seg.text)
                            for seg in structured_segments
                            if seg.python_doc_key is not None
                        }
                        rebuilt = _reconstruct_tool_docstring(
                            source_doc, translated_parts
                        )
                        if rebuilt:
                            doc_map[tool_name] = rebuilt
                        continue

                    # Backward-compat path for pre-structured extracted segments.
                    for seg in tool_segments:
                        if seg.segment_id in translated:
                            doc_map[tool_name] = translated[seg.segment_id]
                            break
                if not doc_map:
                    continue
                dst_path.write_text(
                    json.dumps(doc_map, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            else:
                schema_file = DomainFile(
                    domain=domain,
                    path=src_path,
                    relative_path=regular_segs[0].relative_path,
                    kind="python",
                )
                schema_artifact, _ = build_schema_artifact(schema_file)
                content = apply_json_updates(
                    json.dumps(schema_artifact, ensure_ascii=False, indent=2) + "\n",
                    regular_segs,
                    translated,
                )
                dst_path.write_text(content, encoding="utf-8")
        else:
            continue
        written.append(dst_path)
        manifest_updates[manifest_path][dst_path.name] = _build_asset_metadata(
            src_path=src_path,
            dst_path=dst_path,
            component=component,
            config=config,
        )

    # Ensure DB artifacts with zero extracted segments are still emitted so
    # translated domain folders remain complete (e.g., telecom/user_db.toml).
    if all_files is not None:
        translated_sources = set(by_file.keys())
        for domain_file in all_files:
            if domain_file.path in translated_sources:
                continue
            if domain_file.path.name not in DB_FILE_NAMES:
                continue
            if domain_file.kind not in {"json", "toml"}:
                continue

            src_path = domain_file.path
            dst_dir = data_domains_root / domain_file.domain / lang_id
            dst_path = dst_dir / src_path.name
            manifest_path = dst_dir / TRANSLATION_MANIFEST_NAME

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_bytes(src_path.read_bytes())
            written.append(dst_path)
            manifest_updates[manifest_path][dst_path.name] = _build_asset_metadata(
                src_path=src_path,
                dst_path=dst_path,
                component="db",
                config=config,
            )
    return written, manifest_updates


def run_pipeline(config: PipelineConfig) -> int:
    _validate_vertex_environment(config.model)
    all_files = []
    for domain in config.domains:
        files = discover_domain_files(
            domain=domain,
            data_domains_root=config.data_domains_root,
            src_domains_root=config.src_domains_root,
            components=config.components,
        )
        all_files.extend(files)

    if not all_files:
        print("No files found for selected domains.")
        return 1

    extracted = extract_files(all_files)
    segments = extracted.segments
    protected_terms = extracted.protected_terms

    db_only_files = [
        file
        for file in all_files
        if file.path.name in DB_FILE_NAMES and file.kind in {"json", "toml"}
    ]

    if not segments:
        if db_only_files and len(db_only_files) == len(all_files):
            print(
                "No translatable DB segments found. "
                "Copying DB artifacts through to translated output."
            )
            written, manifest_updates = _write_outputs(
                segments=[],
                translated={},
                data_domains_root=config.data_domains_root,
                lang_id=config.lang_id,
                config=config,
                all_files=all_files,
            )
            manifest_paths = _write_manifest(manifest_updates)
            output_dir = config.data_domains_root / "*" / config.lang_id
            print(f"Wrote {len(written)} files to {output_dir}")
            print(
                "Recorded source fingerprints in "
                f"{len(manifest_paths)} manifest file(s). "
                "If source tools/context change later, rerun translation."
            )
            return 0
        print("No translatable segments found.")
        return 1

    print(f"Found {len(segments)} segments across {len(all_files)} files.")
    print(f"Protected terms collected: {len(protected_terms)}")

    if config.dry_run:
        print("Dry run enabled. Preview:")
        for segment in segments[: config.max_preview]:
            print(f"- [{segment.relative_path}] {segment.segment_id}")
            print(f"  {segment.text[:180]!r}")
        return 0

    translator = LiteLLMTranslator(
        model=config.model,
        timeout_s=config.timeout_s,
        retries=config.retries,
    )
    schema_files = [
        file
        for file in all_files
        if file.kind == "python" and file.path.name in SCHEMA_PYTHON_FILES
    ]
    schema_segments = [
        segment for segment in segments if _component_for_segment(segment) == "schema"
    ]
    nonschema_segments = [
        segment for segment in segments if _component_for_segment(segment) != "schema"
    ]

    translation_map: dict[str, str] = {}
    domain_literal_maps = _load_existing_literal_maps(
        domains=config.domains,
        data_domains_root=config.data_domains_root,
        lang_id=config.lang_id,
    )

    if schema_segments:
        schema_label_segments = [
            segment for segment in schema_segments if segment.translate_runtime_labels
        ]
        schema_prose_segments = [
            segment
            for segment in schema_segments
            if not segment.translate_runtime_labels
        ]

        if schema_label_segments:
            translation_map.update(
                _build_translation_map(
                    segments=schema_label_segments,
                    protected_terms=protected_terms,
                    source_language=config.source_language,
                    target_language=config.target_language,
                    translator=translator,
                    batch_size=config.batch_size,
                    max_concurrency=config.max_concurrency,
                )
            )

        domain_literal_maps.update(
            _build_literal_maps_from_schema_translation(
                schema_files=schema_files,
                schema_segments=schema_segments,
                translated=translation_map,
            )
        )

        if schema_prose_segments:
            translation_map.update(
                _build_translation_map(
                    segments=schema_prose_segments,
                    protected_terms=protected_terms,
                    source_language=config.source_language,
                    target_language=config.target_language,
                    translator=translator,
                    batch_size=config.batch_size,
                    domain_literal_maps=domain_literal_maps,
                    max_concurrency=config.max_concurrency,
                )
            )

    if nonschema_segments:
        translation_map.update(
            _build_translation_map(
                segments=nonschema_segments,
                protected_terms=protected_terms,
                source_language=config.source_language,
                target_language=config.target_language,
                translator=translator,
                batch_size=config.batch_size,
                domain_literal_maps=domain_literal_maps,
                max_concurrency=config.max_concurrency,
            )
        )

    written, manifest_updates = _write_outputs(
        segments=segments,
        translated=translation_map,
        data_domains_root=config.data_domains_root,
        lang_id=config.lang_id,
        config=config,
        all_files=all_files,
    )
    manifest_paths = _write_manifest(manifest_updates)
    output_dir = config.data_domains_root / "*" / config.lang_id
    print(f"Wrote {len(written)} files to {output_dir}")
    print(
        "Recorded source fingerprints in "
        f"{len(manifest_paths)} manifest file(s). "
        "If source tools/context change later, rerun translation."
    )
    return 0
