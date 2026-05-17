#!/usr/bin/env python3
"""Analyze a db.json and recommend --merge and --keep arguments for
db_excel_merge_translations.py.

Operates directly on the db.json — no Excel file needed.

By default it auto-detects which columns to flatten (same logic as
db_analyze_flatten.py) and then classifies every sub-field as translatable
or non-translatable to produce --merge / --keep specs.

You can also supply explicit --flatten specs to skip auto-detection:

Usage:
    # auto-detect flatten, then recommend merge/keep
    python utils/db_analyze_merge.py data/tau2/domains/airline/db.json

    # supply flatten specs explicitly
    python utils/db_analyze_merge.py data/tau2/domains/airline/db.json \\
        --flatten users.name --flatten users.address ...

    # verbose field-level breakdown
    python utils/db_analyze_merge.py data/tau2/domains/airline/db.json --detail
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ── flatten auto-detection thresholds (mirrors db_analyze_flatten.py) ─────────
_STABILITY_THRESHOLD = 1.0
_MAX_EXPANDED_COLS = 20
_LOW_SPARSITY_THRESHOLD = 0.10

# ── translatability heuristics ─────────────────────────────────────────────────

# Field names that are always non-translatable regardless of values.
_NON_TRANSLATABLE_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "id",
        "dob",
        "zip",
        "date",
        "amount",
        "price",
        "number",
        "code",
        "origin",
        "destination",
    }
)

# Field name suffixes/prefixes that indicate non-translatable content.
_NON_TRANSLATABLE_SUFFIXES: tuple[str, ...] = (
    "_id",
    "_at",
    "_number",
    "_code",
    "_date",
    "_time",
)
_NON_TRANSLATABLE_PREFIXES: tuple[str, ...] = ("id_",)

# Regex patterns matched against string values.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")
_UPPERCASE_CODE_RE = re.compile(r"^[A-Z0-9]{2,6}$")  # airport/country/flight codes


# ── helpers ────────────────────────────────────────────────────────────────────


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _iter_rows(table_data: Any) -> list[dict[str, Any]]:
    if isinstance(table_data, dict):
        rows = list(table_data.values())
        if rows and all(isinstance(r, dict) for r in rows):
            return rows
    elif isinstance(table_data, list):
        if table_data and all(isinstance(r, dict) for r in table_data):
            return table_data
    return []


def _key_stability(dicts: list[dict]) -> float:
    counts: Counter[frozenset] = Counter(frozenset(d.keys()) for d in dicts)
    return counts.most_common(1)[0][1] / len(dicts)


# ── flatten auto-detection ─────────────────────────────────────────────────────


def _is_flatten_candidate(col: str, values: list[Any]) -> bool:
    """Return True if this column passes the flatten quality bar."""
    non_null = [v for v in values if v is not None]
    if not non_null:
        return False

    type_counts: Counter[str] = Counter(type(v).__name__ for v in non_null)
    dominant_type = type_counts.most_common(1)[0][0]

    if dominant_type == "dict":
        dicts = [v for v in non_null if isinstance(v, dict)]
        if _key_stability(dicts) < _STABILITY_THRESHOLD:
            return False
        all_keys = {k for d in dicts for k in d}
        if len(all_keys) > _MAX_EXPANDED_COLS:
            return False
        # Reject if the dict values are themselves nested (JSON blobs after flatten)
        sample_vals = [v for d in dicts for v in d.values()]
        if any(isinstance(v, (dict, list)) for v in sample_vals):
            return False
        return True

    if dominant_type == "list":
        lists = [v for v in non_null if isinstance(v, list)]
        all_items = [item for lst in lists for item in lst]
        if not all_items or not all(isinstance(i, dict) for i in all_items):
            return False
        inner_keys = {k for item in all_items for k in item}
        if _key_stability(all_items) < _STABILITY_THRESHOLD:  # type: ignore[arg-type]
            return False
        max_len = max(len(lst) for lst in lists)
        if max_len * len(inner_keys) > _MAX_EXPANDED_COLS:
            return False
        return True

    return False


def _auto_flatten_specs(data: dict[str, Any]) -> list[str]:
    """Return flatten specs using the same logic as db_analyze_flatten.py."""
    specs: list[str] = []
    for table_name, table_data in data.items():
        rows = _iter_rows(table_data)
        if not rows:
            continue
        seen: set[str] = set()
        cols: list[str] = []
        for row in rows:
            for col in row:
                if col not in seen:
                    seen.add(col)
                    cols.append(col)
        for col in cols:
            values = [row.get(col) for row in rows]
            if _is_flatten_candidate(col, values):
                specs.append(f"{table_name}.{col}")
    return specs


# ── sub-field value collection ─────────────────────────────────────────────────


def _collect_subfield_values(
    rows: list[dict[str, Any]], col: str
) -> dict[str, list[Any]]:
    """Gather per-sub-field sample values from a nested column."""
    result: dict[str, list[Any]] = {}
    for row in rows:
        value = row.get(col)
        if isinstance(value, dict):
            for k, v in value.items():
                result.setdefault(k, []).append(v)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        result.setdefault(k, []).append(v)
    return result


# ── translatability classifier ─────────────────────────────────────────────────


def _is_translatable(field: str, values: list[Any]) -> tuple[bool, str]:
    """Return (translatable, reason)."""
    field_lower = field.lower()

    # --- field-name heuristics ---
    if field_lower in _NON_TRANSLATABLE_FIELD_NAMES:
        return False, f"'{field}' is a known non-translatable identifier"
    for suffix in _NON_TRANSLATABLE_SUFFIXES:
        if field_lower.endswith(suffix):
            return False, f"field name ends with '{suffix}'"
    for prefix in _NON_TRANSLATABLE_PREFIXES:
        if field_lower.startswith(prefix):
            return False, f"field name starts with '{prefix}'"

    # --- value-based heuristics ---
    non_null = [v for v in values if v is not None]
    if not non_null:
        return False, "no non-null values to inspect"

    if all(isinstance(v, (int, float)) for v in non_null):
        return False, "all values are numeric"

    str_vals = [v for v in non_null if isinstance(v, str)]
    if not str_vals:
        return True, "non-string complex values"

    if all(_DATE_RE.match(v) for v in str_vals):
        return False, "all values match date/datetime pattern"

    if all(_TIME_RE.match(v) for v in str_vals):
        return False, "all values match time pattern"

    if all(_UPPERCASE_CODE_RE.match(v) for v in str_vals):
        return (
            False,
            "all values are short uppercase codes (airport, country, flight, …)",
        )

    return True, "values appear to be free text"


# ── per-column analysis ────────────────────────────────────────────────────────


def _analyze_merge_column(
    table_name: str,
    col: str,
    rows: list[dict[str, Any]],
    detail: bool,
) -> tuple[bool, list[str]]:
    """
    Analyze one flatten-recommended column.

    Returns:
        (should_merge, keep_specs)
        keep_specs: list of 'table.col.field' strings for non-translatable sub-fields
    """
    subfield_values = _collect_subfield_values(rows, col)
    if not subfield_values:
        return False, []

    translatable_fields: list[str] = []
    non_translatable_fields: list[tuple[str, str]] = []  # (field, reason)

    for field, vals in subfield_values.items():
        ok, reason = _is_translatable(field, vals)
        if ok:
            translatable_fields.append(field)
        else:
            non_translatable_fields.append((field, reason))

    should_merge = bool(translatable_fields)
    keep_specs = (
        [f"{table_name}.{col}.{f}" for f, _ in non_translatable_fields]
        if should_merge
        else []
    )

    if detail:
        for f in translatable_fields:
            print(f"        [translate] {col}.{f}")
        for f, reason in non_translatable_fields:
            keep_tag = " → --keep" if should_merge else ""
            print(f"        [keep     ] {col}.{f}  ({reason}){keep_tag}")

    return should_merge, keep_specs


# ── main ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a db.json and recommend --merge / --keep arguments "
            "for db_excel_merge_translations.py"
        )
    )
    parser.add_argument("input", help="Path to db.json")
    parser.add_argument(
        "--flatten",
        action="append",
        default=[],
        metavar="TABLE.COLUMN",
        help=(
            "Explicit flatten spec (table.column). "
            "If omitted, specs are auto-detected using db_analyze_flatten logic. "
            "Repeatable."
        ),
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show field-level translatable/keep breakdown per column",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.input)

    if not path.exists():
        print(f"[ERROR] file not found: {path}", file=sys.stderr)
        return 1

    data = _load_json(path)
    if not isinstance(data, dict):
        print("[ERROR] top-level JSON must be an object", file=sys.stderr)
        return 1

    # --- resolve flatten specs ---
    if args.flatten:
        flatten_specs = args.flatten
        print(f"[INFO] using {len(flatten_specs)} explicit --flatten spec(s)")
    else:
        flatten_specs = _auto_flatten_specs(data)
        print(
            f"[INFO] auto-detected {len(flatten_specs)} flatten spec(s): {flatten_specs}"
        )

    # --- group specs by table ---
    table_cols: dict[str, list[str]] = {}
    for spec in flatten_specs:
        if spec.count(".") != 1:
            print(
                f"[ERROR] invalid flatten spec '{spec}' (expected table.column)",
                file=sys.stderr,
            )
            return 1
        table, col = spec.split(".", 1)
        table_cols.setdefault(table, []).append(col)

    # --- analyse each table ---
    all_merge_specs: list[str] = []
    all_keep_specs: list[str] = []
    all_skip_specs: list[str] = []

    for table_name, cols in table_cols.items():
        table_data = data.get(table_name)
        if table_data is None:
            print(
                f"[WARN] table '{table_name}' not found in JSON; skipped",
                file=sys.stderr,
            )
            continue

        rows = _iter_rows(table_data)
        if not rows:
            print(
                f"[WARN] table '{table_name}' has no row-dict structure; skipped",
                file=sys.stderr,
            )
            continue

        print(f"\n{'=' * 60}")
        print(f"TABLE: {table_name}")
        print(f"{'=' * 60}")

        for col in cols:
            subfield_values = _collect_subfield_values(rows, col)
            if not subfield_values:
                print(f"\n  · {col}  — no sub-fields found; skipped")
                continue

            print(f"\n  {col}  (sub-fields: {sorted(subfield_values)})")

            should_merge, keep_specs = _analyze_merge_column(
                table_name, col, rows, args.detail
            )

            if should_merge:
                all_merge_specs.append(f"{table_name}.{col}")
                all_keep_specs.extend(keep_specs)
                keep_fields = [s.split(".", 2)[2] for s in keep_specs]
                print(f"    → MERGE  (keep non-translatable: {keep_fields or 'none'})")
            else:
                all_skip_specs.append(f"{table_name}.{col}")
                print(f"    → SKIP   (no translatable sub-fields)")

    # --- summary ---
    print(f"\n{'=' * 60}")
    print("MERGE / KEEP ANALYSIS SUMMARY")
    print(f"{'=' * 60}")

    if all_merge_specs:
        print(f"\n  Columns to --merge : {all_merge_specs}")
    if all_keep_specs:
        print(f"  Sub-fields to --keep: {all_keep_specs}")
    if all_skip_specs:
        print(f"  Skipped (no text)  : {all_skip_specs}")

    # --- output command ---
    print(f"\n{'=' * 60}")
    print("RECOMMENDED db_excel_merge_translations.py COMMAND")
    print(f"{'=' * 60}")

    if not all_merge_specs:
        print("\n  (no columns require merging)")
        return 0

    stem = path.stem
    xlsx = path.with_suffix(".xlsx")
    merged = path.parent / f"{stem}_merged.xlsx"
    translated_root = path.parent / "translated"

    lines = [
        "  python utils/db_excel_merge_translations.py \\",
        f"    -i {xlsx} \\",
        f"    --translated-root {translated_root} \\",
        f"    -o {merged} \\",
    ]
    for spec in all_merge_specs:
        lines.append(f"    --merge {spec} \\")
    for spec in all_keep_specs:
        lines.append(f"    --keep  {spec} \\")
    # strip trailing backslash on last line
    lines[-1] = lines[-1].rstrip(" \\")

    print()
    print("\n".join(lines))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
