from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

from translation.extractors import (
    apply_json_updates,
    apply_python_updates,
    discover_domain_files,
    extract_files,
)
from translation.litellm_translator import LiteLLMTranslator
from translation.models import PipelineConfig, Segment, TranslationRequest
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


def _write_outputs(
    segments: list[Segment],
    translated: dict[str, str],
    output_base: Path,
) -> list[Path]:
    by_file: dict[Path, list[Segment]] = defaultdict(list)
    for segment in segments:
        by_file[segment.file_path].append(segment)

    written: list[Path] = []
    file_items = list(by_file.items())
    for src_path, file_segments in _iter_with_progress(
        file_items, label="Writing files"
    ):
        source_text = src_path.read_text(encoding="utf-8")
        kind = file_segments[0].kind
        relative_path = file_segments[0].relative_path
        dst_path = output_base / relative_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        if kind == "markdown":
            seg = file_segments[0]
            content = translated.get(seg.segment_id, seg.text)
        elif kind == "json":
            content = apply_json_updates(source_text, file_segments, translated)
        elif kind == "python":
            content = apply_python_updates(source_text, file_segments, translated)
        else:
            continue

        dst_path.write_text(content, encoding="utf-8")
        written.append(dst_path)
    return written


def run_pipeline(config: PipelineConfig) -> int:
    all_files = []
    for domain in config.domains:
        files = discover_domain_files(
            domain=domain,
            data_domains_root=config.data_domains_root,
            src_domains_root=config.src_domains_root,
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
    )
    translation_map = _build_translation_map(
        segments=segments,
        protected_terms=protected_terms,
        source_language=config.source_language,
        target_language=config.target_language,
        translator=translator,
        batch_size=config.batch_size,
    )

    output_base = config.output_root / config.target_language.lower()
    written = _write_outputs(
        segments=segments,
        translated=translation_map,
        output_base=output_base,
    )
    print(f"Wrote {len(written)} files to {output_base}")
    return 0
