#!/usr/bin/env python3
"""Merge original and translated Excel DB files into one workbook."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class MergeColumnDescriptor:
    direct_idx: int | None
    dict_subcols: list[tuple[int, str]]
    list_subcols: list[tuple[int, str, int]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge translated Excel DB files into one workbook"
    )
    parser.add_argument("-i", "--original", required=True, help="Original workbook path")
    parser.add_argument(
        "--translated-root",
        required=True,
        help="Directory containing translated language subfolders",
    )
    parser.add_argument("-o", "--output", required=True, help="Output workbook path")
    parser.add_argument(
        "--merge",
        action="append",
        required=True,
        help="Table/column selector in table.column format (repeatable)",
    )
    parser.add_argument(
        "--keep",
        action="append",
        default=[],
        help=(
            "Keep specific nested fields from original in all languages using "
            "table.column.field format (repeatable)"
        ),
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite output file if it exists"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Indent level when serializing nested merged values",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    return parser.parse_args()


def parse_merge_specs(specs: list[str]) -> dict[str, set[str]]:
    merge_map: dict[str, set[str]] = {}
    for spec in specs:
        if spec.count(".") != 1:
            raise ValueError(
                f"invalid --merge selector '{spec}'. Expected format: table.column"
            )
        table, column = spec.split(".", 1)
        if not table or not column:
            raise ValueError(
                f"invalid --merge selector '{spec}'. Expected format: table.column"
            )
        merge_map.setdefault(table, set()).add(column)
    return merge_map


def parse_keep_specs(specs: list[str]) -> dict[str, dict[str, set[str]]]:
    keep_map: dict[str, dict[str, set[str]]] = {}
    for spec in specs:
        if spec.count(".") != 2:
            raise ValueError(
                f"invalid --keep selector '{spec}'. Expected format: table.column.field"
            )
        table, column, field = spec.split(".", 2)
        if not table or not column or not field:
            raise ValueError(
                f"invalid --keep selector '{spec}'. Expected format: table.column.field"
            )
        keep_map.setdefault(table, {}).setdefault(column, set()).add(field)
    return keep_map


def discover_languages(
    translated_root: Path, original_filename: str
) -> list[tuple[str, Path]]:
    if not translated_root.exists() or not translated_root.is_dir():
        raise FileNotFoundError(f"translated root not found: {translated_root}")

    languages: list[tuple[str, Path]] = []
    for entry in sorted(translated_root.iterdir()):
        if not entry.is_dir():
            continue
        candidate = entry / original_filename
        print(f"[DEBUG] checking for language '{entry.name}' at: {candidate}")
        if not candidate.exists():
            raise FileNotFoundError(
                f"translated workbook missing for language '{entry.name}': {candidate}"
            )
        languages.append((entry.name, candidate))

    if not languages:
        raise ValueError(f"no translated language folders found under: {translated_root}")

    return languages


def load_workbook_frames(path: Path) -> list[tuple[str, pd.DataFrame]]:
    workbook = pd.ExcelFile(path)
    return [(sheet, workbook.parse(sheet, dtype=object)) for sheet in workbook.sheet_names]


def validate_workbook_shape(
    base_frames: list[tuple[str, pd.DataFrame]],
    translated_frames: list[tuple[str, pd.DataFrame]],
    language_name: str,
) -> None:
    if len(base_frames) != len(translated_frames):
        raise ValueError(
            f"shape mismatch for language '{language_name}': "
            f"sheet count {len(translated_frames)} != {len(base_frames)}"
        )

    for idx, ((base_name, base_df), (tr_name, tr_df)) in enumerate(
        zip(base_frames, translated_frames)
    ):
        base_rows, base_cols = base_df.shape
        tr_rows, tr_cols = tr_df.shape
        if base_rows != tr_rows or base_cols != tr_cols:
            raise ValueError(
                f"shape mismatch for language '{language_name}' at sheet index {idx} "
                f"(base='{base_name}', translated='{tr_name}'): "
                f"rows/cols {tr_rows}x{tr_cols} != {base_rows}x{base_cols}"
            )


def build_column_index_map(columns: list[str]) -> dict[str, int]:
    return {name: idx for idx, name in enumerate(columns)}


def extract_cell_by_position(df: pd.DataFrame, row_idx: int, col_idx: int) -> Any:
    return df.iat[row_idx, col_idx]


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


def collect_merge_column_positions(
    base_df: pd.DataFrame,
    base_column: str,
) -> MergeColumnDescriptor:
    columns = [str(c) for c in base_df.columns]
    col_to_idx = build_column_index_map(columns)

    direct_idx = col_to_idx.get(base_column)
    dict_subcols: list[tuple[int, str]] = []
    list_subcols: list[tuple[int, str, int]] = []

    list_pattern = re.compile(rf"^{re.escape(base_column)}\.(.+)-(\d+)$")
    dict_pattern = re.compile(rf"^{re.escape(base_column)}\.([^.]+)$")

    for idx, col_name in enumerate(columns):
        list_match = list_pattern.match(col_name)
        if list_match:
            field = list_match.group(1)
            list_index = int(list_match.group(2))
            list_subcols.append((idx, field, list_index))
            continue

        dict_match = dict_pattern.match(col_name)
        if dict_match:
            field = dict_match.group(1)
            dict_subcols.append((idx, field))

    dict_subcols.sort(key=lambda item: item[0])
    list_subcols.sort(key=lambda item: item[0])
    return MergeColumnDescriptor(
        direct_idx=direct_idx,
        dict_subcols=dict_subcols,
        list_subcols=list_subcols,
    )


def reconstruct_value_from_positions(
    df: pd.DataFrame,
    row_idx: int,
    descriptor: MergeColumnDescriptor,
) -> Any:
    if descriptor.list_subcols:
        grouped: dict[int, dict[str, Any]] = {}
        order: list[int] = []
        for col_idx, field, item_index in descriptor.list_subcols:
            value = extract_cell_by_position(df, row_idx, col_idx)
            if is_missing(value):
                continue
            if item_index not in grouped:
                grouped[item_index] = {}
                order.append(item_index)
            grouped[item_index][field] = maybe_parse_json_text(value)

        result: list[dict[str, Any]] = []
        for item_index in sorted(order):
            item = grouped[item_index]
            if item:
                result.append(item)
        if result:
            return result
        return None

    if descriptor.dict_subcols:
        result_dict: dict[str, Any] = {}
        for col_idx, field in descriptor.dict_subcols:
            value = extract_cell_by_position(df, row_idx, col_idx)
            if is_missing(value):
                continue
            result_dict[field] = maybe_parse_json_text(value)
        if result_dict:
            return result_dict
        return None

    if descriptor.direct_idx is not None:
        direct_value = extract_cell_by_position(df, row_idx, descriptor.direct_idx)
        if is_missing(direct_value):
            return None
        return maybe_parse_json_text(direct_value)

    return None


def serialize_value(value: Any, indent: int | None) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=indent)
    return value


def apply_keep_fields(
    original_value: Any,
    translated_value: Any,
    keep_fields: set[str],
) -> Any:
    if not keep_fields:
        return translated_value

    if isinstance(original_value, dict):
        merged = dict(translated_value) if isinstance(translated_value, dict) else {}
        for field in keep_fields:
            if field in original_value:
                merged[field] = original_value[field]
        return merged if merged else translated_value

    if isinstance(original_value, list):
        translated_items = translated_value if isinstance(translated_value, list) else []
        max_len = max(len(original_value), len(translated_items))
        merged_list: list[Any] = []
        for idx in range(max_len):
            original_item = (
                original_value[idx]
                if idx < len(original_value) and isinstance(original_value[idx], dict)
                else {}
            )
            translated_item = (
                translated_items[idx]
                if idx < len(translated_items) and isinstance(translated_items[idx], dict)
                else {}
            )
            if original_item or translated_item:
                merged_item = dict(translated_item)
                for field in keep_fields:
                    if field in original_item:
                        merged_item[field] = original_item[field]
                if merged_item:
                    merged_list.append(merged_item)
        return merged_list if merged_list else translated_value

    return translated_value


def merge_sheet(
    base_df: pd.DataFrame,
    translated_sheet_dfs_by_language: dict[str, pd.DataFrame],
    table_name: str,
    merge_columns: set[str],
    keep_fields_by_column: dict[str, set[str]],
    indent: int | None,
) -> tuple[pd.DataFrame, list[str]]:
    merged_df = base_df.copy()
    warnings: list[str] = []
    columns_to_drop: set[str] = set()
    source_columns = [str(c) for c in base_df.columns]

    for column in sorted(merge_columns):
        descriptor = collect_merge_column_positions(base_df, column)
        has_sources = (
            descriptor.direct_idx is not None
            or bool(descriptor.dict_subcols)
            or bool(descriptor.list_subcols)
        )
        if not has_sources:
            warnings.append(
                f"table={table_name} column={column} not found via direct or flattened columns"
            )

        for col_idx, _field in descriptor.dict_subcols:
            columns_to_drop.add(source_columns[col_idx])
        for col_idx, _field, _list_idx in descriptor.list_subcols:
            columns_to_drop.add(source_columns[col_idx])

        keep_fields = keep_fields_by_column.get(column, set())
        base_col_name = column
        base_values = []
        original_reconstructed_values: list[Any] = []
        for row_idx in range(len(base_df)):
            reconstructed = reconstruct_value_from_positions(base_df, row_idx, descriptor)
            original_reconstructed_values.append(reconstructed)
            base_values.append(serialize_value(reconstructed, indent))
        merged_df[base_col_name] = base_values

        for language_name, lang_df in translated_sheet_dfs_by_language.items():
            lang_col_name = f"{column}.{language_name}"
            lang_values = []
            for row_idx in range(len(lang_df)):
                reconstructed = reconstruct_value_from_positions(
                    lang_df, row_idx, descriptor
                )
                kept = apply_keep_fields(
                    original_value=original_reconstructed_values[row_idx],
                    translated_value=reconstructed,
                    keep_fields=keep_fields,
                )
                lang_values.append(serialize_value(kept, indent))
            merged_df[lang_col_name] = lang_values

    if columns_to_drop:
        merged_df = merged_df.drop(columns=sorted(columns_to_drop), errors="ignore")

    return merged_df, warnings


def main() -> int:
    args = parse_args()

    try:
        merge_map = parse_merge_specs(args.merge)
        keep_map = parse_keep_specs(args.keep)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    original_path = Path(args.original)
    translated_root = Path(args.translated_root)
    output_path = Path(args.output)

    if not original_path.exists():
        print(f"[ERROR] original workbook not found: {original_path}", file=sys.stderr)
        return 1

    if output_path.exists() and not args.overwrite:
        print(
            f"[ERROR] output exists (use --overwrite): {output_path}",
            file=sys.stderr,
        )
        return 1

    try:
        languages = discover_languages(translated_root, original_path.name)
        base_frames = load_workbook_frames(original_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    base_sheet_names = [name for name, _ in base_frames]
    unknown_tables = sorted(set(merge_map) - set(base_sheet_names))
    if unknown_tables:
        print(
            f"[ERROR] merge table(s) not found in original workbook: {', '.join(unknown_tables)}",
            file=sys.stderr,
        )
        return 1

    unknown_keep_tables = sorted(set(keep_map) - set(base_sheet_names))
    if unknown_keep_tables:
        print(
            f"[ERROR] keep table(s) not found in original workbook: {', '.join(unknown_keep_tables)}",
            file=sys.stderr,
        )
        return 1

    for table_name, keep_columns in keep_map.items():
        merge_columns = merge_map.get(table_name, set())
        extra_keep_columns = sorted(set(keep_columns) - set(merge_columns))
        if extra_keep_columns:
            print(
                f"[ERROR] --keep requires matching --merge in table '{table_name}': "
                f"{', '.join(extra_keep_columns)}",
                file=sys.stderr,
            )
            return 1

    translated_frames_by_language: dict[str, list[tuple[str, pd.DataFrame]]] = {}
    for language_name, workbook_path in languages:
        try:
            frames = load_workbook_frames(workbook_path)
            validate_workbook_shape(base_frames, frames, language_name)
            translated_frames_by_language[language_name] = frames
        except Exception as exc:  # noqa: BLE001
            print(
                f"[ERROR] failed to validate language '{language_name}' ({workbook_path}): {exc}",
                file=sys.stderr,
            )
            return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_idx, (table_name, base_df) in enumerate(base_frames):
                merge_columns = merge_map.get(table_name, set())
                per_lang_sheet_dfs = {
                    language_name: frames[sheet_idx][1]
                    for language_name, frames in translated_frames_by_language.items()
                }

                merged_sheet, warnings = merge_sheet(
                    base_df=base_df,
                    translated_sheet_dfs_by_language=per_lang_sheet_dfs,
                    table_name=table_name,
                    merge_columns=merge_columns,
                    keep_fields_by_column=keep_map.get(table_name, {}),
                    indent=args.indent,
                )

                for warning in warnings:
                    print(f"[WARN] {warning}", file=sys.stderr)

                merged_sheet.to_excel(writer, sheet_name=table_name, index=False)

                if args.verbose:
                    print(
                        f"[SHEET] {table_name}: rows={len(merged_sheet)} cols={len(merged_sheet.columns)}"
                    )

        if args.verbose:
            langs = ", ".join(name for name, _ in languages)
            print(f"[LANGUAGES] {langs}")
        print(f"[OK] {original_path} -> {output_path}")
        return 0
    except ModuleNotFoundError as exc:
        if exc.name == "openpyxl":
            print(
                "[ERROR] openpyxl is required to read/write .xlsx files. "
                "Install it with: pip install openpyxl",
                file=sys.stderr,
            )
            return 1
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] failed to write merged workbook: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
