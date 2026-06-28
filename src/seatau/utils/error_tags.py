"""Audit and normalize LLM-judge error tags in ``results_reviewed.json`` files.

The LLM-judge review pipeline writes ``results_reviewed.json`` files whose
``simulations[].review`` and ``simulations[].user_only_review`` entries carry
``errors[].error_tags``. Judges occasionally emit tags outside the canonical
vocabulary (typos, synonyms, severity words); this module audits and repairs
them.

Subcommands:
  check      Report every unique error tag found, flagging non-canonical ones
             (those that need normalization). Read-only.
  normalize  Rewrite raw/typo'd tags to the canonical vocabulary, in place.
             Use --dry-run to preview without writing.

The canonical vocabulary is kept in sync by hand with the LLM judge prompts in
``src/tau2/evaluator/review_llm_judge.py`` and
``src/tau2/evaluator/review_llm_judge_user_only.py``; there is no shared
constant upstream yet.

Usage:
  uv run python -m seatau.utils.error_tags check     data/simulations
  uv run python -m seatau.utils.error_tags normalize data/simulations --dry-run
  uv run python -m seatau.utils.error_tags normalize run_a/ run_b/results_reviewed.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Literal

ErrorSource = Literal["agent", "user"]

# Canonical tag vocabularies. User errors have a narrower vocabulary than agent
# errors because user-only prompts cannot produce tool-call mistakes.
USER_VALID_TAGS: frozenset[str] = frozenset(
    {
        "hallucination",
        "incorrect_interpretation",
        "guideline_violation",
        "revealed_info_early",
        "inconsistent_behavior",
        "premature_termination",
        "missed_required_action",
        "wrong_sequence",
        "interruption_error",
        "other",
    }
)

AGENT_VALID_TAGS: frozenset[str] = USER_VALID_TAGS | frozenset(
    {
        "tool_call_schema_error",
        "tool_call_argument_error",
        "irrelevant_tool_call",
    }
)

VALID_TAGS: frozenset[str] = AGENT_VALID_TAGS | USER_VALID_TAGS


def _normalize_raw_tag(tag: object) -> str:
    """Normalize judge tag spelling before canonical lookup."""
    return str(tag).strip().lower().replace("-", "_").replace(" ", "_")


# Raw tag -> canonical tag (None = discard). Curated mapping of judge typos,
# synonyms, severity words, and non-English variants.
_RAW_TAG_NORM: dict[str, str | None] = {
    # Discard - severity levels or no-error markers used as tags
    "correct": None,
    "no_error": None,
    "minor": None,
    "critical": None,
    "critical_hindered": None,
    "appropriate_transfer": None,
    # Typos of predefined tags
    "guideleine_violation": "guideline_violation",
    "inconsistant_behavior": "inconsistent_behavior",
    "inconsistence_behavior": "inconsistent_behavior",
    "misssed_required_action": "missed_required_action",
    "wong_sequence": "wrong_sequence",
    # Variants -> guideline_violation
    "instruction_violation": "guideline_violation",
    "policy_violation": "guideline_violation",
    "violates_policy": "guideline_violation",
    "premature_transfer": "guideline_violation",
    "inappropriate_action": "guideline_violation",
    "transfer_to_human_agents": "guideline_violation",
    "multiple_tool_calls_simultaneously": "guideline_violation",
    "vi phạm nguyên tắc": "guideline_violation",
    # Variants -> incorrect_interpretation
    "misinterpretation": "incorrect_interpretation",
    "misinterpreted": "incorrect_interpretation",
    "misread": "incorrect_interpretation",
    "misread instructions": "incorrect_interpretation",
    "misread_guideline": "incorrect_interpretation",
    "misread_information": "incorrect_interpretation",
    "misunderstood": "incorrect_interpretation",
    "misunderstood_task": "incorrect_interpretation",
    "misunderstood_user_info": "incorrect_interpretation",
    # Variants -> missed_required_action
    "missing_required_action": "missed_required_action",
    "incomplete_check": "missed_required_action",
    "incomplete_information": "missed_required_action",
    "information_missing": "missed_required_action",
    "insufficient_information": "missed_required_action",
    "missing_required_information": "missed_required_action",
    "missing_check_for_messaging_app_permissions": "missed_required_action",
    # Variants -> hallucination
    "incorrect_information": "hallucination",
    "misinformation": "hallucination",
    "misleading": "hallucination",
    # Variants -> tool_call_argument_error
    "incorrect_calculation": "tool_call_argument_error",
    "mis-calculated_total": "tool_call_argument_error",
    # Variants -> irrelevant_tool_call
    "unnecessary_tool_call": "irrelevant_tool_call",
    "redundant_tool_call": "irrelevant_tool_call",
    "took_unnecessary_action": "irrelevant_tool_call",
    "unnecessary_action": "irrelevant_tool_call",
    "incorrect_tool_usage": "irrelevant_tool_call",
    # Variants -> wrong_sequence
    "premature_action": "wrong_sequence",
    # Variants -> inconsistent_behavior
    "hành vi không nhất quán": "inconsistent_behavior",
    # Variants -> other
    "incorrect_behavior": "other",
    "ineffective_guidance": "other",
    "inefficiency": "other",
    "inefficient": "other",
    "inefficient_action": "other",
    "inefficient_guidance": "other",
    "inefficient_process": "other",
    "inefficient_repetition": "other",
    "information_overload": "other",
    "redundant_response": "other",
    "repeated_error": "other",
    "repeated_information": "other",
    "repeated_requests": "other",
}

TAG_NORM: dict[str, str | None] = {
    _normalize_raw_tag(tag): canonical for tag, canonical in _RAW_TAG_NORM.items()
}

REVIEWED_FILENAME = "results_reviewed.json"


def resolve_reviewed_paths(paths: list[Path]) -> list[Path]:
    """Resolve files / run dirs / parent dirs to ``results_reviewed.json`` paths.

    Mirrors ``seatau.results.resolve_result_paths`` but targets the reviewed
    output file instead of ``results.json``.
    """
    resolved: list[Path] = []
    for path in paths:
        if path.is_file():
            resolved.append(path)
        elif path.is_dir():
            direct = path / REVIEWED_FILENAME
            if direct.exists():
                resolved.append(direct)
            else:
                resolved.extend(sorted(path.rglob(REVIEWED_FILENAME)))
    return resolved


def iter_review_errors(reviewed: dict):
    """Yield each error dict with its review source."""
    for sim in reviewed.get("simulations", []):
        review = sim.get("review")
        if isinstance(review, dict):
            for error in review.get("errors") or []:
                source = error.get("source")
                if source in ("agent", "user"):
                    yield source, error
                else:
                    yield "agent", error

        user_only_review = sim.get("user_only_review")
        if isinstance(user_only_review, dict):
            for error in user_only_review.get("errors") or []:
                yield "user", error


def _valid_tags_for_source(source: ErrorSource) -> frozenset[str]:
    """Return the canonical tag vocabulary for the review source."""
    return USER_VALID_TAGS if source == "user" else AGENT_VALID_TAGS


def _resolve_tag(
    tag: object,
    source: ErrorSource,
    *,
    warn: bool = True,
) -> str | None:
    """Resolve one raw tag to its canonical tag for a review source."""
    normalized = _normalize_raw_tag(tag)
    valid_tags = _valid_tags_for_source(source)
    if normalized in valid_tags:
        return normalized
    if normalized in TAG_NORM:
        canonical = TAG_NORM[normalized]
        if canonical in valid_tags or canonical is None:
            return canonical
    if warn:
        print(
            f"    WARNING: unknown or invalid {source} tag {tag!r} -> 'other'",
            file=sys.stderr,
        )
    return "other"


def normalize_tags(tags: list[str], source: ErrorSource = "agent") -> list[str]:
    """Normalize raw tags to canonical tags, preserving order and de-duping."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        canonical = _resolve_tag(tag, source)
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        result.append(canonical)
    return result


def _target_label(tag: object, source: ErrorSource) -> str:
    """Human-readable normalization target for a non-canonical tag."""
    target = _resolve_tag(tag, source, warn=False)
    return "discard" if target is None else target


def cmd_check(args: argparse.Namespace) -> int:
    files = resolve_reviewed_paths(args.paths)
    if not files:
        print("No results_reviewed.json files found.", file=sys.stderr)
        return 1

    counts: dict[tuple[ErrorSource, str], int] = defaultdict(int)
    invalid_counts: dict[tuple[ErrorSource, str], int] = defaultdict(int)
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        for source, err in iter_review_errors(data):
            for tag in err.get("error_tags", []):
                raw_tag = str(tag)
                counts[(source, raw_tag)] += 1
                normalized = _normalize_raw_tag(raw_tag)
                canonical = _resolve_tag(raw_tag, source, warn=False)
                valid_tags = _valid_tags_for_source(source)
                if (
                    normalized not in valid_tags
                    or canonical != normalized
                    or raw_tag != normalized
                ):
                    invalid_counts[(source, raw_tag)] += 1

    valid = {
        (source, tag): count
        for (source, tag), count in counts.items()
        if (source, tag) not in invalid_counts
    }

    print(f"Scanned {len(files)} {REVIEWED_FILENAME} files\n")
    print("=" * 60)
    print(f"VALID tags ({len(valid)} unique, {sum(valid.values())} occurrences)")
    print("=" * 60)
    for (source, tag), cnt in sorted(valid.items()):
        print(f"  {source:<5} {tag:<35} {cnt:>5}")

    print()
    print("=" * 60)
    print(
        f"INVALID tags - need normalization "
        f"({len(invalid_counts)} unique, {sum(invalid_counts.values())} occurrences)"
    )
    print("=" * 60)
    for (source, tag), cnt in sorted(invalid_counts.items()):
        print(f"  {source:<5} {tag:<35} {cnt:>5}  -> {_target_label(tag, source)}")
    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    files = resolve_reviewed_paths(args.paths)
    if not files:
        print("No results_reviewed.json files found.", file=sys.stderr)
        return 1

    updated = 0
    unchanged = 0
    changes: dict[str, int] = defaultdict(int)

    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for source, err in iter_review_errors(data):
            raw = err.get("error_tags", [])
            norm = normalize_tags(raw, source)
            if norm != raw:
                for t in raw:
                    if _resolve_tag(t, source, warn=False) != t:
                        changes[f"{source}: {t} -> {_target_label(t, source)}"] += 1
                err["error_tags"] = norm
                changed = True

        if changed:
            if not args.dry_run:
                f.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            updated += 1
            print(f"  {'would update' if args.dry_run else 'updated'}: {f}")
        else:
            unchanged += 1

    verb = "would be updated" if args.dry_run else "updated"
    print(f"\nDone. {updated} files {verb}, {unchanged} already clean.")
    if changes:
        print(f"\nTag changes{' (dry run)' if args.dry_run else ''}:")
        for mapping, cnt in sorted(changes.items(), key=lambda kv: -kv[1]):
            print(f"  {mapping:<60} x{cnt}")
    return 0


def _add_paths_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("data/simulations")],
        help=(
            "results_reviewed.json files, run directories, or parent directories "
            "to scan (default: data/simulations)."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Audit error tags (read-only).")
    _add_paths_arg(p_check)
    p_check.set_defaults(func=cmd_check)

    p_norm = sub.add_parser(
        "normalize", help="Rewrite tags to the canonical vocabulary."
    )
    _add_paths_arg(p_norm)
    p_norm.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing."
    )
    p_norm.set_defaults(func=cmd_normalize)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
