#!/usr/bin/env python3
"""Summarize tau2 simulation runs into one CSV row per experiment."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from tau2.data_model.simulation import Results
from tau2.metrics.agent_metrics import compute_metrics

COLUMNS = [
    "experiment",
    "full_experiment_name",
    "domain",
    "agent_model",
    "user_model",
    "pass_1",
    "pass_2",
    "pass_3",
    "total_simulations",
    "total_tasks",
    "average_reward",
    "avg_cost_per_conversation",
    "read_actions_count",
    "read_actions_total",
    "read_actions_percent",
    "write_actions_count",
    "write_actions_total",
    "write_actions_percent",
    "db_match_count",
    "db_mismatch_count",
    "db_match_percent",
    "authentication_not_checked",
    "normal_stop_total",
    "normal_stop_user",
    "normal_stop_agent",
    "agent_errors",
    "agent_error_sims_by_severity",
    "user_errors",
    "user_error_sims_by_severity",
]

RESULT_FILE_NAMES = ("results.json", "results_reviewed.json")


def find_results_files(input_path: Path) -> list[Path]:
    """Find result files under a file, run directory, or parent experiments dir.

    When both ``results.json`` and ``results_reviewed.json`` are present for a
    run, the reviewed file wins so embedded review/auth metrics are included.
    """
    input_path = Path(input_path)
    if input_path.is_file():
        return [input_path]

    reviewed_file = input_path / "results_reviewed.json"
    results_file = input_path / "results.json"
    if reviewed_file.exists():
        return [reviewed_file]
    if results_file.exists():
        return [results_file]

    files_by_run_dir: dict[Path, Path] = {}
    for path in sorted(input_path.rglob("results*.json")):
        if path.name not in RESULT_FILE_NAMES:
            continue
        if path.parent.name == "simulations":
            continue

        current = files_by_run_dir.get(path.parent)
        if current is None or path.name == "results_reviewed.json":
            files_by_run_dir[path.parent] = path

    return [files_by_run_dir[run_dir] for run_dir in sorted(files_by_run_dir)]


def load_results(path: Path) -> Results:
    """Load a Results object while preserving monolithic reviewed files.

    ``Results.load`` treats any file with a sibling ``simulations/`` directory as
    dir-format metadata. Reviewed result files are often monolithic JSON written
    next to that directory, so we validate embedded simulations directly when
    present.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("simulations"):
        data.pop("format_version", None)
        return Results.model_validate(data)
    return Results.load(Path(path))


def normalize_experiment_name(
    results: Results, results_path: Path, strip_prefix: str | None
) -> str:
    """Return the display experiment name for a result file."""
    experiment = results.info.experiment_name or results_path.parent.name
    if strip_prefix and experiment.startswith(strip_prefix):
        return experiment[len(strip_prefix) :]
    return experiment


def full_experiment_name(results: Results, results_path: Path) -> str:
    """Return the most complete experiment/run name available for a result file."""
    experiment = results.info.experiment_name or ""
    run_dir_name = results_path.parent.name

    if experiment and run_dir_name != experiment and run_dir_name.endswith(experiment):
        return run_dir_name
    return experiment or run_dir_name


def safe_percent(count: int, total: int) -> float | str:
    """Return a rounded percentage, or blank when there is no denominator."""
    if total == 0:
        return ""
    return round(count / total * 100, 1)


def clean_float(value: float | None, digits: int) -> float | str:
    """Round a float for CSV output, preserving blanks for missing/NaN values."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return round(value, digits)


def format_sims_by_severity(counts: dict[str, int], severity_order: list[str]) -> str:
    """Format non-clean simulation severity counts for a compact CSV cell."""
    parts = []
    seen = set()
    for severity in severity_order:
        seen.add(severity)
        count = counts.get(severity, 0)
        if count > 0:
            parts.append(f"{severity}={count}")

    for severity in sorted(set(counts) - seen - {"none"}):
        count = counts.get(severity, 0)
        if count > 0:
            parts.append(f"{severity}={count}")

    return ";".join(parts) if parts else "-"


def build_summary_row(
    results_path: Path, strip_experiment_prefix: str | None = "english_"
) -> dict[str, Any]:
    """Build the requested summary CSV row for one result file."""
    results = load_results(results_path)
    metrics = compute_metrics(results)

    read_total = metrics.total_read_actions
    write_total = metrics.total_write_actions
    db_total = metrics.db_match_count + metrics.db_mismatch_count
    normal_stop_user = metrics.termination_user_stop
    normal_stop_agent = metrics.termination_agent_stop

    return {
        "experiment": normalize_experiment_name(
            results, results_path, strip_experiment_prefix
        ),
        "full_experiment_name": full_experiment_name(results, results_path),
        "domain": results.info.environment_info.domain_name,
        "agent_model": results.info.agent_info.llm or "",
        "user_model": results.info.user_info.llm or "",
        "pass_1": clean_float(metrics.pass_hat_ks.get(1), 3),
        "pass_2": clean_float(metrics.pass_hat_ks.get(2), 3),
        "pass_3": clean_float(metrics.pass_hat_ks.get(3), 3),
        "total_simulations": metrics.total_simulations,
        "total_tasks": metrics.total_tasks,
        "average_reward": clean_float(metrics.avg_reward, 4),
        "avg_cost_per_conversation": clean_float(metrics.avg_agent_cost, 4),
        "read_actions_count": metrics.correct_read_actions,
        "read_actions_total": read_total,
        "read_actions_percent": safe_percent(metrics.correct_read_actions, read_total),
        "write_actions_count": metrics.correct_write_actions,
        "write_actions_total": write_total,
        "write_actions_percent": safe_percent(
            metrics.correct_write_actions, write_total
        ),
        "db_match_count": metrics.db_match_count,
        "db_mismatch_count": metrics.db_mismatch_count,
        "db_match_percent": safe_percent(metrics.db_match_count, db_total),
        "authentication_not_checked": metrics.auth_not_checked,
        "normal_stop_total": normal_stop_user + normal_stop_agent,
        "normal_stop_user": normal_stop_user,
        "normal_stop_agent": normal_stop_agent,
        "agent_errors": metrics.total_agent_errors,
        "agent_error_sims_by_severity": format_sims_by_severity(
            metrics.sims_by_max_agent_severity, ["critical", "minor"]
        ),
        "user_errors": metrics.total_user_errors,
        "user_error_sims_by_severity": format_sims_by_severity(
            metrics.sims_by_max_user_severity,
            ["critical_helped", "critical_hindered", "critical", "minor"],
        ),
    }


def build_summary_rows(
    input_path: Path, strip_experiment_prefix: str | None = "english_"
) -> list[dict[str, Any]]:
    """Build summary rows for every result file found under ``input_path``."""
    result_files = find_results_files(input_path)
    if not result_files:
        raise FileNotFoundError(f"No results.json files found under: {input_path}")

    rows = [
        build_summary_row(path, strip_experiment_prefix=strip_experiment_prefix)
        for path in result_files
    ]
    return sorted(rows, key=lambda row: str(row["experiment"]))


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write summary rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def default_output_path(input_path: Path) -> Path:
    """Return the default CSV output path for an input path."""
    if input_path.is_dir():
        return input_path / "results_summary.csv"
    return input_path.with_name(f"{input_path.stem}_summary.csv")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize tau2 result files into one CSV row per experiment."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="A results.json file, a run directory, or a directory of run folders.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: <path>/results_summary.csv for directories).",
    )
    parser.add_argument(
        "--strip-experiment-prefix",
        default="english_",
        help="Prefix to strip from experiment names (default: english_).",
    )
    parser.add_argument(
        "--no-strip-experiment-prefix",
        action="store_true",
        help="Keep experiment names exactly as stored in results.json.",
    )
    return parser.parse_args()


def main(
    path: Path | str | None = None,
    output: Path | str | None = None,
    strip_experiment_prefix: str | None = "english_",
) -> list[dict[str, Any]]:
    """Summarize result files and write the CSV output."""
    if path is None:
        args = parse_args()
        path = args.path
        output = args.output
        strip_experiment_prefix = (
            None if args.no_strip_experiment_prefix else args.strip_experiment_prefix
        )

    input_path = Path(path)
    output_path = (
        Path(output) if output is not None else default_output_path(input_path)
    )
    rows = build_summary_rows(
        input_path, strip_experiment_prefix=strip_experiment_prefix
    )
    write_summary_csv(output_path, rows)
    print(f"Wrote {len(rows)} experiment summaries to {output_path}")
    return rows


if __name__ == "__main__":
    main()
