"""Read/write annotation + translation manifests.

Two manifest files are involved in a round-trip:

1. ``data/seatau/annotations/<workbook>.manifest.yaml`` — written by export,
   read by import for drift detection (reviewer, round_id, git_commit).
2. ``data/tau2/domains/{domain}/{lang}/translation_manifest.json`` —
   updated by import so the runtime's stale-warning machinery can compare
   reviewed translated assets to current English source.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

import paths as path_defs

TRANSLATION_MANIFEST_NAME = "translation_manifest.json"
REVIEWED_TRANSLATION_PIPELINE = "human-reviewed-translation"


def current_git_commit() -> str | None:
    """Return ``git rev-parse HEAD``, or ``None`` outside a checkout."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def sha256(path: Path) -> str:
    """SHA-256 of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def annotation_manifest_path(
    workbook: Path, *, manifest_dir: Path | None = None
) -> Path:
    """Resolve the YAML manifest path for a workbook stem."""
    base = manifest_dir or path_defs.resolve_project_path(
        path_defs.ANNOTATION_MANIFEST_DIR
    )
    return base / f"{workbook.stem}.manifest.yaml"


def load_annotation_manifest(
    workbook: Path, *, manifest_dir: Path | None = None
) -> dict | None:
    """Load the annotation YAML manifest if present."""
    path = annotation_manifest_path(workbook, manifest_dir=manifest_dir)
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_annotation_manifest(
    workbook: Path,
    *,
    reviewer: str,
    round_id: str,
    lang: str,
    domains: list[str],
    data_domains_root: Path,
    src_domains_root: Path,
    sheet_rows: dict[str, int],
    missing_translations: list[str],
    manifest_dir: Path | None = None,
    language_registry_path: Path | str | None = None,
) -> Path:
    """Write the YAML manifest that the importer cross-checks for drift."""
    base = manifest_dir or path_defs.resolve_project_path(
        path_defs.ANNOTATION_MANIFEST_DIR
    )
    base.mkdir(parents=True, exist_ok=True)
    manifest_path = base / f"{workbook.stem}.manifest.yaml"

    body: dict[str, Any] = {
        "manifest_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "reviewer": {"id": reviewer},
        "review_round": {"id": round_id},
        "language": {"code": lang},
        "domains": sorted(domains),
        "workbook": {
            "path": str(workbook),
            "sheet_count": len(sheet_rows) + 2,  # + guideline + examples
        },
        "source": {
            "data_domains_root": str(data_domains_root),
            "src_domains_root": str(src_domains_root),
            "language_registry": str(language_registry_path)
            if language_registry_path
            else None,
            "git_commit": current_git_commit(),
        },
        "artifacts": {
            "sheet_rows": dict(sheet_rows),
            "missing_translations": missing_translations,
        },
    }
    manifest_path.write_text(
        yaml.safe_dump(body, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest_path


def write_translation_manifest(
    out_dir: Path,
    *,
    domain: str,
    lang: str,
    asset_to_sources: dict[str, list[Path]],
    pipeline: str = REVIEWED_TRANSLATION_PIPELINE,
    reviewer: str | None = None,
    round_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``{lang}/translation_manifest.json`` with current source SHAs.

    Args:
        out_dir: ``data/tau2/domains/{domain}/{lang}/`` (must exist).
        domain: Domain name (recorded in manifest body).
        lang: Language code (recorded in manifest body).
        asset_to_sources: ``{output_filename: [english_source_path, ...]}``.
            One entry per file the importer just wrote.
        pipeline: Provenance label (default ``human-reviewed-translation``).
        reviewer: Reviewer ID from the annotation manifest.
        round_id: Review round ID from the annotation manifest.
        extra: Optional extra keys merged into the top-level body.

    Returns:
        Path to the manifest file written.
    """
    now = datetime.now(UTC).isoformat()
    assets: dict[str, dict[str, Any]] = {}
    for output_name, source_paths in asset_to_sources.items():
        source_records: list[dict[str, str]] = []
        for source_path in source_paths:
            if not source_path.exists():
                continue
            try:
                rel = source_path.relative_to(path_defs.PROJECT_ROOT)
            except ValueError:
                rel = source_path
            source_records.append({"path": str(rel), "sha256": sha256(source_path)})
        assets[output_name] = {
            "output_file": output_name,
            "pipeline": pipeline,
            "source_language": "English",
            "target_language": lang,
            "translated_at": now,
            "source_files": source_records,
        }

    body: dict[str, Any] = {
        "pipeline": pipeline,
        "domain": domain,
        "language": lang,
        "generated_at": now,
        "assets": assets,
    }
    if reviewer:
        body["reviewer"] = reviewer
    if round_id:
        body["review_round_id"] = round_id
    if extra:
        body.update(extra)

    out_path = out_dir / TRANSLATION_MANIFEST_NAME
    out_path.write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out_path
