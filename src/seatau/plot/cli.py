"""Common plot dispatcher for SEA-TauBench figures."""

from __future__ import annotations

import argparse
import importlib
import sys

from seatau.plot.registry import COUPLED_FIGURE_MODULES, FIGURE_MODULES

COMMAND_TO_MODULE = {
    **FIGURE_MODULES,
    **COUPLED_FIGURE_MODULES,
}
UNIQUE_MODULES = list(dict.fromkeys(COMMAND_TO_MODULE.values()))


def _load_main(module_path: str):
    module = importlib.import_module(module_path)
    main = getattr(module, "main", None)
    if main is None:
        raise AttributeError(f"{module_path} does not define main()")
    return main


def _run_module(module_path: str, argv: list[str]) -> int:
    old_argv = sys.argv
    sys.argv = [module_path, *argv]
    try:
        result = _load_main(module_path)()
    finally:
        sys.argv = old_argv
    return 0 if result is None else int(result)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plot", description=__doc__)
    parser.add_argument(
        "command",
        choices=["all", "list", *COMMAND_TO_MODULE.keys()],
        help="Figure stem to run, or list/all for batch operations.",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Forwarded to modules.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        if args.args:
            parser.error("list does not accept extra arguments")
        for stem, module in COMMAND_TO_MODULE.items():
            print(f"{stem}\t{module}")
        return 0

    if args.command == "all":
        if args.args:
            parser.error("all does not accept extra arguments")
        for module_path in UNIQUE_MODULES:
            rc = _run_module(module_path, [])
            if rc != 0:
                return rc
        return 0

    module_path = COMMAND_TO_MODULE[args.command]
    return _run_module(module_path, args.args)


if __name__ == "__main__":
    raise SystemExit(main())
