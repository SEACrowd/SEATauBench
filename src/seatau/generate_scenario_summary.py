"""Generate data/seatau/experiments.csv from data/simulations."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from seatau.constants import (
    EXPERIMENTS_CSV,
    L2_LANGUAGE_CODES,
    LANGUAGE_CODE_BY_DISPLAY_NAME,
    LANGUAGE_DISPLAY_NAME_BY_CODE,
    PROJECT_ROOT,
)
from seatau.experiment_matrix import (
    get_scenario_lang_components,
    list_all_scenarios,
    list_supported_domains,
)
from seatau.metrics.language_use import (
    compute_run_language_scores,
    infer_expected_language,
    load_fasttext_model,
)
from seatau.metrics.performance import DOMAIN_TOTALS, mean, pass_at_k, ratio, rho
from seatau.utils.normalize_models import NORMALIZED_MODEL_NAMES, normalize_model_name

SIMULATIONS_DIR = PROJECT_ROOT / "data" / "simulations"
SUPPORTED_SCENARIOS = set(list_all_scenarios())
SUPPORTED_DOMAINS = set(list_supported_domains())
TOOL_MIX_LANGUAGE_BY_TOKEN = {
    "mixed_bi": "tool_mix_2",
    "mixed_tri": "tool_mix_3",
    "mixed_fourth": "tool_mix_4",
    "mixed_multi": "tool_mix_5",
}
LANGUAGE_CODE_BY_LOWER_DISPLAY = {
    display_name.lower(): code
    for display_name, code in LANGUAGE_CODE_BY_DISPLAY_NAME.items()
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
    for code in L2_LANGUAGE_CODES:
        display_name = LANGUAGE_DISPLAY_NAME_BY_CODE[code]
        if display_name.lower() in tokens:
            return display_name
    return ""


def _display_name_for_lang_id(lang_id: str) -> str:
    lang_id = lang_id.lower()
    return LANGUAGE_DISPLAY_NAME_BY_CODE.get(lang_id, lang_id)


def _language(results_path: Path, info: dict[str, Any], scenario: str) -> str:
    name = results_path.parent.name.lower()
    if scenario == "english":
        return LANGUAGE_DISPLAY_NAME_BY_CODE["en"]
    if scenario == "l2_tools":
        for token, language in TOOL_MIX_LANGUAGE_BY_TOKEN.items():
            if token in name:
                return language
        for code, language in LANGUAGE_DISPLAY_NAME_BY_CODE.items():
            if f"_{code}_tools" in name:
                return language
        return ""
    if scenario == "l2_interaction":
        lang_id = info.get("lang_id") or (info.get("seatau_info") or {}).get(
            "run_language"
        )
        if lang_id:
            return _display_name_for_lang_id(str(lang_id))
        return _language_from_run_name(name)

    lang_id = info.get("lang_id") or (info.get("seatau_info") or {}).get("run_language")
    if lang_id:
        return _display_name_for_lang_id(str(lang_id))
    return _language_from_run_name(name)


def _lang_id(info: dict[str, Any], language: str) -> str:
    return str(
        info.get("lang_id")
        or ((info.get("seatau_info") or {}).get("run_language"))
        or LANGUAGE_CODE_BY_DISPLAY_NAME.get(language)
        or LANGUAGE_CODE_BY_LOWER_DISPLAY.get(language.lower())
        or language
    )


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
    if scenario not in SUPPORTED_SCENARIOS:
        return None
    domain = (info.get("environment_info") or {}).get("domain_name", "")
    language = _language(results_path, info, scenario)
    agent_llm = str((info.get("agent_info") or {}).get("llm") or "")
    normalized_agent_llm = normalize_model_name(agent_llm)

    if (
        domain not in SUPPORTED_DOMAINS
        or normalized_agent_llm not in NORMALIZED_MODEL_NAMES
    ):
        return None
    if not language or (scenario == "l2_tools" and language.lower() == "english"):
        return None

    task_rewards: dict[str, list[float]] = defaultdict(list)
    read_match = read_total = write_match = write_total = 0
    db_matches: list[float] = []

    for sim in data.get("simulations", []):
        reward_info = sim.get("reward_info") or {}
        reward = reward_info.get("reward")
        if reward is None:
            continue

        task_rewards[str(sim["task_id"])].append(float(reward))
        db_match = (reward_info.get("db_check") or {}).get("db_match")
        if db_match is not None:
            db_matches.append(float(db_match))

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
    pass_hat_1 = pass_at_k(rewards, 1)
    pass_hat_2 = pass_at_k(rewards, 2)
    pass_hat_3 = pass_at_k(rewards, 3)
    if pass_hat_1 is None or pass_hat_3 is None:
        return None

    lang_id = _lang_id(info, language)
    lang_components = get_scenario_lang_components(scenario)
    detector_model, _detector_error = load_fasttext_model()
    simulations = data.get("simulations", [])
    user_language_scores = compute_run_language_scores(
        simulations=simulations,
        role="user",
        expected_language=infer_expected_language(
            role="user",
            lang_id=lang_id,
            lang_components=lang_components,
            scenario=scenario,
        ),
        detector_model=detector_model,
    )
    agent_language_scores = compute_run_language_scores(
        simulations=simulations,
        role="assistant",
        expected_language=infer_expected_language(
            role="assistant",
            lang_id=lang_id,
            lang_components=lang_components,
            scenario=scenario,
        ),
        detector_model=detector_model,
    )

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
        "rho_hat_3": rho(pass_hat_1, pass_hat_3),
        "read_action": ratio(read_match, read_total),
        "write_action": ratio(write_match, write_total),
        "db_match": mean(db_matches),
        "user_language_correctness": mean(
            [score for score in user_language_scores if score is not None]
        ),
        "agent_language_correctness": mean(
            [score for score in agent_language_scores if score is not None]
        ),
        "total_simulations": len(simulations),
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
