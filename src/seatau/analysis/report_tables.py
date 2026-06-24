"""Generate auditable report tables from SEA-Tau analysis CSVs.

This module does not inspect trajectories directly. It derives report-facing
tables from the reusable analysis outputs:

- `experiments/failure_modes.csv`
- `experiments/failure_mode_tables/<scope>/failure_modes_by_*.csv`
- `experiments/errors.csv`

Usage:
  uv run analyze-report-tables \
    --failure-modes-csv experiments/failure_modes.csv \
    --failure-summary-dir experiments/failure_mode_tables/all_tracked \
    --user-errors-csv experiments/errors.csv \
    --output-dir experiments/failure_mode_tables/report
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

NON_AGENT_MODES = {"success", "non_agent_infrastructure"}
GROUP_TABLES = {
    "domain": "failure_modes_by_domain.csv",
    "language": "failure_modes_by_language.csv",
    "agent": "failure_modes_by_agent.csv",
    "domain_language": "failure_modes_by_domain_language.csv",
    "domain_language_agent": "failure_modes_by_domain_language_agent.csv",
}
GROUP_KEYS = {
    "domain": ("domain",),
    "language": ("lang",),
    "agent": ("agent_llm",),
    "domain_language": ("domain", "lang"),
    "domain_language_agent": ("domain", "lang", "agent_llm"),
}
USER_GROUP_KEYS = {
    "domain": ("domain",),
    "language": ("language",),
    "domain_language": ("domain", "language"),
    "domain_language_agent": ("domain", "language", "agent_llm"),
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into dictionaries."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write rows to CSV, preserving first-seen field order."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_int(value: str | int | None) -> int:
    """Parse an integer CSV field."""
    if value in (None, ""):
        return 0
    return int(value)


def _pct(numerator: int, denominator: int) -> str:
    """Format a percentage with one decimal place."""
    if denominator == 0:
        return "0.0"
    return f"{numerator / denominator * 100:.1f}"


def _mode_names(rows: list[dict[str, str]]) -> list[str]:
    """Return primary failure modes present in a per-simulation table."""
    counts = Counter(row["primary_failure_mode"] for row in rows)
    return [mode for mode, _ in counts.most_common() if mode not in NON_AGENT_MODES]


def aggregate_failure_modes(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Build aggregate primary-failure rows using total tasks as denominator."""
    counts = Counter(row["primary_failure_mode"] for row in rows)
    total = len(rows)
    agent_failures = total - counts["success"] - counts["non_agent_infrastructure"]

    out: list[dict[str, Any]] = []
    for mode, count in counts.most_common():
        if mode in NON_AGENT_MODES:
            continue
        out.append(
            {
                "primary_failure_mode": mode,
                "count": count,
                "total_simulations": total,
                "rate_over_all_tasks": _pct(count, total),
                "agent_failure_count": agent_failures,
                "share_of_agent_failures": _pct(count, agent_failures),
            }
        )
    return out


def _top_modes(row: dict[str, str], top_n: int) -> dict[str, Any]:
    """Return top primary failure modes for a summary row."""
    total = _parse_int(row.get("total_simulations"))
    values: list[tuple[int, str]] = []
    for key, value in row.items():
        if not key.endswith("_count"):
            continue
        mode = key.removesuffix("_count")
        if mode in NON_AGENT_MODES or mode in {
            "total_simulations",
            "agent_failure",
        }:
            continue
        count = _parse_int(value)
        if count:
            values.append((count, mode))
    values.sort(reverse=True)

    out: dict[str, Any] = {}
    for index, (count, mode) in enumerate(values[:top_n], start=1):
        out[f"top_mode_{index}"] = mode
        out[f"top_mode_{index}_count"] = count
        out[f"top_mode_{index}_rate_over_tasks"] = _pct(count, total)
    return out


def compact_failure_summary_rows(
    rows: list[dict[str, str]],
    group_keys: tuple[str, ...],
    top_n: int,
) -> list[dict[str, Any]]:
    """Build compact group rows with task-denominator rates and top modes."""
    out: list[dict[str, Any]] = []
    for row in rows:
        compact = {key: row.get(key, "") for key in group_keys}
        compact.update(
            {
                "total_simulations": _parse_int(row.get("total_simulations")),
                "success_count": _parse_int(row.get("success_count")),
                "success_rate": row.get("success_rate", "0.0"),
                "non_agent_infrastructure_count": _parse_int(
                    row.get("non_agent_infrastructure_count")
                ),
                "non_agent_infrastructure_rate": row.get(
                    "non_agent_infrastructure_rate", "0.0"
                ),
                "agent_failure_count": _parse_int(row.get("agent_failure_count")),
                "agent_failure_rate": row.get("agent_failure_rate", "0.0"),
            }
        )
        compact.update(_top_modes(row, top_n))
        out.append(compact)
    return out


def highest_failure_slices(
    rows: list[dict[str, str]],
    group_keys: tuple[str, ...],
    top_n_modes: int,
    limit: int,
) -> list[dict[str, Any]]:
    """Return the highest agent-failure group slices."""
    compact = compact_failure_summary_rows(rows, group_keys, top_n_modes)
    compact.sort(
        key=lambda row: (
            float(row["agent_failure_rate"]),
            _parse_int(row["agent_failure_count"]),
        ),
        reverse=True,
    )
    return compact[:limit]


def _group_label(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    """Build a stable group label."""
    return " / ".join(str(row.get(key, "")) for key in keys)


def _aggregate_user_rows(
    rows: list[dict[str, str]], group_keys: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Aggregate user-simulator reliability rows by a grouping."""
    grouped: dict[tuple[str, ...], dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for row in rows:
        key = tuple(row.get(group_key, "") for group_key in group_keys)
        values = grouped[key]
        values["num_simulations"] += _parse_int(row.get("num_simulations"))
        values["critical_error_count"] += _parse_int(row.get("critical_error_count"))
        values["benign_error_count"] += _parse_int(row.get("benign_error_count"))
        values["total_error_count"] += _parse_int(row.get("total_error_count"))
        values["user_language_drift_sim_count"] += _parse_int(
            row.get("user_language_drift_sim_count")
        )
        values["user_out_of_scope_count"] += _parse_int(
            row.get("user_out_of_scope_count")
        )

    out: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items()):
        total = values["num_simulations"]
        row = {field: value for field, value in zip(group_keys, key)}
        row.update(
            {
                "num_simulations": total,
                "critical_error_count": values["critical_error_count"],
                "critical_error_rate": _pct(values["critical_error_count"], total),
                "benign_error_count": values["benign_error_count"],
                "benign_error_rate": _pct(values["benign_error_count"], total),
                "total_error_count": values["total_error_count"],
                "total_error_rate": _pct(values["total_error_count"], total),
                "user_language_drift_sim_count": values[
                    "user_language_drift_sim_count"
                ],
                "user_language_drift_sim_rate": _pct(
                    values["user_language_drift_sim_count"], total
                ),
                "user_out_of_scope_count": values["user_out_of_scope_count"],
                "user_out_of_scope_rate": _pct(
                    values["user_out_of_scope_count"], total
                ),
            }
        )
        row["group_label"] = _group_label(row, group_keys)
        out.append(row)
    return out


def write_report_tables(
    failure_modes_csv: Path,
    failure_summary_dir: Path,
    user_errors_csv: Path,
    output_dir: Path,
    top_n_modes: int,
    top_slice_limit: int,
) -> list[Path]:
    """Write report tables derived from analysis CSVs.

    Args:
        failure_modes_csv: Per-simulation failure-mode CSV.
        failure_summary_dir: Directory with `failure_modes_by_*.csv` files.
        user_errors_csv: User reliability summary CSV.
        output_dir: Destination directory for report-facing CSVs.
        top_n_modes: Number of top modes to include in compact summaries.
        top_slice_limit: Number of highest-error slices to include.

    Returns:
        Paths written by the function.
    """
    written: list[Path] = []
    failure_rows = _read_csv(failure_modes_csv)
    aggregate_path = output_dir / "agent_failure_modes_aggregate.csv"
    _write_csv(aggregate_path, aggregate_failure_modes(failure_rows))
    written.append(aggregate_path)

    for group_name, filename in GROUP_TABLES.items():
        group_rows = _read_csv(failure_summary_dir / filename)
        report_rows = compact_failure_summary_rows(
            group_rows, GROUP_KEYS[group_name], top_n_modes
        )
        path = output_dir / f"agent_failure_rates_by_{group_name}.csv"
        _write_csv(path, report_rows)
        written.append(path)

    dla_rows = _read_csv(failure_summary_dir / GROUP_TABLES["domain_language_agent"])
    highest_path = output_dir / "agent_failure_highest_domain_language_agent.csv"
    _write_csv(
        highest_path,
        highest_failure_slices(
            dla_rows,
            GROUP_KEYS["domain_language_agent"],
            top_n_modes,
            top_slice_limit,
        ),
    )
    written.append(highest_path)

    user_rows = _read_csv(user_errors_csv)
    for group_name, group_keys in USER_GROUP_KEYS.items():
        path = output_dir / f"user_reliability_by_{group_name}.csv"
        _write_csv(path, _aggregate_user_rows(user_rows, group_keys))
        written.append(path)

    return written


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--failure-modes-csv",
        type=Path,
        default=Path("experiments/failure_modes.csv"),
        help="Per-simulation failure modes CSV",
    )
    parser.add_argument(
        "--failure-summary-dir",
        type=Path,
        default=Path("experiments/failure_mode_tables/all_tracked"),
        help="Directory with failure_modes_by_*.csv summary tables",
    )
    parser.add_argument(
        "--user-errors-csv",
        type=Path,
        default=Path("experiments/errors.csv"),
        help="User simulator reliability CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/failure_mode_tables/report"),
        help="Output directory for report-facing CSVs",
    )
    parser.add_argument(
        "--top-n-modes",
        type=int,
        default=3,
        help="Number of top primary modes to include in compact tables",
    )
    parser.add_argument(
        "--top-slice-limit",
        type=int,
        default=10,
        help="Number of highest-error domain/language/agent slices to write",
    )
    args = parser.parse_args()

    written = write_report_tables(
        failure_modes_csv=args.failure_modes_csv,
        failure_summary_dir=args.failure_summary_dir,
        user_errors_csv=args.user_errors_csv,
        output_dir=args.output_dir,
        top_n_modes=args.top_n_modes,
        top_slice_limit=args.top_slice_limit,
    )
    print(f"Wrote {len(written)} report tables -> {args.output_dir}")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
