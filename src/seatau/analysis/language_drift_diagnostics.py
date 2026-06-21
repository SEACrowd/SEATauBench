"""Build contextual diagnostics for SEA-Tau language drift.

This script keeps more conversational context so we can ask where drift
appears in tool-mix runs and by turn position.

Usage:
  uv run python -m seatau.analysis.language_drift_diagnostics
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from seatau.analysis.language_drift import (
    DEFAULT_EXPERIMENTS_CSV,
    LANGUAGE_LABELS,
    SCENARIO_LABELS,
    SCENARIO_ORDER,
    ExperimentRow,
    infer_expected_language,
    infer_lang_id,
    is_likely_system_error,
    read_experiment_rows,
    should_exclude_first_agent_turn,
)
from seatau.constants import (
    LANGUAGE_DRIFT_DIAGNOSTICS_DIR,
    LANGUAGE_DRIFT_RUN_SUMMARY_CSV,
    LANGUAGE_DRIFT_TOOL_MIX_SUMMARY_CSV,
    LANGUAGE_DRIFT_TURN_POSITION_CSV,
    to_project_relative_path,
)
from seatau.metrics.language_use import (
    batch_detect_fasttext,
    load_fasttext_model,
    normalize_lang_code,
)
from seatau.utils.normalize_models import short_model

DEFAULT_OUTPUT_DIR = LANGUAGE_DRIFT_DIAGNOSTICS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments-csv", type=Path, default=DEFAULT_EXPERIMENTS_CSV)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--include-system-errors",
        action="store_true",
        help="Include infrastructure/API/user-simulator failures.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    model, detector_warning = load_fasttext_model()
    if model is None:
        raise RuntimeError(
            f"fastText language detection unavailable: {detector_warning}"
        )

    experiments = [
        row
        for row in read_experiment_rows(args.experiments_csv)
        if row.scenario in set(SCENARIO_ORDER)
    ]
    print(
        f"Found {len(experiments)} L2 experiment rows with simulation_source.",
        flush=True,
    )

    all_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for idx, experiment in enumerate(experiments, start=1):
        if idx == 1 or idx % 10 == 0:
            print(
                f"detecting {idx}/{len(experiments)} "
                f"{SCENARIO_LABELS[experiment.scenario]}/"
                f"{experiment.domain}/{experiment.language}/"
                f"{short_model(experiment.agent_llm)}",
                flush=True,
            )
        try:
            all_rows.extend(
                detect_contextual_turns(
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

    turn_df = pd.DataFrame(all_rows)
    if turn_df.empty:
        raise RuntimeError("No contextual language rows were produced.")

    run_summary = build_run_summary(turn_df)
    turn_position = build_turn_position_summary(turn_df)
    tool_mix = build_tool_mix_summary(turn_df)

    run_path = args.output_dir / LANGUAGE_DRIFT_RUN_SUMMARY_CSV.name
    turn_position_path = args.output_dir / LANGUAGE_DRIFT_TURN_POSITION_CSV.name
    tool_mix_path = args.output_dir / LANGUAGE_DRIFT_TOOL_MIX_SUMMARY_CSV.name
    run_summary.to_csv(run_path, index=False)
    turn_position.to_csv(turn_position_path, index=False)
    tool_mix.to_csv(tool_mix_path, index=False)

    print(
        f"Wrote {len(run_summary):,} run rows to "
        f"{to_project_relative_path(run_path).as_posix()}"
    )
    print(
        f"Wrote {len(turn_position):,} turn-position rows to "
        f"{to_project_relative_path(turn_position_path).as_posix()}"
    )
    print(
        f"Wrote {len(tool_mix):,} tool-mix rows to "
        f"{to_project_relative_path(tool_mix_path).as_posix()}"
    )
    if warnings:
        print(
            f"Skipped {len(warnings):,} experiments due to warnings."
        )


def detect_contextual_turns(
    experiment: ExperimentRow,
    *,
    model: object,
    include_system_errors: bool,
) -> list[dict[str, Any]]:
    """Detect language for user and assistant turns, retaining local context."""

    results_json = experiment.simulation_source / "results.json"
    data = json.loads(results_json.read_text())
    info = data.get("info") or {}
    lang_id = infer_lang_id(info, experiment.language)
    expected_language = infer_expected_language(experiment.scenario, lang_id)

    rows: list[dict[str, Any]] = []
    texts: list[str] = []
    row_indices: list[int] = []

    for sim in data.get("simulations") or []:
        is_system_error = is_likely_system_error(sim)
        if is_system_error and not include_system_errors:
            continue
        first_agent_text_seen = False

        for message_idx, message in enumerate(sim.get("messages") or []):
            role = str(message.get("role") or "")
            content = str(message.get("content") or "").strip()
            had_tool_call = bool(message.get("tool_calls"))
            if role == "tool":
                continue
            if role not in {"user", "assistant"}:
                continue
            if len(content) < 5 or (
                content.startswith("###") and content.endswith("###")
            ):
                continue

            is_agent = role == "assistant"
            is_first_agent_text_turn = is_agent and not first_agent_text_seen

            row = {
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
                "message_idx": message_idx,
                "turn_idx": int(message.get("turn_idx") or message_idx),
                "role": "agent" if is_agent else "user",
                "has_tool_call": had_tool_call,
                "termination_reason": sim.get("termination_reason", ""),
                "is_system_error": is_system_error,
                "is_first_agent_text_turn": is_first_agent_text_turn,
                "counted_for_language_correctness": not should_exclude_first_agent_turn(
                    scenario=experiment.scenario,
                    role="agent" if is_agent else "user",
                    is_first_agent_text_turn=is_first_agent_text_turn,
                ),
            }
            rows.append(row)
            texts.append(content)
            row_indices.append(len(rows) - 1)

            if is_agent:
                first_agent_text_seen = True

    labels = batch_detect_fasttext(model, texts)
    for row_idx, label in zip(row_indices, labels, strict=True):
        detected = normalize_lang_code(label) if label else ""
        row = rows[row_idx]
        row["detected_language"] = detected
        row["language_bucket"] = language_bucket(detected, row["expected_language"])
        row["is_target_language"] = detected == row["expected_language"]
        row["is_english"] = detected == "en"
        row["is_non_target_language"] = (
            bool(detected) and detected != row["expected_language"]
        )
    return rows


def build_run_summary(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-run correctness for user and agent roles."""

    group_cols = [
        "experiments_all_line",
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
        "results_json",
        "role",
    ]
    rows: list[dict[str, Any]] = []
    for key, group in turn_df.groupby(group_cols, dropna=False, sort=True):
        base = dict(zip(group_cols, key, strict=True))
        detected = group.loc[group["detected_language"].astype(str).ne("")]
        counts = Counter(detected["detected_language"].astype(str))
        total = len(group)
        target_count = int(group["is_target_language"].sum())
        non_target_count = int(group["is_non_target_language"].sum())
        english_count = int(group["is_english"].sum())
        rows.append(
            {
                **base,
                "turn_count": int(total),
                "target_turn_count": target_count,
                "non_target_turn_count": non_target_count,
                "english_turn_count": english_count,
                "language_correctness": safe_rate(target_count, total),
                "non_target_share": safe_rate(non_target_count, total),
                "english_share": safe_rate(english_count, total),
                "detected_lang_proportion": lang_proportion(counts, len(detected)),
                "detected_lang_proportion_json": json.dumps(
                    proportions_dict(counts, len(detected)),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )
    return pd.DataFrame(rows)


def build_turn_position_summary(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate non-target rate by turn position and role."""

    frame = turn_df.loc[turn_df["counted_for_language_correctness"]].copy()
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(
        ["scenario", "scenario_label", "role", "turn_idx"], dropna=False, sort=True
    ):
        base = dict(zip(["scenario", "scenario_label", "role", "turn_idx"], key, strict=True))
        total = len(group)
        rows.append(
            {
                **base,
                "turn_count": int(total),
                "non_target_turn_count": int(group["is_non_target_language"].sum()),
                "non_target_share": safe_rate(
                    group["is_non_target_language"].sum(), total
                ),
            }
        )
    return pd.DataFrame(rows)


def build_tool_mix_summary(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detected languages for L2 Tools tool-mix agent turns."""

    frame = turn_df.loc[
        turn_df["role"].eq("agent")
        & turn_df["counted_for_language_correctness"]
        & turn_df["scenario"].eq("l2_tools")
        & turn_df["language"].astype(str).str.startswith("tool_mix")
    ].copy()
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(
        ["scenario", "scenario_label", "domain", "language", "language_label", "detected_language"],
        dropna=False,
        sort=True,
    ):
        base = dict(
            zip(
                [
                    "scenario",
                    "scenario_label",
                    "domain",
                    "language",
                    "language_label",
                    "detected_language",
                ],
                key,
                strict=True,
            )
        )
        rows.append(
            {
                **base,
                "turn_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def language_bucket(detected: str, expected_language: str) -> str:
    """Bucket detected language into target, English, or other."""

    if detected == expected_language:
        return "target"
    if detected == "en":
        return "english"
    return "other"


def looks_like_structured_payload(text: str) -> bool:
    """Heuristic for assistant turns that are JSON/tool payload echoes."""

    stripped = text.strip()
    if stripped.startswith(("{", "[")):
        return True
    return stripped.count('":') >= 2 or stripped.count('": "') >= 2


def proportions_dict(counter: Counter[str], denominator: int) -> dict[str, float]:
    """Language proportions sorted by frequency."""

    if denominator <= 0:
        return {}
    return {
        lang: round(count / denominator, 6)
        for lang, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if lang
    }


def lang_proportion(counter: Counter[str], denominator: int) -> str:
    """Format language proportions like `en_0.516|ko_0.011`."""

    return "|".join(
        f"{lang}_{share:.3f}"
        for lang, share in proportions_dict(counter, denominator).items()
    )


def safe_rate(numerator: Any, denominator: Any) -> float:
    """Return a rounded rate, using zero for empty denominators."""

    denom = int(denominator)
    return round(float(numerator) / denom, 6) if denom else 0.0


if __name__ == "__main__":
    main()
