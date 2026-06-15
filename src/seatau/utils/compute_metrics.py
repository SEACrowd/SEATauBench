"""Compute experiment metrics from results.json files and normalize experiments.csv."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from math import comb
from pathlib import Path

from seatau.analysis.model_names import canonical_model_name

DOMAIN_MAX_TOTAL_SIMULATIONS = {
    "airline": 150,
    "retail": 342,
    "telecom": 342,
}


def _pass_at_k(task_rewards_list: list[list[float]], k: int) -> float | None:
    """Compute E[C(c,k)/C(n,k)] where c=correct trials and n=total trials."""
    values = []
    for trials in task_rewards_list:
        n = len(trials)
        if n < k:
            continue
        c = sum(1 for r in trials if r == 1.0)
        denom = comb(n, k)
        values.append(comb(c, k) / denom if denom > 0 else 0.0)
    return sum(values) / len(values) if values else None


def _expected_total_simulations(domain: str) -> int:
    try:
        return DOMAIN_MAX_TOTAL_SIMULATIONS[domain]
    except KeyError as exc:
        raise ValueError(f"unknown domain: {domain!r}") from exc


def _to_proportion(value: str | float | int | None) -> float | None:
    """Convert a tracker value to a 0-1 proportion when possible."""
    if value is None:
        return None
    if isinstance(value, str):
        if value == "":
            return None
        value = float(value)

    numeric = float(value)
    if numeric > 1.0:
        numeric /= 100.0
    return round(numeric, 3)


def _relative_simulation_source(results_path: Path) -> str:
    parent = results_path.parent
    if not parent.is_absolute():
        return parent.as_posix()
    try:
        return parent.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return parent.as_posix()


def infer_progress(
    domain: str,
    total_simulations: int,
    total_tasks: int,
    base_task_count: int,
    evaluated_simulations: int,
) -> str:
    """Infer row progress from the actual run metrics."""
    if total_simulations < _expected_total_simulations(domain):
        return "IN_PROGRESS"
    if total_tasks < base_task_count:
        return "PARTIAL"
    if evaluated_simulations < total_simulations:
        return "NEEDS_CHECK"
    return "DONE"


def normalize_experiments_csv(
    csv_path: Path,
    output_path: Path | None = None,
) -> Path:
    """Rewrite ``experiments.csv`` using the current translated tracker format."""
    destination = output_path or csv_path
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"{csv_path} is missing a header row")
        rows = list(reader)

    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        row.pop(None, None)
        normalized_row: dict[str, str] = {}
        for field in fieldnames:
            normalized_row[field] = row.get(field, "")
        normalized_rows.append(normalized_row)

    with destination.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)

    return destination


def compute_metrics(results_path: Path) -> dict[str, object]:
    """Compute pass@k, action, db_match, and language correctness metrics."""
    with results_path.open() as f:
        data = json.load(f)

    info = data["info"]
    simulations = data["simulations"]
    tasks = data.get("tasks", [])

    task_rewards: dict[str, list[float]] = defaultdict(list)
    read_match = 0
    read_total = 0
    write_match = 0
    write_total = 0
    db_matches: list[float] = []
    lang_scores: list[float] = []
    evaluated = 0

    for sim in simulations:
        reward_info = sim.get("reward_info")
        if reward_info is None:
            continue

        reward = reward_info.get("reward")
        if reward is None:
            continue

        evaluated += 1
        task_id = sim["task_id"]
        task_rewards[task_id].append(reward)

        db_check = reward_info.get("db_check") or {}
        if db_check.get("db_match") is not None:
            db_matches.append(float(db_check["db_match"]))

        lang_info = (reward_info.get("info") or {}).get("language_correctness")
        if lang_info and lang_info.get("score") is not None:
            lang_scores.append(float(lang_info["score"]))

        action_checks = reward_info.get("action_checks") or []
        for ac in action_checks:
            tool_type = ac.get("tool_type", "")
            matched = int(ac.get("action_match", False))
            if tool_type == "read":
                read_total += 1
                read_match += matched
            elif tool_type == "write":
                write_total += 1
                write_match += matched

    tasks_rewards = list(task_rewards.values())
    n_tasks = len(tasks_rewards)
    return {
        "experiment": (info.get("seatau_info") or {}).get("experiment_name", ""),
        "domain": (info.get("environment_info") or {}).get("domain_name", ""),
        "language_or_scenario": info.get("lang_id", ""),
        "agent_llm": canonical_model_name(
            (info.get("agent_info") or {}).get("llm", "")
        ),
        "pass_hat_1": _to_proportion(_pass_at_k(tasks_rewards, 1)),
        "pass_hat_2": _to_proportion(_pass_at_k(tasks_rewards, 2)),
        "pass_hat_3": _to_proportion(_pass_at_k(tasks_rewards, 3)),
        "read_action_count": read_match,
        "read_acount_total": read_total,
        "read_action": _to_proportion(read_match / read_total if read_total else None),
        "write_action_count": write_match,
        "write_acount_total": write_total,
        "write_action": _to_proportion(write_match / write_total if write_total else None),
        "db_match": _to_proportion(sum(db_matches) / len(db_matches) if db_matches else None),
        "language_correctness": _to_proportion(
            sum(lang_scores) / len(lang_scores) if lang_scores else None
        ),
        "total_simulations": len(simulations),
        "total_tasks": n_tasks,
        "_base_task_count": len(tasks),
        "_evaluated_simulations": evaluated,
        "simulation_source": _relative_simulation_source(results_path),
        "suggested_progress": infer_progress(
            str((info.get("environment_info") or {}).get("domain_name", "")),
            len(simulations),
            n_tasks,
            len(tasks),
            evaluated,
        ),
    }


def _format_metric_value(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.1%}"
    return str(value)


if __name__ == "__main__":
    runs = [
        "2026-05-16-13-43-08_airline_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-16-15-12-02_airline_th_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-16-17-08-16_airline_tl_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-16-18-54-35_airline_vi_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-16-20-45-18_airline_zh_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-16-01-37-48_retail_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
        "2026-05-17-02-21-54_telecom_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    ]
    sim_base = Path("data/simulations")

    for run in runs:
        results_path = sim_base / run / "results.json"
        if not results_path.exists():
            print(f"MISSING: {results_path}")
            continue
        metrics = compute_metrics(results_path)
        print(f"\n{'=' * 60}")
        print(f"Run: {run}")
        for key, value in metrics.items():
            print(f"  {key}: {_format_metric_value(value)}")
