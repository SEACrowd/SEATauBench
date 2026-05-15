"""Command-line entry points for SEA-TAU localization helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seatau.annotation.export import main as export_annotation_main
from seatau.localization.patch_sheet import patch_annotation_workbook, scan_workbook
from seatau.localization.synthetic import generate_value_pools, save_value_pools


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m seatau.localization",
        description="Generate and apply synthetic names/addresses for annotation workbooks.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate", help="Generate a reusable synthetic value catalog."
    )
    generate.add_argument("--lang", required=True, help="Target language code.")
    generate.add_argument("--count", type=int, default=32)
    generate.add_argument("--seed", type=int, default=None)
    generate.add_argument("-o", "--output", required=True, type=Path)

    scan = subparsers.add_parser(
        "scan", help="Inspect an annotation workbook and summarize candidates."
    )
    scan.add_argument("--lang", required=True)
    scan.add_argument("--workbook", required=True, type=Path)

    patch = subparsers.add_parser(
        "propagate",
        help="Replace localized name/address content in an annotation workbook.",
    )
    patch.add_argument("--lang", required=True)
    patch.add_argument("--workbook", required=True, type=Path)
    patch.add_argument("-o", "--output", type=Path, default=None)
    patch.add_argument("--catalog", type=Path, default=None)
    patch.add_argument("--seed", type=int, default=None)

    export = subparsers.add_parser(
        "export",
        help=(
            "Run the annotation exporter and then propagate synthetic values "
            "into the generated workbook."
        ),
    )
    export.add_argument("--domains", nargs="+", default=["retail", "telecom"])
    export.add_argument("--lang-id", required=True)
    export.add_argument("-o", "--output", required=True, type=Path)
    export.add_argument("--reviewer", default="unknown")
    export.add_argument("--round-id", default=None)
    export.add_argument("--annotation-metadata-dir", default=None)
    export.add_argument("--overwrite", action="store_true")
    export.add_argument("--catalog", type=Path, default=None)
    export.add_argument("--seed", type=int, default=None)
    export.add_argument("--count", type=int, default=32)
    export.add_argument("--data-domains-root", default="data/tau2/domains")
    export.add_argument("--src-domains-root", default="src/tau2/domains")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        pools = generate_value_pools(args.lang, count=args.count, seed=args.seed)
        save_value_pools(pools, args.output)
        print(json.dumps(pools.to_dict(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "scan":
        cases = scan_workbook(args.workbook, lang=args.lang)
        for category, value_cases in sorted(cases.items()):
            print(f"{category}: {len(value_cases)}")
            for case in value_cases[:5]:
                print(f"  - {case.address} -> {case.source}")
        return 0

    if args.command == "propagate":
        report = patch_annotation_workbook(
            args.workbook,
            lang=args.lang,
            output_path=args.output,
            catalog_path=args.catalog,
            seed=args.seed,
        )
        print(report.summary())
        return 0

    if args.command == "export":
        rc = export_annotation_main(
            [
                "--domains",
                *args.domains,
                "--lang-id",
                args.lang_id,
                "-o",
                str(args.output),
                "--reviewer",
                args.reviewer,
                "--data-domains-root",
                args.data_domains_root,
                "--src-domains-root",
                args.src_domains_root,
                *(["--round-id", args.round_id] if args.round_id else []),
                *(
                    ["--annotation-metadata-dir", args.annotation_metadata_dir]
                    if args.annotation_metadata_dir
                    else []
                ),
                *(["--overwrite"] if args.overwrite else []),
            ]
        )
        if rc != 0:
            return rc
        report = patch_annotation_workbook(
            args.output,
            lang=args.lang_id,
            output_path=args.output,
            catalog_path=args.catalog,
            seed=args.seed,
        )
        print(report.summary())
        return 0

    parser.error(f"unknown command: {args.command}")
    return 1
