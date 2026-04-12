from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from docstring_parser import DocstringStyle
from docstring_parser import parse as parse_docstring

from translation.extractors import (
    apply_json_updates,
    apply_toml_updates,
    discover_domain_files,
    extract_files,
)
from translation.language import TRANSLATION_MANIFEST_NAME
from translation.litellm_translator import LiteLLMTranslator
from translation.models import PipelineConfig, Segment, TranslationRequest
from translation.paths import to_project_relative_path
from translation.protect import mask_protected_tokens, unmask_protected_tokens

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


def _build_translation_map(
    segments: list[Segment],
    protected_terms: set[str],
    source_language: str,
    target_language: str,
    translator: LiteLLMTranslator,
    batch_size: int,
) -> dict[str, str]:
    translated: dict[str, str] = {}
    batches = _chunked(segments, size=batch_size)

    for batch in _iter_with_progress(batches, label="Translating batches"):
        requests: list[TranslationRequest] = []
        masked_lookup = {}
        for segment in batch:
            masked = mask_protected_tokens(
                segment.text, protected_terms=protected_terms
            )
            masked_lookup[segment.segment_id] = masked
            requests.append(
                TranslationRequest(segment_id=segment.segment_id, text=masked.text)
            )
        batch_out = translator.translate_batch(
            requests=requests,
            source_language=source_language,
            target_language=target_language,
        )
        for segment_id, translated_masked_text in batch_out.items():
            translated[segment_id] = unmask_protected_tokens(
                translated_masked_text, masked_lookup[segment_id]
            )

    return translated


def _component_for_segment(segment: Segment) -> str:
    if segment.kind == "python":
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
        source_text = src_path.read_text(encoding="utf-8")
        kind = file_segments[0].kind
        domain = file_segments[0].domain
        filename = src_path.name
        component = _component_for_segment(file_segments[0])

        # All outputs go to data/tau2/domains/{domain}/{lang_id}/{filename}
        dst_dir = data_domains_root / domain / lang_id
        manifest_path = dst_dir / TRANSLATION_MANIFEST_NAME

        if kind == "markdown":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            seg = file_segments[0]
            dst_path.write_text(
                translated.get(seg.segment_id, seg.text), encoding="utf-8"
            )
        elif kind == "json":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            content = apply_json_updates(source_text, file_segments, translated)
            dst_path.write_text(content, encoding="utf-8")
        elif kind == "toml":
            dst_path = dst_dir / filename
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            content = apply_toml_updates(source_text, file_segments, translated)
            dst_path.write_text(content, encoding="utf-8")
        elif kind == "python":
            tools_by_name: dict[str, list[Segment]] = defaultdict(list)
            for seg in file_segments:
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
                    rebuilt = _reconstruct_tool_docstring(source_doc, translated_parts)
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
            dst_path = dst_dir / (src_path.stem + ".json")
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(
                json.dumps(doc_map, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        else:
            continue
        written.append(dst_path)
        manifest_updates[manifest_path][dst_path.name] = _build_asset_metadata(
            src_path=src_path,
            dst_path=dst_path,
            component=component,
            config=config,
        )
    return written, manifest_updates


def run_pipeline(config: PipelineConfig) -> int:
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

    if not segments:
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

    api_key = os.getenv(config.api_key_env, "").strip()
    if not api_key:
        raise RuntimeError(
            f"Missing API key env var: {config.api_key_env}. "
            f"Set it before running translation."
        )

    translator = LiteLLMTranslator(
        model=config.model,
        api_key=api_key,
        api_base=config.api_base,
        api_version=config.api_version,
        max_rpm=config.max_rpm,
        timeout_s=config.timeout_s,
        retries=config.retries,
    )
    translation_map = _build_translation_map(
        segments=segments,
        protected_terms=protected_terms,
        source_language=config.source_language,
        target_language=config.target_language,
        translator=translator,
        batch_size=config.batch_size,
    )

    written, manifest_updates = _write_outputs(
        segments=segments,
        translated=translation_map,
        data_domains_root=config.data_domains_root,
        lang_id=config.lang_id,
        config=config,
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
