#!/usr/bin/env python3
"""Verify that translated db.json files have the same structure as the original.

PASS — every table, row count, field key, nested dict key, list length, and value type matches the original across all languages.

Checks (order-insensitive for dict keys):
  1. [Table names] Same top-level table names
  2. [Row count] Same row count and row keys per table
  3. [Field keys] Same field keys per row
  4. [Nested keys] Same nested dict keys at any depth
  5. [List lengths] Same list lengths and same keys per list item (for list-of-dicts)
  6. [Value types] Compatible value types (translated string→string is OK; string→int is not)

  ┌──────────────┬────────────────────────────────────────────────────────────┐
  │    Check     │                           Detail                           │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Table names  │ Same set of top-level tables                               │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Row count    │ Same number of rows per table                              │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Row keys     │ Same IDs for dict-keyed tables                             │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Field keys   │ Same column names per row (order-insensitive)              │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Nested dict  │ Recursive key-set comparison at any depth                  │
  │ keys         │                                                            │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ List lengths │ Same number of items in every list                         │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ List item    │ Same fields per item in list-of-dicts                      │
  │ keys         │                                                            │
  ├──────────────┼────────────────────────────────────────────────────────────┤
  │ Value types  │ str→str, int→int, etc. (translated string values are fine, │
  │              │  type changes are not)                                     │
  └──────────────┴────────────────────────────────────────────────────────────┘

Usage:
    python utils/db_verify_structure.py \\
        --original data/tau2/domains/airline/db.json \\
        --translated data/tau2/domains/airline/v1/Chinese/db.json \\
                     data/tau2/domains/airline/v1/Indonesian/db.json \\
                     data/tau2/domains/airline/v1/Thai/db.json \\
                     data/tau2/domains/airline/v1/Vietnamese/db.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ── diff helpers ───────────────────────────────────────────────────────────────

def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def _compare_values(
    orig: Any,
    trans: Any,
    path: str,
    errors: list[str],
) -> None:
    """Recursively compare structure; ignore actual string values (translation)."""

    orig_type = _type_name(orig)
    trans_type = _type_name(trans)

    # Type must match (string→string OK, int stays int, etc.)
    if orig_type != trans_type:
        errors.append(
            f"{path}: type mismatch — expected {orig_type}, got {trans_type}"
        )
        return

    if isinstance(orig, dict):
        orig_keys = set(orig.keys())
        trans_keys = set(trans.keys())
        missing = orig_keys - trans_keys
        extra = trans_keys - orig_keys
        if missing:
            errors.append(f"{path}: missing keys {sorted(missing)}")
        if extra:
            errors.append(f"{path}: unexpected extra keys {sorted(extra)}")
        for key in orig_keys & trans_keys:
            _compare_values(orig[key], trans[key], f"{path}.{key}", errors)
        return

    if isinstance(orig, list):
        if len(orig) != len(trans):
            errors.append(
                f"{path}: list length mismatch — expected {len(orig)}, got {len(trans)}"
            )
            # still compare overlapping items
        for idx, (o_item, t_item) in enumerate(zip(orig, trans)):
            _compare_values(o_item, t_item, f"{path}[{idx}]", errors)
        return

    # scalar — only check type (already done above); value may differ (translation)


# ── table-level comparison ─────────────────────────────────────────────────────

def _compare_table(
    table_name: str,
    orig_table: Any,
    trans_table: Any,
    max_row_errors: int,
) -> list[str]:
    errors: list[str] = []
    path = f"[{table_name}]"

    orig_type = _type_name(orig_table)
    trans_type = _type_name(trans_table)
    if orig_type != trans_type:
        errors.append(f"{path}: table type mismatch — expected {orig_type}, got {trans_type}")
        return errors

    if isinstance(orig_table, dict):
        orig_keys = set(orig_table.keys())
        trans_keys = set(trans_table.keys())
        missing_rows = orig_keys - trans_keys
        extra_rows = trans_keys - orig_keys

        if len(orig_keys) != len(trans_keys):
            errors.append(
                f"{path}: row count mismatch — expected {len(orig_keys)}, got {len(trans_keys)}"
            )
        if missing_rows:
            sample = sorted(missing_rows)[:5]
            errors.append(
                f"{path}: {len(missing_rows)} missing row key(s), e.g. {sample}"
            )
        if extra_rows:
            sample = sorted(extra_rows)[:5]
            errors.append(
                f"{path}: {len(extra_rows)} unexpected extra row key(s), e.g. {sample}"
            )

        row_error_count = 0
        for row_key in sorted(orig_keys & trans_keys):
            row_errors: list[str] = []
            _compare_values(
                orig_table[row_key],
                trans_table[row_key],
                f"{path}[{row_key!r}]",
                row_errors,
            )
            if row_errors:
                errors.extend(row_errors)
                row_error_count += 1
                if row_error_count >= max_row_errors:
                    remaining = len(orig_keys & trans_keys) - row_error_count
                    errors.append(
                        f"{path}: stopped after {max_row_errors} row error(s) "
                        f"({remaining} row(s) not checked)"
                    )
                    break
        return errors

    if isinstance(orig_table, list):
        if len(orig_table) != len(trans_table):
            errors.append(
                f"{path}: row count mismatch — expected {len(orig_table)}, got {len(trans_table)}"
            )
        row_error_count = 0
        for idx, (o_row, t_row) in enumerate(zip(orig_table, trans_table)):
            row_errors = []
            _compare_values(o_row, t_row, f"{path}[{idx}]", row_errors)
            if row_errors:
                errors.extend(row_errors)
                row_error_count += 1
                if row_error_count >= max_row_errors:
                    remaining = min(len(orig_table), len(trans_table)) - row_error_count
                    errors.append(
                        f"{path}: stopped after {max_row_errors} row error(s) "
                        f"({remaining} row(s) not checked)"
                    )
                    break
        return errors

    # scalar table — just type-check (done above)
    return errors


# ── file-level comparison ──────────────────────────────────────────────────────

def verify(
    original: dict[str, Any],
    translated: dict[str, Any],
    translated_label: str,
    max_row_errors: int,
    verbose: bool,
) -> list[str]:
    all_errors: list[str] = []

    orig_tables = set(original.keys())
    trans_tables = set(translated.keys())
    missing_tables = orig_tables - trans_tables
    extra_tables = trans_tables - orig_tables

    if missing_tables:
        all_errors.append(f"missing tables: {sorted(missing_tables)}")
    if extra_tables:
        all_errors.append(f"unexpected extra tables: {sorted(extra_tables)}")

    for table_name in sorted(orig_tables & trans_tables):
        table_errors = _compare_table(
            table_name,
            original[table_name],
            translated[table_name],
            max_row_errors=max_row_errors,
        )
        if table_errors:
            all_errors.extend(table_errors)
        elif verbose:
            orig_len = len(original[table_name])
            print(f"  [OK] {table_name} ({orig_len} rows)")

    return all_errors


# ── main ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify translated db.json files have the same structure as the original"
    )
    parser.add_argument(
        "--original",
        required=True,
        help="Path to the original (reference) db.json",
    )
    parser.add_argument(
        "--translated",
        nargs="+",
        required=True,
        metavar="PATH",
        help="Path(s) to translated db.json file(s) to verify",
    )
    parser.add_argument(
        "--max-row-errors",
        type=int,
        default=10,
        metavar="N",
        help="Stop checking rows in a table after N row-level errors (default: 10)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print OK tables as well as errors",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    orig_path = Path(args.original)

    if not orig_path.exists():
        print(f"[ERROR] original not found: {orig_path}", file=sys.stderr)
        return 1

    original = json.loads(orig_path.read_text(encoding="utf-8"))
    if not isinstance(original, dict):
        print("[ERROR] original is not a JSON object", file=sys.stderr)
        return 1

    overall_ok = True

    for trans_path_str in args.translated:
        trans_path = Path(trans_path_str)
        label = trans_path.parent.name  # e.g. "Chinese"

        print(f"\n{'='*60}")
        print(f"Verifying: {trans_path}  [{label}]")
        print(f"{'='*60}")

        if not trans_path.exists():
            print(f"  [ERROR] file not found: {trans_path}")
            overall_ok = False
            continue

        try:
            translated = json.loads(trans_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"  [ERROR] invalid JSON: {exc}")
            overall_ok = False
            continue

        if not isinstance(translated, dict):
            print("  [ERROR] translated file is not a JSON object")
            overall_ok = False
            continue

        errors = verify(
            original=original,
            translated=translated,
            translated_label=label,
            max_row_errors=args.max_row_errors,
            verbose=args.verbose,
        )

        if errors:
            overall_ok = False
            print(f"  [FAIL] {len(errors)} structural issue(s) found:")
            for err in errors:
                print(f"    - {err}")
        else:
            print(f"  [PASS] structure matches original ({orig_path.name})")

    print()
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
