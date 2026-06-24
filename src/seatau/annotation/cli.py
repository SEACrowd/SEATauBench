"""Annotation CLI: ``python -m seatau.annotation <command>``.

Subcommands:
    export   Build a reviewer workbook from current artefacts.
    import   Read a reviewed workbook back into ``{lang}_loc/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from seatau.annotation import export as export_mod
from seatau.annotation.import_reviewed import import_reviewed


def _add_export(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "export",
        help="Build a reviewer workbook from current artefacts.",
        add_help=True,
    )
    # Re-use the export module's argument shape so the surface stays identical.
    p.add_argument("--domains", nargs="+", default=["retail", "telecom"])
    p.add_argument("--lang-id", default="vi", help="language code, e.g. vi")
    p.add_argument("--data-domains-root", default="data/tau2/domains")
    p.add_argument("--src-domains-root", default="src/tau2/domains")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--reviewer", default="unknown")
    p.add_argument("--round-id", default=None)
    p.add_argument("--annotation-metadata-dir", default=None)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")


def _add_import(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "import",
        help="Import a reviewed annotation workbook into {lang}_loc/.",
    )
    p.add_argument("--workbook", required=True, type=Path)
    p.add_argument("--lang", required=True, help="language code, e.g. vi")
    p.add_argument(
        "--allow-machine-fallback",
        action="store_true",
        help="Use name.{lang} when name.{lang}.final is empty (default: reject).",
    )
    p.add_argument(
        "--no-canonical-check",
        action="store_true",
        help="Skip canonical-token preservation validator.",
    )
    p.add_argument(
        "--no-manifest-check",
        action="store_true",
        help="Skip git_commit drift check against the annotation manifest.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m seatau.annotation")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_export(sub)
    _add_import(sub)
    args = parser.parse_args(argv)

    if args.cmd == "export":
        # Forward to the export module's main(). Reconstruct argv so its
        # parser sees the same flags.
        forwarded: list[str] = []
        for flag, value in [
            ("--domains", args.domains),
            ("--lang-id", args.lang_id),
            ("--data-domains-root", args.data_domains_root),
            ("--src-domains-root", args.src_domains_root),
            ("--output", args.output),
            ("--reviewer", args.reviewer),
            ("--round-id", args.round_id),
            ("--annotation-metadata-dir", args.annotation_metadata_dir),
        ]:
            if value is None:
                continue
            if isinstance(value, list):
                forwarded.append(flag)
                forwarded.extend(str(v) for v in value)
            else:
                forwarded.extend([flag, str(value)])
        if args.overwrite:
            forwarded.append("--overwrite")
        if args.verbose:
            forwarded.append("--verbose")
        return export_mod.main(forwarded)

    if args.cmd == "import":
        report = import_reviewed(
            workbook=args.workbook,
            lang=args.lang,
            allow_machine_fallback=args.allow_machine_fallback,
            require_canonical_tokens=not args.no_canonical_check,
            require_manifest=not args.no_manifest_check,
        )
        print(report.summary())
        return 1 if report.errors else 0

    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
