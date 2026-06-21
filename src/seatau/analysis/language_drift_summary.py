"""Recompute agent language drift from raw SEA-Tau trajectories.

This script intentionally starts from `data/seatau/experiments.csv` and the
referenced `results.json` files instead of trusting previous aggregate CSVs.

Outputs:
  data/analyses/language_drift_summary/agent_language_drift_by_task.csv

Usage:
  uv run python -m seatau.analysis.language_drift_summary
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from seatau.analysis.language_drift import (
    DEFAULT_EXPERIMENTS_CSV,
    LANGUAGE_LABELS,
    SCENARIO_LABELS,
    ExperimentRow,
    infer_expected_language,
    infer_lang_id,
    is_likely_system_error,
    read_experiment_rows,
    should_exclude_first_agent_turn,
    text_turns,
)
from seatau.constants import LANGUAGE_DRIFT_SUMMARY_DIR, to_project_relative_path
from seatau.metrics.language_use import (
    batch_detect_fasttext,
    load_fasttext_model,
    normalize_lang_code,
)
from seatau.utils.normalize_models import short_model
from seatau.utils.text import squash

DEFAULT_OUTPUT_DIR = LANGUAGE_DRIFT_SUMMARY_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=DEFAULT_EXPERIMENTS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--include-system-errors",
        action="store_true",
        help="Include infrastructure/API/user-simulator failures in drift summaries.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    model, detector_warning = load_fasttext_model()
    if model is None:
        raise RuntimeError(
            f"fastText language detection is unavailable: {detector_warning}"
        )

    experiments = read_experiment_rows(args.experiments_csv)
    print(
        f"Found {len(experiments)} experiment rows with simulation_source.", flush=True
    )

    all_turn_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for idx, experiment in enumerate(experiments, start=1):
        if idx == 1 or idx % 10 == 0:
            print(
                f"detecting {idx}/{len(experiments)} "
                f"{experiment.scenario}/{experiment.domain}/"
                f"{experiment.language}/{short_model(experiment.agent_llm)}",
                flush=True,
            )
        try:
            all_turn_rows.extend(
                detect_experiment_turns(
                    experiment,
                    model=model,
                    include_system_errors=args.include_system_errors,
                )
            )
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
            warnings.append(
                {
                    "experiments_all_line": experiment.line_number,
                    "simulation_source": to_project_relative_path(
                        experiment.simulation_source
                    ).as_posix(),
                    "error": str(exc),
                }
            )

    turn_df = pd.DataFrame(all_turn_rows)
    if turn_df.empty:
        raise RuntimeError("No agent text turns were detected.")

    task_df = build_task_summary(turn_df)
    task_path = args.output_dir / "agent_language_drift_by_task.csv"
    task_df.to_csv(task_path, index=False)

    print(
        f"Wrote {len(task_df):,} task rows to "
        f"{to_project_relative_path(task_path).as_posix()}"
    )
    if warnings:
        print(f"Skipped {len(warnings):,} experiments due to warnings.")


def detect_experiment_turns(
    experiment: ExperimentRow,
    *,
    model: object,
    include_system_errors: bool,
) -> list[dict[str, Any]]:
    """Detect fastText language labels for every assistant text turn."""

    results_json = experiment.simulation_source / "results.json"
    data = json.loads(results_json.read_text())
    info = data.get("info") or {}
    lang_id = infer_lang_id(info, experiment.language)
    expected_language = infer_expected_language(experiment.scenario, lang_id)

    rows: list[dict[str, Any]] = []
    texts: list[str] = []
    row_indices: list[int] = []
    simulations = data.get("simulations") or []
    for sim in simulations:
        is_system_error = is_likely_system_error(sim)
        if is_system_error and not include_system_errors:
            continue
        for agent_text_idx, (turn_idx, text) in enumerate(
            text_turns(sim.get("messages") or [], "assistant")
        ):
            if should_exclude_first_agent_turn(
                scenario=experiment.scenario,
                role="assistant",
                is_first_agent_text_turn=agent_text_idx == 0,
            ):
                continue
            rows.append(
                {
                    "experiments_all_line": experiment.line_number,
                    "scenario": experiment.scenario,
                    "scenario_label": SCENARIO_LABELS.get(
                        experiment.scenario, experiment.scenario
                    ),
                    "domain": experiment.domain,
                    "language": experiment.language,
                    "language_label": LANGUAGE_LABELS.get(
                        experiment.language, experiment.language
                    ),
                    "lang_id": lang_id,
                    "expected_language": expected_language,
                    "agent_llm": experiment.agent_llm,
                    "agent_family": short_model(experiment.agent_llm),
                    "normalized_agent_llm": experiment.normalized_agent_llm,
                    "simulation_source": to_project_relative_path(
                        experiment.simulation_source
                    ).as_posix(),
                    "results_json": to_project_relative_path(results_json).as_posix(),
                    "task_id": sim.get("task_id"),
                    "trial": sim.get("trial"),
                    "turn_idx": turn_idx,
                    "termination_reason": sim.get("termination_reason", ""),
                    "is_system_error": is_system_error,
                    "text_snippet": squash(text, 500),
                }
            )
            texts.append(text)
            row_indices.append(len(rows) - 1)

    labels = batch_detect_fasttext(model, texts)
    for row_idx, label in zip(row_indices, labels, strict=True):
        detected = normalize_lang_code(label) if label else ""
        rows[row_idx]["detected_language"] = detected
        rows[row_idx]["is_target_language"] = detected == expected_language
        rows[row_idx]["is_english"] = detected == "en"
        rows[row_idx]["is_non_target_language"] = (
            bool(detected) and detected != expected_language
        )
    return rows


def build_task_summary(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate turn detections to one row per task/trial group."""

    group_cols = [
        "scenario",
        "scenario_label",
        "domain",
        "language",
        "language_label",
        "lang_id",
        "expected_language",
        "agent_llm",
        "agent_family",
        "normalized_agent_llm",
        "simulation_source",
        "task_id",
    ]
    rows: list[dict[str, Any]] = []
    for key, group in turn_df.groupby(group_cols, dropna=False, sort=True):
        base = dict(zip(group_cols, key, strict=True))
        detected = group.loc[group["detected_language"].astype(str).ne("")]
        langs = Counter(detected["detected_language"].astype(str))
        drift_turns = group.loc[group["is_non_target_language"], "turn_idx"].tolist()
        rows.append(
            {
                **base,
                "turns_total": int(len(group)),
                "trials_observed": int(group["trial"].nunique()),
                "english_turns": int(group["is_english"].sum()),
                "non_target_turns": int(group["is_non_target_language"].sum()),
                "target_turns": int(group["is_target_language"].sum()),
                "english_turn_share": safe_rate(group["is_english"].sum(), len(group)),
                "non_target_turn_share": safe_rate(
                    group["is_non_target_language"].sum(), len(group)
                ),
                "target_turn_share": safe_rate(
                    group["is_target_language"].sum(), len(group)
                ),
                "first_non_target_turn": min(drift_turns) if drift_turns else "",
                "detected_lang_proportion": lang_proportion(langs, len(detected)),
                "detected_lang_proportion_json": json.dumps(
                    proportions_dict(langs, len(detected)),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )
    return pd.DataFrame(rows)


def proportions_dict(counter: Counter[str], denominator: int) -> dict[str, float]:
    """Return language proportions sorted by descending frequency."""

    if denominator <= 0:
        return {}
    return {
        lang: round(count / denominator, 6)
        for lang, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if lang
    }


def lang_proportion(counter: Counter[str], denominator: int) -> str:
    """Format language proportions like `en_0.516|de_0.004`."""

    return "|".join(
        f"{lang}_{proportion:.3f}"
        for lang, proportion in proportions_dict(counter, denominator).items()
    )


def median_or_blank(values: list[Any]) -> float | str:
    """Median for numeric values, blank when there are none."""

    numeric_values = [float(value) for value in values if value not in ("", None)]
    return round(float(median(numeric_values)), 6) if numeric_values else ""


def safe_rate(numerator: Any, denominator: Any) -> float | str:
    """Return a rounded rate, or blank for zero denominator."""

    denom = int(denominator)
    return round(float(numerator) / denom, 6) if denom else ""


if __name__ == "__main__":
    main()
