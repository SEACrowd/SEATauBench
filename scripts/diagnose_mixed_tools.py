#!/usr/bin/env python3
"""Diagnose mixed-language tool partitions and mixed-tool result summaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from experiments.mixed_lang_tools.diagnostics import (  # noqa: E402
    diagnose_mixed_tools_configs,
    summarize_mixed_results,
)

DEFAULT_CONFIGS = [
    "2lang_uniform_en-th",
    "3lang_uniform_en-th-vi",
    "4lang_uniform_en-th-vi-id",
    "5lang_uniform_en-th-vi-id-zh",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Show realized mixed-language tool assignments, docstring coverage, "
            "non-nested partition changes, and optional result deltas."
        )
    )
    parser.add_argument("--domain", required=True, help="Domain name, e.g. telecom.")
    parser.add_argument(
        "--configs",
        nargs="+",
        default=DEFAULT_CONFIGS,
        help="Mixed-tools config names in comparison order.",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Optional tau2 results directory to summarize.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path for the full diagnostic JSON payload.",
    )
    return parser.parse_args()


def _print_partition_summary(payload: dict[str, Any]) -> None:
    print(f"Domain: {payload['domain']}")
    for config in payload["configs"]:
        print(
            "\n"
            f"{config['config_name']}: "
            f"languages={config['languages']} "
            f"strategy={config['partition_strategy']} "
            f"tools_per_added_language={config['tools_per_added_language']} "
            f"counts={config['summary']['by_language']} "
            f"docstrings={config['docstring_count']}/{config['tool_count']} "
            f"group_mode_used={config['group_mode_used']}"
        )
        if config["missing_docstrings"]:
            print(f"  missing_docstrings={config['missing_docstrings']}")
        for tool, lang in config["tool_assignments"].items():
            print(f"  {tool}: {lang}")

    if payload["comparisons"]:
        print("\nAdjacent partition comparisons:")
        for comparison in payload["comparisons"]:
            print(
                f"  {comparison['previous_config']} -> "
                f"{comparison['current_config']}: "
                f"changed={comparison['changed_tool_count']} "
                f"unchanged={comparison['unchanged_tool_count']} "
                f"nested_progressive={comparison['is_nested_progressive']}"
            )


def _print_results_summary(payload: dict[str, Any]) -> None:
    print("\nMixed-tool results:")
    for run in payload["runs"]:
        print(
            f"  {run['experiment_name']}: "
            f"config={run['mixed_tools_config']} "
            f"sims={run['simulation_count']} "
            f"tasks={run['unique_task_count']} "
            f"trials={run['trials']} "
            f"avg_reward={run['average_reward']:.4f}"
        )
    for delta_group in payload["task_score_deltas"]:
        print(
            "\n"
            f"Top task improvements vs {delta_group['baseline_experiment']} "
            f"for {delta_group['experiment_name']}:"
        )
        for row in delta_group["top_improvements"][:5]:
            print(
                f"  delta={row['delta']:.3f} "
                f"base={row['baseline_score']:.3f} "
                f"exp={row['experiment_score']:.3f} "
                f"{row['task_id']}"
            )


def main() -> int:
    args = parse_args()
    payload: dict[str, Any] = {
        "partition_diagnostics": diagnose_mixed_tools_configs(
            domain=args.domain,
            config_names=args.configs,
        )
    }
    if args.results_dir is not None:
        payload["results_summary"] = summarize_mixed_results(args.results_dir)

    _print_partition_summary(payload["partition_diagnostics"])
    if "results_summary" in payload:
        _print_results_summary(payload["results_summary"])

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nWrote JSON: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
