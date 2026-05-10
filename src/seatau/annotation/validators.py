"""Validation rules for the annotation import pipeline.

Each rule returns a list of human-readable error strings. A non-empty list
means the rule fired; the importer aggregates them per-sheet and either
errors or warns depending on the chosen policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from seatau.annotation import addresses

# Tokens we expect to round-trip verbatim from English source into the
# localized output. These are conservative: snake_case identifiers and
# common ID shapes used across tau2 domains. They never carry prose.
_SNAKE_CASE_RE = re.compile(r"\b[a-z][a-z0-9_]{2,}\b")
_ID_PATTERNS = (
    re.compile(r"#W\d{6,}"),  # retail order IDs
    re.compile(r"\bgift_card_\d+\b"),
    re.compile(r"\bcredit_card_\d+\b"),
    re.compile(r"\bP\d{4,}\b"),  # telecom plan IDs
)


def empty_finals(rows: Iterable[dict], lang: str) -> list[str]:
    """Return addresses with empty ``name.{lang}.final`` (i.e. unreviewed rows)."""
    missing: list[str] = []
    for row in rows:
        if addresses.is_blank(row.get(f"name.{lang}.final")):
            missing.append(str(row.get("address", "<unknown>")))
    return missing


def address_coverage(workbook_rows: int, source_segments: int, sheet: str) -> list[str]:
    """Reject when ``len(rows)`` and ``len(segments)`` disagree.

    A coverage gap means the workbook was edited destructively (rows
    deleted or duplicated) or the English source changed under the
    reviewer's feet. Either way, the round-trip is unsafe.
    """
    if workbook_rows != source_segments:
        return [
            f"{sheet}: row count {workbook_rows} != segment count "
            f"{source_segments} (rows deleted/added or source changed?)"
        ]
    return []


def canonical_tokens_preserved(
    english_text: str, localized_text: str, *, sheet: str
) -> list[str]:
    """Assert ID-shaped tokens from the English source survive in the output.

    Catches the "annotator paraphrased an ID" case. Snake-case identifiers
    are checked separately because translators legitimately translate
    common English words; we only flag *ID-shaped* tokens whose absence
    would break tool calls or DB lookups.
    """
    errors: list[str] = []
    for pattern in _ID_PATTERNS:
        for match in pattern.findall(english_text):
            if match not in localized_text:
                errors.append(
                    f"{sheet}: canonical ID {match!r} missing from localized output"
                )
    return errors


def manifest_drift(
    annotation_manifest: dict | None,
    *,
    current_git_commit: str | None,
) -> list[str]:
    """Warn when the annotation manifest's ``git_commit`` differs from HEAD.

    Drift means the English source has potentially changed since the
    workbook was exported, so address mappings may not line up.
    """
    if annotation_manifest is None:
        return ["annotation manifest missing — cannot verify HEAD drift"]
    source = annotation_manifest.get("source", {})
    recorded = source.get("git_commit") if isinstance(source, dict) else None
    if recorded is None:
        return ["annotation manifest has no git_commit recorded"]
    if current_git_commit is None:
        return ["cannot read current git_commit (not a checkout?)"]
    if recorded != current_git_commit:
        return [
            f"git_commit drift: workbook recorded {recorded[:12]}.., "
            f"HEAD is {current_git_commit[:12]}.."
        ]
    return []
