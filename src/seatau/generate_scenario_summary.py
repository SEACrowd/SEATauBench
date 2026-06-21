"""Generate data/seatau/experiments.csv from data/simulations."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from math import comb
from pathlib import Path
from typing import Any

from seatau.paths import EXPERIMENTS_CSV, PROJECT_ROOT
from seatau.utils.normalize_models import NORMALIZED_MODEL_NAMES, normalize_model_name

SIMULATIONS_DIR = PROJECT_ROOT / "data" / "simulations"

DOMAINS = ("airline", "retail", "telecom")
DOMAIN_TOTALS = {"airline": 150, "retail": 342, "telecom": 342}
LANGUAGE_BY_CODE = {
    "zh": "chinese",
    "id": "indonesian",
    "th": "thai",
    "vi": "vietnamese",
    "tl": "filipino",
}
LANGUAGE_NAMES = tuple(LANGUAGE_BY_CODE.values())
SCENARIOS = ("english", "l2_tools", "l2_interaction", "l2_domain")
TOOL_MIX_BY_TOKEN = {
    "mixed_bi": "tool_mix_2",
    "mixed_tri": "tool_mix_3",
    "mixed_fourth": "tool_mix_4",
    "mixed_multi": "tool_mix_5",
}
CSV_FIELDS = [
    "scenario",
    "domain",
    "language_senario",
    "agent_llm",
    "normalized_agent_llm",
    "simulation_source",
    "pass_hat_1",
    "pass_hat_2",
    "pass_hat_3",
    "rho_hat_3",
    "read_action",
    "write_action",
    "db_match",
    "user_language_correctness",
    "agent_language_correctness",
    "total_simulations",
    "total_tasks",
]


def _pass_at_k(task_rewards: list[list[float]], k: int) -> float | None:
    values: list[float] = []
    for rewards in task_rewards:
        n = len(rewards)
        if n < k:
            continue
        correct = sum(reward == 1.0 for reward in rewards)
        values.append(comb(correct, k) / comb(n, k))
    return round(sum(values) / len(values), 3) if values else None


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def _rho(pass_hat_1: float | None, pass_hat_3: float | None) -> float | None:
    if not pass_hat_1 or pass_hat_3 is None:
        return None
    return round(pass_hat_3 / pass_hat_1, 3)


def _csv_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return str(round(value, 3))
    return str(value)


def _relative_source(results_path: Path) -> str:
    return results_path.parent.relative_to(PROJECT_ROOT).as_posix()


def _scenario(results_path: Path) -> str:
    return results_path.relative_to(SIMULATIONS_DIR).parts[0]


def _language_from_run_name(name: str) -> str:
    tokens = set(name.lower().split("_"))
    for language in LANGUAGE_NAMES:
        if language in tokens:
            return language
    return ""


def _language(results_path: Path, info: dict[str, Any], scenario: str) -> str:
    name = results_path.parent.name.lower()
    if scenario == "english":
        return "english"
    if scenario == "l2_tools":
        for token, language in TOOL_MIX_BY_TOKEN.items():
            if token in name:
                return language
        for code, language in LANGUAGE_BY_CODE.items():
            if f"_{code}_tools" in name:
                return language
        return ""
    if scenario == "l2_interaction":
        lang_id = info.get("lang_id") or (info.get("seatau_info") or {}).get(
            "run_language"
        )
        if lang_id:
            return LANGUAGE_BY_CODE.get(str(lang_id).lower(), str(lang_id).lower())
        return _language_from_run_name(name)

    lang_id = info.get("lang_id") or (info.get("seatau_info") or {}).get("run_language")
    if lang_id:
        return LANGUAGE_BY_CODE.get(str(lang_id).lower(), str(lang_id).lower())
    return _language_from_run_name(name)


def _row_quality(row: dict[str, str]) -> tuple[int, int, int, str]:
    expected_total = DOMAIN_TOTALS[row["domain"]]
    total_simulations = int(row["total_simulations"] or 0)
    total_tasks = int(row["total_tasks"] or 0)
    return (
        int(total_simulations >= expected_total),
        total_tasks,
        total_simulations,
        row["simulation_source"],
    )


def _read_row(results_path: Path) -> dict[str, str] | None:
    with results_path.open(encoding="utf-8") as f:
        data = json.load(f)

    info = data.get("info") or {}
    scenario = _scenario(results_path)
    if scenario not in SCENARIOS:
        return None
    domain = (info.get("environment_info") or {}).get("domain_name", "")
    language = _language(results_path, info, scenario)
    agent_llm = str((info.get("agent_info") or {}).get("llm") or "")
    normalized_agent_llm = normalize_model_name(agent_llm)

    if domain not in DOMAINS or normalized_agent_llm not in NORMALIZED_MODEL_NAMES:
        return None
    if not language or (scenario == "l2_tools" and language == "english"):
        return None

    task_rewards: dict[str, list[float]] = defaultdict(list)
    read_match = read_total = write_match = write_total = 0
    db_matches: list[float] = []
    language_scores: list[float] = []

    for sim in data.get("simulations", []):
        reward_info = sim.get("reward_info") or {}
        reward = reward_info.get("reward")
        if reward is None:
            continue

        task_rewards[str(sim["task_id"])].append(float(reward))
        db_match = (reward_info.get("db_check") or {}).get("db_match")
        if db_match is not None:
            db_matches.append(float(db_match))

        language_info = (reward_info.get("info") or {}).get("language_correctness")
        if language_info and language_info.get("score") is not None:
            language_scores.append(float(language_info["score"]))

        for action_check in reward_info.get("action_checks") or []:
            action_match = int(action_check.get("action_match", False))
            match action_check.get("tool_type"):
                case "read":
                    read_match += action_match
                    read_total += 1
                case "write":
                    write_match += action_match
                    write_total += 1

    rewards = list(task_rewards.values())
    pass_hat_1 = _pass_at_k(rewards, 1)
    pass_hat_2 = _pass_at_k(rewards, 2)
    pass_hat_3 = _pass_at_k(rewards, 3)
    if pass_hat_1 is None or pass_hat_3 is None:
        return None

    row = {
        "scenario": scenario,
        "domain": domain,
        "language_senario": language,
        "agent_llm": agent_llm,
        "normalized_agent_llm": normalized_agent_llm,
        "simulation_source": _relative_source(results_path),
        "pass_hat_1": pass_hat_1,
        "pass_hat_2": pass_hat_2,
        "pass_hat_3": pass_hat_3,
        "rho_hat_3": _rho(pass_hat_1, pass_hat_3),
        "read_action": _ratio(read_match, read_total),
        "write_action": _ratio(write_match, write_total),
        "db_match": _mean(db_matches),
        "user_language_correctness": "",
        "agent_language_correctness": _mean(language_scores),
        "total_simulations": len(data.get("simulations", [])),
        "total_tasks": len(rewards),
    }
    return {field: _csv_value(row[field]) for field in CSV_FIELDS}


def build_rows(simulations_dir: Path = SIMULATIONS_DIR) -> list[dict[str, str]]:
    rows: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for results_path in sorted(simulations_dir.glob("**/results.json")):
        row = _read_row(results_path)
        if row is None:
            continue
        key = (
            row["scenario"],
            row["domain"],
            row["language_senario"],
            row["normalized_agent_llm"],
        )
        if key not in rows or _row_quality(row) > _row_quality(rows[key]):
            rows[key] = row

    return sorted(
        rows.values(),
        key=lambda row: (
            row["scenario"],
            row["domain"],
            row["language_senario"],
            row["normalized_agent_llm"],
        ),
    )


def write_experiments_csv(
    output_path: Path = EXPERIMENTS_CSV,
    simulations_dir: Path = SIMULATIONS_DIR,
) -> Path:
    rows = build_rows(simulations_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


if __name__ == "__main__":
    path = write_experiments_csv()
    print(f"Wrote {path}")
