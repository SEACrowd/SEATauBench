#!/usr/bin/env python3
"""Analyze a db.json file and recommend which columns to pass to --flatten.

Usage:
    python utils/db_analyze_flatten.py data/tau2/domains/airline/db.json
    python utils/db_analyze_flatten.py data/tau2/domains/airline/db.json --detail
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


# ── thresholds ────────────────────────────────────────────────────────────────
# A dict column is "stable" when every row has the exact same key set.
STABILITY_THRESHOLD = 1.0   # 1.0 = 100% of rows must share the same key set

# Maximum number of generated columns we're willing to accept from one flatten.
# (= max_list_length × number_of_inner_keys)
MAX_EXPANDED_COLS = 20

# Fraction of rows that must have the maximum list length for us to call it
# "low sparsity". If fewer rows hit the max, extra columns will be blank for
# the rest, which is acceptable up to a point.
LOW_SPARSITY_THRESHOLD = 0.10   # top-length rows must be ≥ 10% of all rows


# ── helpers ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_rows(table_data: Any) -> list[dict[str, Any]]:
    """Return a flat list of row dicts regardless of table shape."""
    if isinstance(table_data, dict):
        rows = list(table_data.values())
        if rows and all(isinstance(r, dict) for r in rows):
            return rows
    elif isinstance(table_data, list):
        if table_data and all(isinstance(r, dict) for r in table_data):
            return table_data
    return []


def key_stability(values: list[dict]) -> tuple[float, list[frozenset]]:
    """Return (stability_ratio, list_of_key_sets).

    stability_ratio = fraction of rows that share the single most-common key set.
    """
    counts: Counter[frozenset] = Counter(frozenset(v.keys()) for v in values)
    most_common_count = counts.most_common(1)[0][1]
    stability = most_common_count / len(values)
    return stability, list(counts.keys())


def analyze_column(
    col: str,
    values: list[Any],
    detail: bool,
) -> dict[str, Any]:
    """Inspect one column across all rows and return analysis metadata."""
    non_null = [v for v in values if v is not None]
    total = len(values)

    if not non_null:
        return {"col": col, "kind": "empty", "verdict": "skip", "reason": "all null"}

    # --- determine dominant type ---
    type_counts: Counter[str] = Counter(type(v).__name__ for v in non_null)
    dominant_type, dominant_count = type_counts.most_common(1)[0]

    result: dict[str, Any] = {
        "col": col,
        "dominant_type": dominant_type,
        "type_counts": dict(type_counts),
        "total_rows": total,
        "non_null_rows": len(non_null),
    }

    # --- dict column ---
    if dominant_type == "dict":
        dicts = [v for v in non_null if isinstance(v, dict)]
        stability, key_sets = key_stability(dicts)
        all_keys = sorted({k for ks in key_sets for k in ks})
        result.update(
            kind="dict",
            stability=stability,
            all_keys=all_keys,
            num_unique_key_sets=len(key_sets),
        )
        # Check whether the dict values themselves are nested (would stay as JSON blobs)
        sample_values = [
            v for row_val in non_null if isinstance(row_val, dict)
            for v in row_val.values()
        ]
        values_are_nested = sample_values and any(
            isinstance(v, (dict, list)) for v in sample_values
        )

        if stability < STABILITY_THRESHOLD:
            result["verdict"] = "avoid"
            result["reason"] = (
                f"key set varies across rows (stability={stability:.0%}, "
                f"{len(key_sets)} unique key sets) → would produce sparse/unpredictable columns"
            )
        elif len(all_keys) > MAX_EXPANDED_COLS:
            result["verdict"] = "avoid"
            result["reason"] = (
                f"too many expanded columns ({len(all_keys)} > {MAX_EXPANDED_COLS})"
            )
        elif values_are_nested:
            result["verdict"] = "avoid"
            result["reason"] = (
                f"dict values are themselves nested objects → flattening only goes one level deep, "
                f"cell values would still be JSON blobs"
            )
        else:
            result["verdict"] = "flatten"
            result["reason"] = (
                f"100% stable key set {all_keys} → "
                f"expands to {len(all_keys)} columns with no sparsity"
            )
        return result

    # --- list-of-dicts column ---
    if dominant_type == "list":
        lists = [v for v in non_null if isinstance(v, list)]
        all_dicts = [item for lst in lists for item in lst]
        if not all_dicts or not all(isinstance(item, dict) for item in all_dicts):
            result.update(
                kind="list",
                verdict="skip",
                reason="list items are not dicts; cannot flatten",
            )
            return result

        length_counts: Counter[int] = Counter(len(lst) for lst in lists)
        max_len = max(length_counts)
        inner_keys = sorted({k for item in all_dicts for k in item.keys()})
        inner_stability, inner_key_sets = key_stability(
            [item for item in all_dicts if isinstance(item, dict)]
        )
        expanded_cols = max_len * len(inner_keys)
        top_length_fraction = length_counts[max_len] / total

        result.update(
            kind="list[dict]",
            max_items=max_len,
            length_distribution=dict(sorted(length_counts.items())),
            inner_keys=inner_keys,
            inner_key_stability=inner_stability,
            expanded_cols=expanded_cols,
            top_length_fraction=top_length_fraction,
        )

        problems = []
        if inner_stability < STABILITY_THRESHOLD:
            problems.append(
                f"inner keys vary (stability={inner_stability:.0%})"
            )
        if expanded_cols > MAX_EXPANDED_COLS:
            problems.append(
                f"too many expanded columns ({expanded_cols} > {MAX_EXPANDED_COLS})"
            )

        if problems:
            result["verdict"] = "avoid"
            result["reason"] = "; ".join(problems)
        else:
            pct_max = f"{top_length_fraction:.0%}"
            sparsity_note = (
                "low sparsity" if top_length_fraction >= LOW_SPARSITY_THRESHOLD
                else "high sparsity at max length"
            )
            result["verdict"] = "flatten"
            result["reason"] = (
                f"stable inner keys {inner_keys}, "
                f"max {max_len} items → {expanded_cols} cols, "
                f"{pct_max} of rows reach max length ({sparsity_note})"
            )

        return result

    # --- scalar or other ---
    result.update(kind="scalar", verdict="skip", reason="scalar value; nothing to flatten")
    return result


def print_analysis(
    table_name: str,
    analyses: list[dict[str, Any]],
    detail: bool,
) -> list[str]:
    """Print per-table results and return a list of recommended flatten specs."""
    recommendations: list[str] = []

    print(f"\n{'='*60}")
    print(f"TABLE: {table_name}")
    print(f"{'='*60}")

    for a in analyses:
        col = a["col"]
        verdict = a.get("verdict", "skip")
        kind = a.get("kind", "unknown")
        reason = a.get("reason", "")

        icon = {"flatten": "✓", "avoid": "✗", "skip": "·"}.get(verdict, "?")
        print(f"\n  {icon} {col}  [{kind}]")

        if detail:
            if kind == "dict":
                print(f"      keys       : {a.get('all_keys')}")
                print(f"      stability  : {a.get('stability', 0):.0%}")
            elif kind == "list[dict]":
                print(f"      inner_keys : {a.get('inner_keys')}")
                print(f"      dist       : {a.get('length_distribution')}")
                print(f"      expanded   : {a.get('expanded_cols')} cols")
            print(f"      verdict    : {verdict.upper()} — {reason}")
        else:
            print(f"      {verdict.upper()} — {reason}")

        if verdict == "flatten":
            recommendations.append(f"{table_name}.{col}")

    return recommendations


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a db.json and recommend --flatten arguments for db_json_to_excel.py"
    )
    parser.add_argument("input", help="Path to db.json")
    parser.add_argument(
        "--detail", action="store_true",
        help="Show full breakdown (key sets, distributions, column counts)",
    )
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"[ERROR] file not found: {path}", file=sys.stderr)
        return 1

    data = load_json(path)
    if not isinstance(data, dict):
        print("[ERROR] top-level JSON must be an object", file=sys.stderr)
        return 1

    all_specs: list[str] = []

    for table_name, table_data in data.items():
        rows = iter_rows(table_data)
        if not rows:
            print(f"\n{'='*60}")
            print(f"TABLE: {table_name}  [no row-dict structure — skipped]")
            continue

        # collect all columns present across rows
        all_cols: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for col in row:
                if col not in seen:
                    seen.add(col)
                    all_cols.append(col)

        analyses = []
        for col in all_cols:
            values = [row.get(col) for row in rows]
            analyses.append(analyze_column(col, values, args.detail))

        specs = print_analysis(table_name, analyses, args.detail)
        all_specs.extend(specs)

    # ── summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("RECOMMENDED --flatten ARGUMENTS")
    print(f"{'='*60}")
    if all_specs:
        flag_str = " \\\n  ".join(f"--flatten {s}" for s in all_specs)
        print(f"\n  python utils/db_json_to_excel.py \\\n"
              f"    -i {args.input} \\\n"
              f"  {flag_str}")
    else:
        print("  (no columns recommended for flattening)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
