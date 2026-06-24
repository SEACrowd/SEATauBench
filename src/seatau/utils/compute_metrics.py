"""Compute experiment metrics from results.json files and write to experiments.csv."""

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
    """Compute E[C(c,k)/C(n,k)] where c=correct trials, n=total trials per task."""
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


def _infer_progress(
    domain: str,
    total_simulations: int,
    total_tasks: int,
    base_task_count: int,
    evaluated_simulations: int,
) -> str:
    if total_simulations < _expected_total_simulations(domain):
        return "IN_PROGRESS"
    if total_tasks < base_task_count:
        return "PARTIAL"
    if evaluated_simulations < total_simulations:
        return "NEEDS_CHECK"
    return "DONE"


def compute_metrics(results_path: Path) -> dict:
    """Compute pass@k, action, db_match, and language correctness metrics."""
    with open(results_path) as f:
        data = json.load(f)

    info = data["info"]
    simulations = data["simulations"]
    tasks = data.get("tasks", [])

    # Group by task_id
    task_rewards: dict[str, list[float]] = defaultdict(list)
    read_match = 0
    read_total = 0
    write_match = 0
    write_total = 0
    db_matches = []
    lang_scores = []
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

        # DB match
        db_check = reward_info.get("db_check") or {}
        if db_check.get("db_match") is not None:
            db_matches.append(float(db_check["db_match"]))

        # Language correctness
        lang_info = (reward_info.get("info") or {}).get("language_correctness")
        if lang_info and lang_info.get("score") is not None:
            lang_scores.append(lang_info["score"])

        # Action checks (read/write)
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

    # Pass@k using E[C(c,k)/C(n,k)] (excludes tasks with fewer than k trials)
    tasks = list(task_rewards.values())
    n_tasks = len(tasks)
    p1 = _pass_at_k(tasks, 1)
    p2 = _pass_at_k(tasks, 2)
    p3 = _pass_at_k(tasks, 3)

    db_match_pct = sum(db_matches) / len(db_matches) if db_matches else None
    lang_corr_pct = sum(lang_scores) / len(lang_scores) if lang_scores else None

    read_pct = read_match / read_total if read_total else None
    write_pct = write_match / write_total if write_total else None

    def fmt_pct(v: float | None) -> str | None:
        return round(v * 100, 1) if v is not None else None

    # Extract run metadata from info
    lang_id = info.get("lang_id", "")
    domain = (info.get("environment_info") or {}).get("domain_name", "")
    agent_llm = canonical_model_name((info.get("agent_info") or {}).get("llm", ""))
    experiment = (info.get("seatau_info") or {}).get("experiment_name", "")

    return {
        "scenario": experiment,
        "domain": domain,
        "language_or_scenario": lang_id,
        "agent_llm": agent_llm,
        "pass_hat_1": fmt_pct(p1),
        "pass_hat_2": fmt_pct(p2),
        "pass_hat_3": fmt_pct(p3),
        "read_action_count": read_match,
        "read_action_total": read_total,
        "read_action_percent": fmt_pct(read_pct),
        "write_action_count": write_match,
        "write_action_total": write_total,
        "write_action_percent": fmt_pct(write_pct),
        "db_match": fmt_pct(db_match_pct),
        "language_correctness": fmt_pct(lang_corr_pct),
        "total_simulations": len(simulations),
        "total_tasks": n_tasks,
        "_base_task_count": len(tasks),
        "_evaluated_simulations": evaluated,
        "simulation_source": results_path.parent.name,
        "suggested_progress": _infer_progress(
            domain,
            len(simulations),
            n_tasks,
            len(tasks),
            evaluated,
        ),
    }


RUNS = [
    "2026-05-16-13-43-08_airline_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-16-15-12-02_airline_th_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-16-17-08-16_airline_tl_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-16-18-54-35_airline_vi_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-16-20-45-18_airline_zh_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-16-01-37-48_retail_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
    "2026-05-17-02-21-54_telecom_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8",
]

sim_base = Path("data/simulations")

for run in RUNS:
    results_path = sim_base / run / "results.json"
    if not results_path.exists():
        print(f"MISSING: {results_path}")
        continue
    m = compute_metrics(results_path)
    print(f"\n{'=' * 60}")
    print(f"Run: {run}")
    for k, v in m.items():
        print(f"  {k}: {v}")
