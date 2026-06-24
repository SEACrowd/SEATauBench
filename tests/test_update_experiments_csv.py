from __future__ import annotations

import csv
from pathlib import Path

import scripts.update_experiments_csv as update_experiments_csv

CSV_FIELDS = [
    "progress",
    "progress_notes",
    "experiment",
    "domain",
    "language_or_scenario",
    "agent_llm",
    "simulation_source",
    "pass_hat_1",
    "pass_hat_2",
    "pass_hat_3",
    "read_action_count",
    "read_acount_total",
    "read_action_percent",
    "write_action_count",
    "write_acount_total",
    "write_action_percent",
    "db_match",
    "language_correctness",
    "total_simulations",
    "total_tasks",
]


def _write_csv(path: Path, row: dict[str, str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def _read_csv(path: Path) -> dict[str, str]:
    with path.open(newline="") as f:
        return next(csv.DictReader(f))


def test_update_csv_blanks_read_metrics_for_telecom(
    monkeypatch, tmp_path: Path
) -> None:
    results_path = tmp_path / "results.json"
    results_path.write_text("{}", encoding="utf-8")

    csv_path = tmp_path / "experiments.csv"
    _write_csv(
        csv_path,
        {
            "progress": "TODO",
            "progress_notes": "",
            "experiment": "translated",
            "domain": "telecom",
            "language_or_scenario": "id",
            "agent_llm": "azure/gpt-5-mini",
            "simulation_source": "",
            "pass_hat_1": "",
            "pass_hat_2": "",
            "pass_hat_3": "",
            "read_action_count": "",
            "read_acount_total": "",
            "read_action_percent": "",
            "write_action_count": "",
            "write_acount_total": "",
            "write_action_percent": "",
            "db_match": "",
            "language_correctness": "",
            "total_simulations": "",
            "total_tasks": "",
        },
    )

    monkeypatch.setattr(
        update_experiments_csv,
        "compute_metrics",
        lambda _: {
            "experiment": "translated",
            "domain": "telecom",
            "language_or_scenario": "id",
            "agent_llm": "azure/gpt-5-mini",
            "pass_hat_1": 49.7,
            "pass_hat_2": 32.5,
            "pass_hat_3": 24.6,
            "read_action_count": 0,
            "read_acount_total": 0,
            "read_action_percent": 0.0,
            "write_action_count": 750,
            "write_acount_total": 937,
            "write_action_percent": 80.0,
            "db_match": 24.0,
            "language_correctness": 99.5,
            "total_simulations": 342,
            "total_tasks": 114,
            "_base_task_count": 114,
            "_evaluated_simulations": 342,
            "simulation_source": "run-dir",
        },
    )

    update_experiments_csv.update_csv(results_path, csv_path)

    row = _read_csv(csv_path)
    assert row["read_action_count"] == ""
    assert row["read_acount_total"] == ""
    assert row["read_action_percent"] == ""
    assert row["write_action_count"] == "750"
    assert row["write_acount_total"] == "937"
    assert row["write_action_percent"] == "80.0"
    assert row["simulation_source"] == "run-dir"
