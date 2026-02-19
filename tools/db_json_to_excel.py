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


def normalize_table(
    table_name: str,
    table_data: Any,
    key_column: str,
    indent: int | None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    if isinstance(table_data, dict):
        items = list(table_data.items())
        if items and all(isinstance(v, dict) for _, v in items):
            for row_key, row_value in items:
                merged = {key_column: row_key, **row_value}
                rows.append(
                    {
                        col: serialize_nested(value, indent)
                        for col, value in merged.items()
                    }
                )
            return pd.DataFrame(rows)

        for row_key, row_value in items:
            rows.append(
                {
                    key_column: row_key,
                    "value": serialize_nested(row_value, indent),
                }
            )
        return pd.DataFrame(rows)

    if isinstance(table_data, list):
        if table_data and all(isinstance(item, dict) for item in table_data):
            for item in table_data:
                rows.append(
                    {col: serialize_nested(value, indent) for col, value in item.items()}
                )
            return pd.DataFrame(rows)

        return pd.DataFrame(
            [{"value": serialize_nested(item, indent)} for item in table_data]
        )

    return pd.DataFrame([{"value": serialize_nested(table_data, indent)}])


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

    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for table_name, table_data in payload.items():
                frame = normalize_table(
                    table_name=table_name,
                    table_data=table_data,
                    key_column=options.key_column,
                    indent=options.indent,
                )
                sheet_name = sanitize_sheet_name(table_name, used_sheet_names)
                frame.to_excel(writer, sheet_name=sheet_name, index=False)

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
