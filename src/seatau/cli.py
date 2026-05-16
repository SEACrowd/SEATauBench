"""SEA-TAU experiment fanout CLI.

Wraps ``tau2 run`` with the experiment-preset matrix defined in
``src/seatau/experiments.yaml``: resolves language components, fans out across
non-English languages, picks mixed-tools configs per language, and logs the
resolved SEA-TAU metadata before each invocation.

This module replaces the legacy ``scripts/run_seatau.sh`` wrapper. Invoke it
either as the installed ``seatau`` console script or as ``python -m seatau``.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from seatau.experiment_matrix import (
    get_experiment_preset,
    is_known_experiment,
    list_all_experiments,
    list_experiment_aliases,
    list_known_experiments,
    list_supported_domains,
    resolve_experiment_name,
)
from seatau.mixed_lang_tools import default_mixed_config_for_lang, find_mixed_config
from seatau.translation.language import (
    list_non_english_languages,
    load_language_registry,
)
from tau2.scripts.seatau_logging import (
    build_seatau_run_settings,
    log_seatau_run_settings,
)

_BASELINE = "baseline"
_TAU2_BASE_CMD: tuple[str, ...] = ("uv", "run", "tau2", "run")

_EPILOG = """\
Experiment presets (source of truth: src/seatau/experiments.yaml):
  mixed_tools    EXP #1: English conversation + mixed-language tool descriptions.
  crosslingual   EXP #2: English assets + L2 user/agent prompting.
  translated     EXP #3: translated context + translated tools + L2 prompting.
  localized      EXP #4: human-localized assets (same components as translated).
  baseline       English-only, no language components.
  Aliases: trans_tool->mixed_tools, mixed_2lang, mixed_3lang, mixed_5lang.

Language behavior:
  - If --lang-id is passed in tau2 args, only that target language is run.
  - Otherwise, non-baseline experiments fan out across every non-English
    language in src/seatau/languages.json.

Examples:
  uv run seatau --experiment crosslingual \\
    --domain retail --lang-id vi --agent-llm azure/gpt-5-mini --num-tasks 5

  uv run seatau --all-experiments \\
    --domain retail --lang-id vi --agent-llm azure/gpt-5-mini --num-tasks 5

  uv run seatau --all-experiments --dry-run \\
    --domain retail --lang-id vi --agent-llm azure/gpt-5-mini --num-tasks 5
"""


@dataclass(frozen=True)
class _Args:
    experiments: tuple[str, ...]
    mixed_config: str | None
    dry_run: bool
    tau_args: tuple[str, ...]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seatau",
        description="Run SEA-TAU experiment presets on top of `tau2 run`.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--experiment",
        metavar="NAME",
        help="Run one experiment preset (alias-resolved against experiments.yaml).",
    )
    group.add_argument(
        "--all-experiments",
        action="store_true",
        help="Run every preset in experiments.yaml's `all_experiments` list.",
    )
    parser.add_argument(
        "--mixed-tools-config",
        metavar="NAME",
        default=None,
        help="Force a specific mixed-tools partition config (overrides preset default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the `tau2 run` invocations without executing them.",
    )
    return parser


def _flag_value(argv: Iterable[str], flag: str) -> str | None:
    """Return the value following ``flag`` in ``argv``, or None if absent."""
    seen = False
    for token in argv:
        if seen:
            return token
        if token == flag:
            seen = True
    return None


def _count_flag(argv: Iterable[str], flag: str) -> int:
    return sum(1 for token in argv if token == flag)


def _exit(message: str, code: int = 2) -> "subprocess.NoReturn":  # type: ignore[name-defined]
    print(message, file=sys.stderr)
    raise SystemExit(code)


def parse_args(argv: list[str]) -> _Args:
    """Parse argv into script-owned options + tau2 passthrough."""
    parser = _build_parser()
    ns, tau_args = parser.parse_known_args(argv)

    if ns.experiment is not None:
        experiments: tuple[str, ...] = (ns.experiment,)
    else:
        experiments = tuple(list_all_experiments())

    for raw in experiments:
        if not is_known_experiment(raw):
            valid = ", ".join(list_known_experiments())
            aliases = list_experiment_aliases()
            alias_msg = (
                f" Aliases: {', '.join(f'{k}->{v}' for k, v in sorted(aliases.items()))}"
                if aliases
                else ""
            )
            _exit(f"Unknown experiment: {raw!r}. Valid: {valid}.{alias_msg}")

    if _count_flag(tau_args, "--mixed-tools-config") > 0 and ns.mixed_tools_config:
        _exit("Pass --mixed-tools-config only once (script option).")
    if _count_flag(tau_args, "--mixed-tools-config") > 1:
        _exit("Pass --mixed-tools-config at most once.")

    domain = _flag_value(tau_args, "--domain")
    if domain is not None:
        if domain == "mock":
            print("[SKIP] SEA-TAU experiments do not run on domain 'mock'.")
            raise SystemExit(0)
        supported = list_supported_domains()
        if domain not in supported:
            _exit(
                f"Unknown domain: {domain!r}. "
                f"Supported: {', '.join(supported)}."
            )

    lang_id = _flag_value(tau_args, "--lang-id")
    if lang_id is not None:
        registry = load_language_registry()
        if lang_id not in registry:
            _exit(
                f"Unknown lang-id: {lang_id!r}. "
                f"Available: {', '.join(sorted(registry))}."
            )

    mixed_config = ns.mixed_tools_config or _flag_value(tau_args, "--mixed-tools-config")
    if mixed_config and find_mixed_config(mixed_config) is None:
        _exit(f"Mixed-tools config not found: {mixed_config!r}.")

    return _Args(
        experiments=experiments,
        mixed_config=ns.mixed_tools_config,
        dry_run=ns.dry_run,
        tau_args=tuple(tau_args),
    )


def _resolve_languages(tau_args: tuple[str, ...]) -> tuple[list[str], bool]:
    """Return (languages, explicit) based on whether --lang-id is in passthrough."""
    explicit = _flag_value(tau_args, "--lang-id")
    if explicit:
        return [explicit], True
    return list_non_english_languages(), False


def _resolve_mixed_config_name(
    preset_default: str | None,
    user_override: str | None,
    lang: str,
) -> str | None:
    """Resolve which mixed-tools config to use, mirroring the bash precedence."""
    if user_override:
        return user_override
    if preset_default:
        return preset_default
    return default_mixed_config_for_lang(lang)


@dataclass(frozen=True)
class Invocation:
    """One resolved `tau2 run` invocation."""

    experiment: str
    lang: str
    mixed_config: str | None
    argv: tuple[str, ...]


def iter_invocations(args: _Args) -> Iterator[Invocation | str]:
    """Yield Invocation objects (and ``[SKIP] ...`` strings) for each fan-out step."""
    languages, lang_explicit = _resolve_languages(args.tau_args)

    for raw_exp in args.experiments:
        experiment = resolve_experiment_name(raw_exp)
        if experiment == _BASELINE:
            yield Invocation(
                experiment=experiment,
                lang="en",
                mixed_config=None,
                argv=_TAU2_BASE_CMD + args.tau_args,
            )
            continue

        preset = get_experiment_preset(experiment)
        for lang in languages:
            local_args: list[str] = list(args.tau_args)
            mixed_cfg: str | None = None

            if preset.mixed_tools:
                mixed_cfg = _resolve_mixed_config_name(
                    preset.default_mixed_config, args.mixed_config, lang
                )
                if mixed_cfg is None:
                    if args.mixed_config:
                        _exit(
                            f"Mixed-tools config not found: {args.mixed_config!r}."
                        )
                    if lang_explicit:
                        _exit(
                            f"No default mixed-tools config available for lang {lang!r}. "
                            "Use --mixed-tools-config."
                        )
                    yield (
                        f"[SKIP] mixed_tools for lang '{lang}': no default config "
                        "available. Pass --mixed-tools-config to force a config."
                    )
                    continue

            if not lang_explicit:
                local_args += ["--lang-id", lang]
            if "--seatau-experiment" not in args.tau_args:
                local_args += ["--seatau-experiment", experiment]
            if mixed_cfg is not None:
                local_args += ["--mixed-tools-config", mixed_cfg]

            yield Invocation(
                experiment=experiment,
                lang=lang,
                mixed_config=mixed_cfg,
                argv=_TAU2_BASE_CMD + tuple(local_args),
            )


def _print_command(argv: tuple[str, ...]) -> None:
    print("$ " + " ".join(shlex.quote(token) for token in argv))


def _log_settings(invocation: Invocation, log_level: str) -> None:
    settings = build_seatau_run_settings(
        experiment=invocation.experiment,
        lang_id=invocation.lang,
        mixed_tools_config=invocation.mixed_config,
    )
    log_seatau_run_settings(settings=settings, log_level=log_level)


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``seatau`` / ``python -m seatau``."""
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    log_level = _flag_value(args.tau_args, "--log-level") or "INFO"

    exit_code = 0
    for item in iter_invocations(args):
        if isinstance(item, str):
            print(item)
            continue
        if item.experiment != _BASELINE and not args.dry_run:
            _log_settings(item, log_level)
        _print_command(item.argv)
        if args.dry_run:
            continue
        result = subprocess.run(list(item.argv), check=False)
        if result.returncode != 0:
            exit_code = result.returncode
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
