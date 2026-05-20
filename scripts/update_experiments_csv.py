"""Update a single row in experiments.csv from a results.json file."""

from __future__ import annotations

import argparse
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

_TELECOM_BLANK_READ_METRICS = {
    "read_action_count",
    "read_acount_total",
    "read_action_percent",
}

_NEEDS_CHECK_NOTE_RE = (
    "infra failure",
    "infra failures",
    "connection failure",
    "connection failures",
    "failed to open tunnel",
    "connection info is not ready",
    "key refresh",
)
_ACCEPTABLE_NOTE_RE = (
    "acceptable",
    "clean run",
    "cleanly rerun",
    "completed",
    "finished",
    "all 114 tasks",
    "all tasks",
    "full 114 tasks",
)


def _pass_at_k(task_rewards_list: list[list[float]], k: int) -> float | None:
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


def infer_progress(metrics: dict[str, object]) -> str:
    """Infer row progress from the actual run metrics."""
    domain = str(metrics["domain"])
    total_simulations = int(metrics["total_simulations"])
    total_tasks = int(metrics["total_tasks"])
    base_task_count = int(metrics["_base_task_count"])
    evaluated_simulations = int(
        metrics.get("_evaluated_simulations", total_simulations)
    )

    if total_simulations < _expected_total_simulations(domain):
        return "IN_PROGRESS"
    if total_tasks < base_task_count:
        return "PARTIAL"
    if evaluated_simulations < total_simulations:
        return "NEEDS_CHECK"
    return "DONE"


def _note_requires_check(note: str) -> bool:
    """Return True when progress notes describe a compromised run."""
    normalized = note.casefold()
    if any(token in normalized for token in _ACCEPTABLE_NOTE_RE):
        return False
    return any(token in normalized for token in _NEEDS_CHECK_NOTE_RE)


def compute_metrics(results_path: Path) -> dict[str, object]:
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

    def fmt_pct(v: float | None) -> float | None:
        return round(v * 100, 1) if v is not None else None

    lang_id = info.get("lang_id", "")
    domain = (info.get("environment_info") or {}).get("domain_name", "")
    agent_llm = canonical_model_name((info.get("agent_info") or {}).get("llm", ""))
    experiment = (info.get("seatau_info") or {}).get("experiment_name", "")

    return {
        "experiment": experiment,
        "domain": domain,
        "language_or_scenario": lang_id,
        "agent_llm": agent_llm,
        "pass_hat_1": fmt_pct(_pass_at_k(list(task_rewards.values()), 1)),
        "pass_hat_2": fmt_pct(_pass_at_k(list(task_rewards.values()), 2)),
        "pass_hat_3": fmt_pct(_pass_at_k(list(task_rewards.values()), 3)),
        "read_action_count": read_match,
        "read_acount_total": read_total,
        "read_action_percent": fmt_pct(read_match / read_total if read_total else None),
        "write_action_count": write_match,
        "write_acount_total": write_total,
        "write_action_percent": fmt_pct(
            write_match / write_total if write_total else None
        ),
        "db_match": fmt_pct(sum(db_matches) / len(db_matches) if db_matches else None),
        "language_correctness": fmt_pct(
            sum(lang_scores) / len(lang_scores) if lang_scores else None
        ),
        "total_simulations": len(simulations),
        "total_tasks": len(task_rewards),
        "_base_task_count": len(tasks),
        "_evaluated_simulations": evaluated,
        "simulation_source": results_path.parent.name,
    }


def update_csv(
    results_path: Path,
    csv_path: Path,
    progress: str = "DONE",
    agent_llm_override: str | None = None,
) -> None:
    metrics = compute_metrics(results_path)
    if agent_llm_override:
        metrics = dict(metrics)
        metrics["agent_llm"] = agent_llm_override
    if progress == "DONE":
        progress = infer_progress(metrics)
    domain = str(metrics["domain"])
    rows: list[dict[str, str]]
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    updated = False
    for row in rows:
        if (
            row["experiment"] == metrics["experiment"]
            and row["domain"] == metrics["domain"]
            and row["language_or_scenario"] == metrics["language_or_scenario"]
            and row["agent_llm"] == metrics["agent_llm"]
        ):
            if progress == "DONE":
                progress = infer_progress(metrics)
                if progress == "DONE" and _note_requires_check(
                    row.get("progress_notes", "")
                ):
                    progress = "NEEDS_CHECK"
            row["progress"] = progress
            row["simulation_source"] = str(metrics["simulation_source"])
            for key in (
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
            ):
                value = metrics[key]
                if domain == "telecom" and key in _TELECOM_BLANK_READ_METRICS:
                    row[key] = ""
                    continue
                row[key] = "" if value is None else str(value)
            updated = True
            break

    if not updated:
        raise ValueError(
            "matching row not found for "
            f"{metrics['experiment']} / {metrics['domain']} / "
            f"{metrics['language_or_scenario']} / {metrics['agent_llm']}"
        )

    fieldnames = [name for name in rows[0].keys() if name is not None]
    for row in rows:
        row.pop(None, None)

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_json", type=Path)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("experiments/experiments.csv"),
        help="Path to experiments.csv",
    )
    parser.add_argument(
        "--progress",
        default="DONE",
        help="Progress value to write into the matched row",
    )
    parser.add_argument(
        "--agent-llm-override",
        default=None,
        help="Override the agent_llm used for CSV row lookup (e.g. when the run used a "
        "different provider for the same model than what is tracked in the CSV).",
    )
    args = parser.parse_args()
    update_csv(
        args.results_json,
        args.csv,
        progress=args.progress,
        agent_llm_override=args.agent_llm_override,
    )


if __name__ == "__main__":
    main()
