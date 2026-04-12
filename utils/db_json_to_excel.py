#!/usr/bin/env python3
"""Convert database-style JSON files into Excel workbooks with multiple sheets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd

INVALID_SHEET_CHARS = re.compile(r"[\[\]:*?/\\]")
MAX_SHEET_NAME_LEN = 31


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert JSON files with multiple top-level tables into .xlsx files"
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        help="Input JSON file path(s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output .xlsx file path (only valid with a single input)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store generated .xlsx files",
    )
    parser.add_argument(
        "--key-column",
        default="_row_key",
        help="Column name used to preserve row keys from dict-based tables",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Indent level for nested JSON values stored in cells",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
    )
    parser.add_argument(
        "--flatten",
        action="append",
        default=[],
        help=(
            "Flatten selected dict columns using table.column format "
            "(repeatable, e.g. --flatten users.address)"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print detailed conversion logs",
    )

    args = parser.parse_args()

    if args.output and len(args.input) != 1:
        parser.error("--output can only be used with a single --input file")

    return args


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("top-level JSON must be an object mapping table names to tables")

    return payload


def serialize_nested(value: Any, indent: int | None) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=indent)
    return value


def parse_flatten_specs(specs: list[str]) -> dict[str, set[str]]:
    flatten_map: dict[str, set[str]] = {}
    for spec in specs:
        if spec.count(".") != 1:
            raise ValueError(
                f"invalid --flatten selector '{spec}'. Expected format: table.column"
            )
        table_name, column_name = spec.split(".", 1)
        if not table_name or not column_name:
            raise ValueError(
                f"invalid --flatten selector '{spec}'. Expected format: table.column"
            )
        flatten_map.setdefault(table_name, set()).add(column_name)

    return flatten_map


def flatten_dict_columns_in_row(
    row: dict[str, Any],
    columns_to_flatten: set[str],
    indent: int | None,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    flattened_row = dict(row)

    for column in columns_to_flatten:
        if column not in flattened_row:
            continue

        value = flattened_row[column]
        if isinstance(value, dict):
            flattened_row.pop(column)
            for nested_key, nested_value in value.items():
                flattened_row[f"{column}.{nested_key}"] = serialize_nested(
                    nested_value, indent
                )
            continue

        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            flattened_row.pop(column)
            ordered_keys: list[str] = []
            seen_keys: set[str] = set()
            for item in value:
                for key in item:
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    ordered_keys.append(key)

            for index, item in enumerate(value, start=1):
                for key in ordered_keys:
                    if key not in item:
                        continue
                    flattened_row[f"{column}.{key}-{index}"] = serialize_nested(
                        item[key], indent
                    )
            continue

        warnings.append(f"column={column} type={type(value).__name__}")

    return flattened_row, warnings


def normalize_table(
    table_name: str,
    table_data: Any,
    key_column: str,
    indent: int | None,
    flatten_columns: set[str],
) -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    warned_non_dict_columns: set[str] = set()
    seen_columns: set[str] = set()

    if isinstance(table_data, dict):
        items = list(table_data.items())
        if items and all(isinstance(v, dict) for _, v in items):
            for row_key, row_value in items:
                seen_columns.update(row_value.keys())
                merged = {key_column: row_key, **row_value}
                flattened_row, row_warnings = flatten_dict_columns_in_row(
                    merged, flatten_columns, indent
                )
                for warning in row_warnings:
                    column = warning.split()[0].split("=", 1)[1]
                    if column in warned_non_dict_columns:
                        continue
                    warned_non_dict_columns.add(column)
                    warnings.append(
                        f"table={table_name} {warning}; left as JSON"
                    )
                rows.append(
                    {
                        col: serialize_nested(value, indent)
                        for col, value in flattened_row.items()
                    }
                )

            for missing_column in sorted(flatten_columns - seen_columns):
                warnings.append(
                    f"table={table_name} column={missing_column} not found; ignored"
                )

            return pd.DataFrame(rows), warnings

        for row_key, row_value in items:
            rows.append(
                {
                    key_column: row_key,
                    "value": serialize_nested(row_value, indent),
                }
            )
        if flatten_columns:
            for column in sorted(flatten_columns):
                warnings.append(
                    f"table={table_name} column={column} ignored; table rows are not objects"
                )
        return pd.DataFrame(rows), warnings

    if isinstance(table_data, list):
        if table_data and all(isinstance(item, dict) for item in table_data):
            for item in table_data:
                seen_columns.update(item.keys())
                flattened_row, row_warnings = flatten_dict_columns_in_row(
                    item, flatten_columns, indent
                )
                for warning in row_warnings:
                    column = warning.split()[0].split("=", 1)[1]
                    if column in warned_non_dict_columns:
                        continue
                    warned_non_dict_columns.add(column)
                    warnings.append(
                        f"table={table_name} {warning}; left as JSON"
                    )
                rows.append(
                    {
                        col: serialize_nested(value, indent)
                        for col, value in flattened_row.items()
                    }
                )
            for missing_column in sorted(flatten_columns - seen_columns):
                warnings.append(
                    f"table={table_name} column={missing_column} not found; ignored"
                )
            return pd.DataFrame(rows), warnings

        if flatten_columns:
            for column in sorted(flatten_columns):
                warnings.append(
                    f"table={table_name} column={column} ignored; table rows are not objects"
                )
        return pd.DataFrame(
            [{"value": serialize_nested(item, indent)} for item in table_data]
        ), warnings

    if flatten_columns:
        for column in sorted(flatten_columns):
            warnings.append(
                f"table={table_name} column={column} ignored; table is scalar"
            )

    return pd.DataFrame([{"value": serialize_nested(table_data, indent)}]), warnings


def sanitize_sheet_name(name: str, used_names: set[str]) -> str:
    cleaned = INVALID_SHEET_CHARS.sub("", str(name)).strip() or "Sheet"
    base = cleaned[:MAX_SHEET_NAME_LEN]
    candidate = base
    counter = 2

    while candidate in used_names:
        suffix = f"_{counter}"
        allowed = MAX_SHEET_NAME_LEN - len(suffix)
        candidate = f"{base[:allowed]}{suffix}"
        counter += 1

    used_names.add(candidate)
    return candidate


def resolve_output_path(
    input_path: Path,
    output: str | None,
    output_dir: str | None,
) -> Path:
    if output:
        return Path(output)

    target_dir = Path(output_dir) if output_dir else input_path.parent
    return target_dir / f"{input_path.stem}.xlsx"


def convert_file(input_path: Path, output_path: Path, options: SimpleNamespace) -> bool:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")

    payload = load_json(input_path)

    if output_path.exists() and not options.overwrite:
        print(
            f"[SKIP] output exists (use --overwrite): {output_path}",
            file=sys.stderr,
        )
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    used_sheet_names: set[str] = set()
    flatten_map = parse_flatten_specs(options.flatten)

    unknown_tables = sorted(set(flatten_map) - set(payload))
    for table_name in unknown_tables:
        print(
            f"[WARN] input={input_path} table={table_name} not found; flatten ignored",
            file=sys.stderr,
        )

    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for table_name, table_data in payload.items():
                frame, table_warnings = normalize_table(
                    table_name=table_name,
                    table_data=table_data,
                    key_column=options.key_column,
                    indent=options.indent,
                    flatten_columns=flatten_map.get(table_name, set()),
                )
                sheet_name = sanitize_sheet_name(table_name, used_sheet_names)
                frame.to_excel(writer, sheet_name=sheet_name, index=False)
                for warning in table_warnings:
                    print(f"[WARN] input={input_path} {warning}", file=sys.stderr)

                if options.verbose:
                    print(
                        f"[TABLE] input={input_path} table={table_name} "
                        f"sheet={sheet_name} rows={len(frame)} cols={len(frame.columns)}"
                    )
    except ModuleNotFoundError as exc:
        if exc.name == "openpyxl":
            raise RuntimeError(
                "openpyxl is required to write .xlsx files. "
                "Install it with: pip install openpyxl"
            ) from exc
        raise

    return True


def main() -> int:
    args = parse_args()
    try:
        parse_flatten_specs(args.flatten)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    failures = 0
    for input_name in args.input:
        input_path = Path(input_name)
        output_path = resolve_output_path(input_path, args.output, args.output_dir)

        try:
            written = convert_file(input_path, output_path, options=args)
            if written:
                print(f"[OK] {input_path} -> {output_path}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(
                f"[ERROR] failed to convert {input_path}: {exc}",
                file=sys.stderr,
            )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
