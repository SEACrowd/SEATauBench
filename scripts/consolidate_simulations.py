#!/usr/bin/env python3
"""Consolidate tau2 simulation results into single CSV and JSONL files.

This script walks a directory of tau2 run outputs (default: ``data/simulations``),
loads every ``results.json``, flattens one row per simulation, and writes:

- a CSV file for spreadsheet/analysis workflows
- a JSONL file for downstream scripting / data pipelines

The exporter supports both tau2 storage layouts:
- monolithic JSON results (simulations embedded in ``results.json``)
- directory format (metadata in ``results.json`` + ``simulations/*.json``)
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

FIELDNAMES = [
    "run_dir_name",
    "run_dir",
    "results_path",
    "results_timestamp",
    "experiment_name",
    "domain",
    "agent_implementation",
    "agent_llm",
    "agent_llm_args_json",
    "user_implementation",
    "user_llm",
    "user_llm_args_json",
    "num_trials",
    "max_steps",
    "max_errors",
    "seed",
    "lang_id",
    "lang_components_json",
    "mixed_tools_config",
    "auto_user_system",
    "retrieval_config",
    "retrieval_config_kwargs_json",
    "simulation_id",
    "task_id",
    "trial",
    "mode",
    "termination_reason",
    "reward",
    "reward_basis_json",
    "reward_breakdown_json",
    "db_match",
    "db_reward",
    "action_checks_count",
    "env_assertions_count",
    "nl_assertions_count",
    "communicate_checks_count",
    "auth_status",
    "auth_classification_json",
    "hallucination_retries_used",
    "hallucination_check_json",
    "message_count",
    "agent_cost",
    "user_cost",
    "start_time",
    "end_time",
    "duration",
    "first_agent_message",
    "first_user_message",
]


def json_compact(value: Any) -> str:
    """Serialize nested data in a compact, CSV-safe form."""
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_results_payload(results_path: Path) -> dict[str, Any]:
    """Load a results payload, including dir-format sibling simulation files."""
    data = json.loads(results_path.read_text(encoding="utf-8"))

    if data.get("simulations"):
        return data

    sims_dir = results_path.parent / "simulations"
    if sims_dir.is_dir():
        simulations = []
        for sim_file in sorted(sims_dir.glob("*.json")):
            simulations.append(json.loads(sim_file.read_text(encoding="utf-8")))
        data["simulations"] = simulations
    else:
        data["simulations"] = []

    return data


def find_results_files(input_dir: Path) -> list[Path]:
    """Find top-level run results.json files under the input directory."""
    results_files: list[Path] = []
    for path in sorted(input_dir.rglob("results.json")):
        if path.parent.name == "simulations":
            continue
        results_files.append(path)
    return results_files


def first_message_by_role(messages: list[dict[str, Any]], role: str) -> str:
    """Return the first non-empty message content for a role."""
    for message in messages:
        if message.get("role") != role:
            continue
        content = message.get("content")
        if isinstance(content, str) and content:
            return content
    return ""


def build_row(
    *,
    run_dir: Path,
    results_path: Path,
    results_data: dict[str, Any],
    simulation: dict[str, Any],
) -> dict[str, Any]:
    """Flatten one simulation into a single row."""
    info = results_data.get("info") or {}
    reward_info = simulation.get("reward_info") or {}
    db_check = reward_info.get("db_check") or {}
    messages = simulation.get("messages") or []
    auth = simulation.get("auth_classification") or {}

    row = {
        "run_dir_name": run_dir.name,
        "run_dir": str(run_dir),
        "results_path": str(results_path),
        "results_timestamp": results_data.get("timestamp"),
        "experiment_name": info.get("experiment_name"),
        "domain": (info.get("environment_info") or {}).get("domain_name"),
        "agent_implementation": (info.get("agent_info") or {}).get("implementation"),
        "agent_llm": (info.get("agent_info") or {}).get("llm"),
        "agent_llm_args_json": json_compact(
            (info.get("agent_info") or {}).get("llm_args")
        ),
        "user_implementation": (info.get("user_info") or {}).get("implementation"),
        "user_llm": (info.get("user_info") or {}).get("llm"),
        "user_llm_args_json": json_compact(
            (info.get("user_info") or {}).get("llm_args")
        ),
        "num_trials": info.get("num_trials"),
        "max_steps": info.get("max_steps"),
        "max_errors": info.get("max_errors"),
        "seed": simulation.get("seed", info.get("seed")),
        "lang_id": info.get("lang_id"),
        "lang_components_json": json_compact(info.get("lang_components")),
        "mixed_tools_config": info.get("mixed_tools_config"),
        "auto_user_system": info.get("auto_user_system"),
        "retrieval_config": info.get("retrieval_config"),
        "retrieval_config_kwargs_json": json_compact(
            info.get("retrieval_config_kwargs")
        ),
        "simulation_id": simulation.get("id"),
        "task_id": simulation.get("task_id"),
        "trial": simulation.get("trial"),
        "mode": simulation.get("mode"),
        "termination_reason": simulation.get("termination_reason"),
        "reward": reward_info.get("reward"),
        "reward_basis_json": json_compact(reward_info.get("reward_basis")),
        "reward_breakdown_json": json_compact(reward_info.get("reward_breakdown")),
        "db_match": db_check.get("db_match"),
        "db_reward": db_check.get("db_reward"),
        "action_checks_count": len(reward_info.get("action_checks") or []),
        "env_assertions_count": len(reward_info.get("env_assertions") or []),
        "nl_assertions_count": len(reward_info.get("nl_assertions") or []),
        "communicate_checks_count": len(reward_info.get("communicate_checks") or []),
        "auth_status": auth.get("status"),
        "auth_classification_json": json_compact(auth),
        "hallucination_retries_used": simulation.get("hallucination_retries_used"),
        "hallucination_check_json": json_compact(simulation.get("hallucination_check")),
        "message_count": len(messages),
        "agent_cost": simulation.get("agent_cost"),
        "user_cost": simulation.get("user_cost"),
        "start_time": simulation.get("start_time"),
        "end_time": simulation.get("end_time"),
        "duration": simulation.get("duration"),
        "first_agent_message": first_message_by_role(messages, "assistant"),
        "first_user_message": first_message_by_role(messages, "user"),
    }

    return row


def consolidate_rows(input_dir: Path) -> list[dict[str, Any]]:
    """Collect flattened rows for every simulation in the input directory."""
    rows: list[dict[str, Any]] = []

    for results_path in find_results_files(input_dir):
        run_dir = results_path.parent
        results_data = load_results_payload(results_path)
        for simulation in results_data.get("simulations") or []:
            rows.append(
                build_row(
                    run_dir=run_dir,
                    results_path=results_path,
                    results_data=results_data,
                    simulation=simulation,
                )
            )

    rows.sort(
        key=lambda row: (
            row["run_dir_name"] or "",
            str(row["task_id"] or ""),
            int(row["trial"] or 0),
            row["simulation_id"] or "",
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write flattened rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write flattened rows to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolidate tau2 simulation results into CSV and JSONL."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/simulations"),
        help="Directory containing tau2 run output folders (default: data/simulations).",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Output CSV path (default: <input-dir>/consolidated_simulations.csv).",
    )
    parser.add_argument(
        "--jsonl-out",
        type=Path,
        default=None,
        help="Output JSONL path (default: <input-dir>/consolidated_simulations.jsonl).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_dir = args.input_dir
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    rows = consolidate_rows(input_dir)
    if not rows:
        raise SystemExit(f"No simulations found under: {input_dir}")

    csv_out = args.csv_out or (input_dir / "consolidated_simulations.csv")
    jsonl_out = args.jsonl_out or (input_dir / "consolidated_simulations.jsonl")

    write_csv(csv_out, rows)
    write_jsonl(jsonl_out, rows)

    print(f"Wrote {len(rows)} rows")
    print(f"CSV:   {csv_out}")
    print(f"JSONL: {jsonl_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
