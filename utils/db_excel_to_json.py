#!/usr/bin/env python3
"""Convert Excel database workbooks (including merged multilingual files) to JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

LIST_FLATTEN_PATTERN = re.compile(r"^(.+)\.([^.]+)-(\d+)$")
DICT_FLATTEN_PATTERN = re.compile(r"^(.+)\.([^.]+)$")


@dataclass
class ColumnSelection:
    out_name: str
    src_idx: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert .xlsx database files to JSON"
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        help="Input workbook path(s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON path (only valid with a single input and without --split-tables)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store generated JSON file(s)",
    )
    parser.add_argument(
        "--language",
        help=(
            "Language suffix from merged columns (e.g. th, id, vi). "
            "When set, base columns prefer base.<language> values when available."
        ),
    )
    parser.add_argument(
        "--key-column",
        default="_row_key",
        help="Column name used to reconstruct dict-keyed tables",
    )
    parser.add_argument(
        "--split-tables",
        action="store_true",
        help=(
            "Write one JSON file per sheet using format "
            "'<workbook filename> - <sheet>.json'"
        ),
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indent level for output JSON",
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

    if args.output and (len(args.input) != 1 or args.split_tables):
        parser.error(
            "--output can only be used with a single --input and without --split-tables"
        )

    return args


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return bool(pd.isna(value))


def maybe_parse_json_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value
    return value


def normalize_scalar(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return str(value)
    return value


def select_columns(columns: list[str], language: str | None) -> list[ColumnSelection]:
    col_to_idx = {name: idx for idx, name in enumerate(columns)}

    if language is None:
        return [ColumnSelection(out_name=name, src_idx=idx) for name, idx in col_to_idx.items()]

    variant_by_base: dict[str, dict[str, str]] = {}
    variant_columns: set[str] = set()

    for name in columns:
        if "." not in name:
            continue
        base, suffix = name.rsplit(".", 1)
        if base in col_to_idx:
            variant_by_base.setdefault(base, {})[suffix] = name
            variant_columns.add(name)

    selections: list[ColumnSelection] = []
    for name in columns:
        if name in variant_columns:
            continue

        src_name = name
        if language and name in variant_by_base:
            src_name = variant_by_base[name].get(language, name)
        selections.append(ColumnSelection(out_name=name, src_idx=col_to_idx[src_name]))

    return selections


def unflatten_row(flat_row: dict[str, Any]) -> dict[str, Any]:
    result = dict(flat_row)

    list_groups: dict[str, dict[int, dict[str, Any]]] = {}
    list_keys_to_remove: list[str] = []
    for key, value in result.items():
        match = LIST_FLATTEN_PATTERN.match(key)
        if not match:
            continue
        base, field, index_s = match.groups()
        if base in result:
            continue
        index = int(index_s)
        list_groups.setdefault(base, {}).setdefault(index, {})[field] = value
        list_keys_to_remove.append(key)

    for key in list_keys_to_remove:
        result.pop(key, None)

    for base, grouped in list_groups.items():
        items: list[dict[str, Any]] = []
        for index in sorted(grouped):
            item = grouped[index]
            if item:
                items.append(item)
        if items:
            result[base] = items

    dict_groups: dict[str, dict[str, Any]] = {}
    dict_keys_to_remove: list[str] = []
    for key, value in result.items():
        match = DICT_FLATTEN_PATTERN.match(key)
        if not match:
            continue
        base, field = match.groups()
        if base in result:
            continue
        dict_groups.setdefault(base, {})[field] = value
        dict_keys_to_remove.append(key)

    for key in dict_keys_to_remove:
        result.pop(key, None)

    for base, fields in dict_groups.items():
        if fields:
            result[base] = fields

    return result


def frame_to_table(
    df: pd.DataFrame,
    key_column: str,
    language: str | None,
) -> Any:
    columns = [str(c) for c in df.columns]
    selections = select_columns(columns, language=language)
    rows: list[dict[str, Any]] = []

    for row_idx in range(len(df)):
        flat_row: dict[str, Any] = {}
        for selection in selections:
            raw_value = df.iat[row_idx, selection.src_idx]
            if is_missing(raw_value):
                continue
            value = normalize_scalar(raw_value)
            value = maybe_parse_json_text(value)
            flat_row[selection.out_name] = value

        row_obj = unflatten_row(flat_row)
        rows.append(row_obj)

    if any(key_column in row for row in rows):
        output_dict: dict[str, Any] = {}
        for row in rows:
            if key_column not in row:
                continue
            row_key = str(row[key_column])
            content = {k: v for k, v in row.items() if k != key_column}
            if set(content) == {"value"}:
                output_dict[row_key] = content["value"]
            else:
                output_dict[row_key] = content
        return output_dict

    only_value_column = all((set(row) <= {"value"}) for row in rows)
    if only_value_column:
        return [row.get("value") for row in rows]

    return rows


def load_workbook_frames(path: Path) -> list[tuple[str, pd.DataFrame]]:
    workbook = pd.ExcelFile(path)
    return [(sheet, workbook.parse(sheet, dtype=object)) for sheet in workbook.sheet_names]


def resolve_output_path(
    input_path: Path,
    output: str | None,
    output_dir: str | None,
) -> Path:
    if output:
        return Path(output)
    target_dir = Path(output_dir) if output_dir else input_path.parent
    return target_dir / f"{input_path.stem}.json"


def write_json(path: Path, payload: Any, indent: int, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        print(f"[SKIP] output exists (use --overwrite): {path}", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=indent)
        f.write("\n")
    return True


def convert_file(input_path: Path, args: argparse.Namespace) -> bool:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")

    frames = load_workbook_frames(input_path)
    payload: dict[str, Any] = {}
    for sheet_name, df in frames:
        payload[sheet_name] = frame_to_table(
            df=df,
            key_column=args.key_column,
            language=args.language,
        )

    if args.split_tables:
        wrote_any = False
        target_dir = Path(args.output_dir) if args.output_dir else input_path.parent
        for sheet_name, table_data in payload.items():
            path = target_dir / f"{input_path.name} - {sheet_name}.json"
            wrote = write_json(
                path=path,
                payload={sheet_name: table_data},
                indent=args.indent,
                overwrite=args.overwrite,
            )
            if wrote:
                wrote_any = True
                if args.verbose:
                    print(f"[TABLE] input={input_path} sheet={sheet_name} output={path}")
        return wrote_any

    output_path = resolve_output_path(input_path, args.output, args.output_dir)
    wrote = write_json(
        path=output_path,
        payload=payload,
        indent=args.indent,
        overwrite=args.overwrite,
    )
    if wrote and args.verbose:
        print(
            f"[FILE] input={input_path} output={output_path} "
            f"sheets={len(payload)} language={args.language or 'original'}"
        )
    return wrote


def main() -> int:
    args = parse_args()
    failures = 0

    for input_name in args.input:
        input_path = Path(input_name)
        try:
            wrote = convert_file(input_path, args)
            if wrote:
                print(f"[OK] {input_path}")
        except ModuleNotFoundError as exc:
            if exc.name == "openpyxl":
                print(
                    "[ERROR] openpyxl is required to read .xlsx files. "
                    "Install it with: pip install openpyxl",
                    file=sys.stderr,
                )
                return 1
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(
                f"[ERROR] failed to convert {input_path}: {exc}",
                file=sys.stderr,
            )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
