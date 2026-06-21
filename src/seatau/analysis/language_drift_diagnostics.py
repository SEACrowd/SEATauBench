"""Build contextual diagnostics for SEA-Tau language drift.

This script keeps more conversational context so we can ask where drift
appears: after tool calls, in tool-mix runs, by turn position, and whether
user/agent drift appears to follow the other speaker.

Usage:
  uv run python -m seatau.analysis.language_drift_diagnostics
"""

from __future__ import annotations

import argparse
import csv
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
from seatau.constants import LANGUAGE_DRIFT_DIAGNOSTICS_DIR, to_project_relative_path
from seatau.metrics.language_use import (
    batch_detect_fasttext,
    load_fasttext_model,
    normalize_lang_code,
)
from seatau.utils.normalize_models import short_model
from seatau.utils.text import squash

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

    summary = build_context_summary(turn_df)
    evidence = build_drift_evidence(turn_df)

    turn_path = args.output_dir / "contextual_turn_language.csv"
    summary_path = args.output_dir / "contextual_language_summary.csv"
    evidence_path = args.output_dir / "drift_cause_evidence.csv"
    warnings_path = args.output_dir / "contextual_language_warnings.csv"
    turn_df.to_csv(turn_path, index=False)
    summary.to_csv(summary_path, index=False)
    evidence.to_csv(evidence_path, index=False)
    write_dict_csv(warnings_path, warnings)

    print(
        f"Wrote {len(turn_df):,} contextual turn rows to "
        f"{to_project_relative_path(turn_path).as_posix()}"
    )
    print(
        f"Wrote {len(summary):,} summary rows to "
        f"{to_project_relative_path(summary_path).as_posix()}"
    )
    print(
        f"Wrote {len(evidence):,} evidence rows to "
        f"{to_project_relative_path(evidence_path).as_posix()}"
    )
    if warnings:
        print(
            f"Wrote {len(warnings):,} warnings to "
            f"{to_project_relative_path(warnings_path).as_posix()}"
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
        sim_rows: list[dict[str, Any]] = []
        previous_role = ""
        previous_text_role = ""
        previous_agent_had_tool_call = False
        first_agent_text_seen = False
        tool_since_last_text = False

        for message_idx, message in enumerate(sim.get("messages") or []):
            role = str(message.get("role") or "")
            content = str(message.get("content") or "").strip()
            had_tool_call = bool(message.get("tool_calls"))
            if role == "tool":
                tool_since_last_text = True
                previous_role = "tool"
                continue
            if role not in {"user", "assistant"}:
                previous_role = role
                continue
            if len(content) < 5 or (
                content.startswith("###") and content.endswith("###")
            ):
                previous_role = role
                previous_agent_had_tool_call = role == "assistant" and had_tool_call
                continue

            is_agent = role == "assistant"
            is_first_agent_text_turn = is_agent and not first_agent_text_seen
            excluded_from_agent_language_correctness = should_exclude_first_agent_turn(
                scenario=experiment.scenario,
                role="agent" if is_agent else "user",
                is_first_agent_text_turn=is_first_agent_text_turn,
            )

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
                "previous_role": previous_role,
                "previous_text_role": previous_text_role,
                "after_tool_result": role == "assistant" and tool_since_last_text,
                "after_agent_tool_call": role == "assistant"
                and previous_agent_had_tool_call,
                "has_tool_call": had_tool_call,
                "termination_reason": sim.get("termination_reason", ""),
                "is_system_error": is_system_error,
                "is_first_agent_text_turn": is_first_agent_text_turn,
                "excluded_from_agent_language_correctness": excluded_from_agent_language_correctness,
                "counted_for_language_correctness": not excluded_from_agent_language_correctness,
                "text_snippet": squash(content, 500),
            }
            rows.append(row)
            sim_rows.append(row)
            texts.append(content)
            row_indices.append(len(rows) - 1)

            previous_role = role
            previous_text_role = "agent" if role == "assistant" else "user"
            previous_agent_had_tool_call = role == "assistant" and had_tool_call
            if is_agent:
                first_agent_text_seen = True
            tool_since_last_text = False

        # The row ids are implicit in list position and filled after detection.
        for row in sim_rows:
            row["simulation_turns_kept"] = len(sim_rows)

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

    add_previous_speaker_context(rows)
    for row in rows:
        row["drift_cause"] = classify_drift_cause(row)
    return rows


def add_previous_speaker_context(rows: list[dict[str, Any]]) -> None:
    """Add previous same/opposite speaker language context within each simulation."""

    by_sim: dict[tuple[str, Any, Any], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["simulation_source"]), row["task_id"], row["trial"])
        by_sim.setdefault(key, []).append(row)
    for sim_rows in by_sim.values():
        sim_rows.sort(key=lambda row: (int(row["message_idx"]), int(row["turn_idx"])))
        previous_by_role: dict[str, dict[str, Any] | None] = {
            "user": None,
            "agent": None,
        }
        for row in sim_rows:
            role = str(row["role"])
            other_role = "user" if role == "agent" else "agent"
            prev_same = previous_by_role.get(role)
            prev_other = previous_by_role.get(other_role)
            row["previous_same_role_detected_language"] = (
                prev_same.get("detected_language", "") if prev_same else ""
            )
            row["previous_other_role_detected_language"] = (
                prev_other.get("detected_language", "") if prev_other else ""
            )
            row["previous_same_role_non_target"] = bool(
                prev_same and prev_same.get("is_non_target_language")
            )
            row["previous_other_role_non_target"] = bool(
                prev_other and prev_other.get("is_non_target_language")
            )
            previous_by_role[role] = row


def classify_drift_cause(row: dict[str, Any]) -> str:
    """Assign an interpretable heuristic label for non-target language turns."""

    if not row.get("is_non_target_language"):
        return "target_or_expected_language"
    text = str(row.get("text_snippet") or "").lower()
    if "transfer" in text or "human agent" in text or "please hold" in text:
        return "transfer_or_system_template"
    if row["role"] == "agent":
        if looks_like_structured_payload(text):
            return "structured_tool_echo"
        if row.get("after_tool_result"):
            return "post_tool_response"
        if row.get("previous_other_role_non_target"):
            return "follows_user_drift"
        if int(row.get("turn_idx") or 0) <= 2:
            return "early_turn"
        return "other_or_detector_noise"
    if row.get("previous_other_role_non_target"):
        return "follows_agent_drift"
    if row.get("previous_same_role_non_target"):
        return "continued_user_drift"
    if int(row.get("turn_idx") or 0) <= 3:
        return "early_turn"
    return "other_or_detector_noise"


def build_context_summary(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detected language proportions over useful context groups."""

    group_cols = [
        "scenario",
        "scenario_label",
        "domain",
        "language",
        "language_label",
        "expected_language",
        "role",
        "after_tool_result",
        "drift_cause",
    ]
    rows: list[dict[str, Any]] = []
    for key, group in turn_df.groupby(group_cols, dropna=False, sort=True):
        base = dict(zip(group_cols, key, strict=True))
        counted = group.loc[group["counted_for_language_correctness"]]
        detected = counted.loc[counted["detected_language"].astype(str).ne("")]
        counts = Counter(detected["detected_language"].astype(str))
        rows.append(
            {
                **base,
                "turn_count": int(len(group)),
                "counted_turn_count": int(len(counted)),
                "task_count": int(group["task_id"].nunique()),
                "raw_non_target_share": safe_rate(
                    group["is_non_target_language"].sum(), len(group)
                ),
                "non_target_share": safe_rate(
                    counted["is_non_target_language"].sum(), len(counted)
                ),
                "english_share": safe_rate(counted["is_english"].sum(), len(counted)),
                "target_share": safe_rate(
                    counted["is_target_language"].sum(), len(counted)
                ),
                "detected_lang_proportion": lang_proportion(counts, len(detected)),
                "detected_lang_proportion_json": json.dumps(
                    proportions_dict(counts, len(detected)),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )
    return pd.DataFrame(rows)


def build_drift_evidence(turn_df: pd.DataFrame) -> pd.DataFrame:
    """Small auditable table of high-signal non-target examples."""

    drift = turn_df.loc[turn_df["is_non_target_language"]].copy()
    if drift.empty:
        return drift
    drift["priority"] = drift["drift_cause"].map(
        {
            "post_tool_response": 0,
            "structured_tool_echo": 0,
            "follows_user_drift": 1,
            "follows_agent_drift": 1,
            "continued_user_drift": 2,
            "early_turn": 3,
            "transfer_or_system_template": 4,
            "other_or_detector_noise": 5,
        }
    )
    fields = [
        "scenario_label",
        "domain",
        "language_label",
        "role",
        "agent_family",
        "task_id",
        "trial",
        "turn_idx",
        "expected_language",
        "detected_language",
        "drift_cause",
        "after_tool_result",
        "excluded_from_agent_language_correctness",
        "previous_other_role_detected_language",
        "text_snippet",
        "simulation_source",
    ]
    return (
        drift.sort_values(["priority", "scenario_label", "domain", "language_label"])
        .groupby(["scenario", "role", "drift_cause"], dropna=False)
        .head(20)[fields]
        .reset_index(drop=True)
    )


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


def write_dict_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dictionaries to CSV."""

    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
