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

The canonical vocabulary (``VALID_TAGS``) is kept in sync by hand with the LLM
judge prompt in ``src/tau2/evaluator/review_llm_judge.py``; there is no shared
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

# Canonical error-tag vocabulary (mirrors the "Error Tags" list in the LLM judge
# prompt at src/tau2/evaluator/review_llm_judge.py).
VALID_TAGS: frozenset[str] = frozenset(
    {
        "hallucination",
        "incorrect_interpretation",
        "guideline_violation",
        "revealed_info_early",
        "inconsistent_behavior",
        "tool_call_schema_error",
        "tool_call_argument_error",
        "irrelevant_tool_call",
        "premature_termination",
        "missed_required_action",
        "wrong_sequence",
        "interruption_error",
        "other",
    }
)

# Raw tag -> canonical tag (None = discard). Curated mapping of judge typos,
# synonyms, severity words, and non-English variants.
TAG_NORM: dict[str, str | None] = {
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

REVIEW_KEYS = ("review", "user_only_review")
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
    """Yield each error dict across full and user-only reviews."""
    for sim in reviewed.get("simulations", []):
        for key in REVIEW_KEYS:
            review = sim.get(key)
            if isinstance(review, dict):
                yield from review.get("errors") or []


def normalize_tags(tags: list[str]) -> list[str]:
    """Normalize raw tags to canonical tags, preserving order and de-duping."""
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        if tag in VALID_TAGS:
            canonical = tag
        elif tag in TAG_NORM:
            canonical = TAG_NORM[tag]
        else:
            print(f"    WARNING: unknown tag {tag!r} -> 'other'", file=sys.stderr)
            canonical = "other"
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        result.append(canonical)
    return result


def _target_label(tag: str) -> str:
    """Human-readable normalization target for a non-canonical tag."""
    target = TAG_NORM.get(tag, "other")
    return "discard" if target is None else target


def cmd_check(args: argparse.Namespace) -> int:
    files = resolve_reviewed_paths(args.paths)
    if not files:
        print("No results_reviewed.json files found.", file=sys.stderr)
        return 1

    counts: dict[str, int] = defaultdict(int)
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        for err in iter_review_errors(data):
            for tag in err.get("error_tags", []):
                counts[tag] += 1

    valid = {t: c for t, c in counts.items() if t in VALID_TAGS}
    invalid = {t: c for t, c in counts.items() if t not in VALID_TAGS}

    print(f"Scanned {len(files)} {REVIEWED_FILENAME} files\n")
    print("=" * 60)
    print(f"VALID tags ({len(valid)} unique, {sum(valid.values())} occurrences)")
    print("=" * 60)
    for tag, cnt in sorted(valid.items()):
        print(f"  {tag:<35} {cnt:>5}")

    print()
    print("=" * 60)
    print(
        f"INVALID tags - need normalization "
        f"({len(invalid)} unique, {sum(invalid.values())} occurrences)"
    )
    print("=" * 60)
    for tag, cnt in sorted(invalid.items()):
        print(f"  {tag:<35} {cnt:>5}  -> {_target_label(tag)}")
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
        for err in iter_review_errors(data):
            raw = err.get("error_tags", [])
            norm = normalize_tags(raw)
            if norm != raw:
                for t in raw:
                    if t not in VALID_TAGS:
                        changes[f"{t} -> {_target_label(t)}"] += 1
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
