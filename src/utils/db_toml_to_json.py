#!/usr/bin/env python3
"""Convert TOML database files into JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None
    import toml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert TOML files into JSON files")
    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        help="Input TOML file path(s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file path (only valid with a single input)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store generated JSON files",
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

    if args.output and len(args.input) != 1:
        parser.error("--output can only be used with a single --input file")

    return args


def load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"input file not found: {path}")

    try:
        if tomllib is not None:
            with path.open("rb") as f:
                payload = tomllib.load(f)
        else:
            with path.open("r", encoding="utf-8") as f:
                payload = toml.load(f)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"invalid TOML: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("top-level TOML must be a table/object")

    return payload


def resolve_output_path(
    input_path: Path,
    output: str | None,
    output_dir: str | None,
) -> Path:
    if output:
        return Path(output)

    target_dir = Path(output_dir) if output_dir else input_path.parent
    return target_dir / f"{input_path.stem}.json"


def convert_file(input_path: Path, output_path: Path, args: argparse.Namespace) -> bool:
    payload = load_toml(input_path)

    if output_path.exists() and not args.overwrite:
        print(
            f"[SKIP] output exists (use --overwrite): {output_path}",
            file=sys.stderr,
        )
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=args.indent)
        f.write("\n")

    if args.verbose:
        top_level_keys = len(payload)
        print(
            f"[FILE] input={input_path} output={output_path} top_level_keys={top_level_keys}"
        )

    return True


def main() -> int:
    args = parse_args()

    failures = 0
    for input_name in args.input:
        input_path = Path(input_name)
        output_path = resolve_output_path(input_path, args.output, args.output_dir)

        try:
            written = convert_file(input_path, output_path, args)
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
