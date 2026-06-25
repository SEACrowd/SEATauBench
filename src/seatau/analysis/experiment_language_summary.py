"""Regenerate `data/analyses/experiment_language_summary.csv` from `data/simulations/`.

For every row in `data/seatau/experiments.csv`, this recomputes user/agent
language correctness and drift directly from the run's `results.json`
trajectory with fastText, then joins the result with that run's pass-rate
metrics.

Usage:
  uv run python -m seatau.analysis.experiment_language_summary
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

from paths import (
    EXPERIMENT_LANGUAGE_SUMMARY_CSV,
    EXPERIMENTS_CSV,
    PROJECT_ROOT,
)
from seatau.analysis.language_drift import (
    infer_lang_id,
    is_likely_system_error,
    should_exclude_first_agent_turn,
)
from seatau.analysis.language_drift_summary import lang_proportion
from seatau.constants import (
    to_project_relative_path,
)
from seatau.experiment_matrix import get_scenario_lang_components
from seatau.metrics.language_use import (
    FastTextModel,
    batch_detect_fasttext,
    infer_expected_language,
    load_fasttext_model,
    normalize_lang_code,
    text_turns,
)

CSV_FIELDS = [
    "experiments_all_line",
    "scenario",
    "domain",
    "language_scenario",
    "lang_id",
    "expected_language",
    "agent_llm",
    "normalized_agent_llm",
    "results_json",
    "lang_components",
    "pass_hat_1",
    "pass_hat_2",
    "pass_hat_3",
    "rho_3",
    "user_language_correctness",
    "agent_language_correctness",
    "csv_user_language_correctness",
    "csv_agent_language_correctness",
    "user_turns_total",
    "agent_turns_total",
    "user_non_target_lang_proportion",
    "agent_non_target_lang_proportion",
    "user_drift_turn",
    "agent_drift_turn",
    "user_drift_trial_count",
    "agent_drift_trial_count",
    "user_detected_lang_proportion",
    "agent_detected_lang_proportion",
    "language_detector_warning",
]

EMPTY_ROLE_METRICS = {
    "turns_total": 0,
    "language_correctness": None,
    "non_target_lang_proportion": "",
    "detected_lang_proportion": "",
    "drift_turn": None,
    "drift_trial_count": 0,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=EXPERIMENTS_CSV)
    parser.add_argument("--output", type=Path, default=EXPERIMENT_LANGUAGE_SUMMARY_CSV)
    args = parser.parse_args()

    model, model_warning = load_fasttext_model()
    experiment_rows = read_experiment_rows(args.experiments_csv)
    print(f"Found {len(experiment_rows)} experiment rows.", flush=True)

    rows = []
    for idx, (line_number, csv_row) in enumerate(experiment_rows, start=1):
        if idx == 1 or idx % 10 == 0:
            print(f"processing {idx}/{len(experiment_rows)}", flush=True)
        rows.append(
            build_row(line_number, csv_row, model=model, model_warning=model_warning)
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Wrote {len(rows):,} rows to {to_project_relative_path(args.output).as_posix()}"
    )


def read_experiment_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    """Load `experiments.csv` rows that have an identified simulation source."""

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            (line_number, row)
            for line_number, row in enumerate(reader, start=2)
            if (row.get("simulation_source") or "").strip()
        ]


def build_row(
    line_number: int,
    csv_row: dict[str, str],
    *,
    model: FastTextModel | None,
    model_warning: str | None,
) -> dict[str, str]:
    """Build one `experiment_language_summary.csv` row for an experiment run."""

    scenario = csv_row["scenario"]
    domain = csv_row["domain"]
    language = csv_row["language_senario"]
    results_json = PROJECT_ROOT / csv_row["simulation_source"] / "results.json"

    row: dict[str, Any] = {
        "experiments_all_line": line_number,
        "scenario": scenario,
        "domain": domain,
        "language_scenario": language,
        "agent_llm": csv_row["agent_llm"],
        "normalized_agent_llm": csv_row["normalized_agent_llm"],
        "results_json": to_project_relative_path(results_json).as_posix(),
        "pass_hat_1": csv_row["pass_hat_1"],
        "pass_hat_2": csv_row["pass_hat_2"],
        "pass_hat_3": csv_row["pass_hat_3"],
        "rho_3": csv_row["rho_hat_3"],
        "csv_user_language_correctness": csv_row["user_language_correctness"],
        "csv_agent_language_correctness": csv_row["agent_language_correctness"],
    }

    if model is None:
        row["language_detector_warning"] = model_warning or ""
        return {field: _csv_value(row.get(field)) for field in CSV_FIELDS}

    data = json.loads(results_json.read_text(encoding="utf-8"))
    info = data.get("info") or {}
    lang_id = infer_lang_id(info, language)
    components = get_scenario_lang_components(scenario)
    user_expected = infer_expected_language(
        role="user", lang_id=lang_id, lang_components=components, scenario=scenario
    )
    agent_expected = infer_expected_language(
        role="assistant", lang_id=lang_id, lang_components=components, scenario=scenario
    )
    simulations = data.get("simulations") or []

    user_metrics = compute_role_metrics(
        simulations,
        message_role="user",
        expected_language=user_expected,
        model=model,
        scenario=scenario,
    )
    agent_metrics = compute_role_metrics(
        simulations,
        message_role="assistant",
        expected_language=agent_expected,
        model=model,
        scenario=scenario,
    )

    row.update(
        {
            "lang_id": lang_id,
            "expected_language": agent_expected,
            "lang_components": json.dumps(list(components)) if components else "",
            "user_language_correctness": user_metrics["language_correctness"],
            "agent_language_correctness": agent_metrics["language_correctness"],
            "user_turns_total": user_metrics["turns_total"],
            "agent_turns_total": agent_metrics["turns_total"],
            "user_non_target_lang_proportion": user_metrics[
                "non_target_lang_proportion"
            ],
            "agent_non_target_lang_proportion": agent_metrics[
                "non_target_lang_proportion"
            ],
            "user_drift_turn": user_metrics["drift_turn"],
            "agent_drift_turn": agent_metrics["drift_turn"],
            "user_drift_trial_count": user_metrics["drift_trial_count"],
            "agent_drift_trial_count": agent_metrics["drift_trial_count"],
            "user_detected_lang_proportion": user_metrics["detected_lang_proportion"],
            "agent_detected_lang_proportion": agent_metrics["detected_lang_proportion"],
            "language_detector_warning": "",
        }
    )
    return {field: _csv_value(row.get(field)) for field in CSV_FIELDS}


def compute_role_metrics(
    simulations: list[dict[str, Any]],
    *,
    message_role: str,
    expected_language: str,
    model: FastTextModel,
    scenario: str,
) -> dict[str, Any]:
    """Detect per-turn languages for one role across every trial in a run."""

    texts: list[str] = []
    owners: list[int] = []
    turn_indices: list[int] = []

    for sim_idx, sim in enumerate(simulations):
        if is_likely_system_error(sim):
            continue
        turns = text_turns(sim.get("messages") or [], message_role)
        for text_idx, (turn_idx, text) in enumerate(turns):
            if should_exclude_first_agent_turn(
                scenario=scenario,
                role=message_role,
                is_first_agent_text_turn=text_idx == 0,
            ):
                continue
            texts.append(text)
            owners.append(sim_idx)
            turn_indices.append(turn_idx)

    if not texts:
        return dict(EMPTY_ROLE_METRICS)

    labels = batch_detect_fasttext(model, texts)
    detected = [normalize_lang_code(label) if label else None for label in labels]

    turns_total = len(texts)
    target_turns = 0
    lang_counter: Counter[str] = Counter()
    non_target_counter: Counter[str] = Counter()
    first_drift_turn_by_sim: dict[int, int] = {}

    for sim_idx, turn_idx, lang in zip(owners, turn_indices, detected, strict=True):
        if lang is None:
            continue
        lang_counter[lang] += 1
        if lang == expected_language:
            target_turns += 1
        else:
            non_target_counter[lang] += 1
            first_drift_turn_by_sim[sim_idx] = min(
                turn_idx, first_drift_turn_by_sim.get(sim_idx, turn_idx)
            )

    detected_total = sum(lang_counter.values())
    drift_turn_values = list(first_drift_turn_by_sim.values())

    return {
        "turns_total": turns_total,
        "language_correctness": round(target_turns / turns_total, 6),
        "non_target_lang_proportion": lang_proportion(
            non_target_counter, detected_total
        ),
        "detected_lang_proportion": lang_proportion(lang_counter, detected_total),
        "drift_turn": round(float(median(drift_turn_values)), 6)
        if drift_turn_values
        else None,
        "drift_trial_count": len(first_drift_turn_by_sim),
    }


def _csv_value(value: object) -> str:
    return "" if value is None else str(value)


if __name__ == "__main__":
    main()
