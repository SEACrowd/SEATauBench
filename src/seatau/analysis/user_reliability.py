"""Summarize user-simulator reliability errors in SEA-Tau trajectories.

This script owns `experiments/errors.csv`. It follows the experiment-analysis
template's split between user-simulator errors and agent failures:

- Task-critical user errors: high-severity simulator failures that can preclude
  task completion, currently `###OUT-OF-SCOPE###`.
- Task-benign user errors: lower-severity simulator issues that do not usually
  prevent completion, currently language drift, short detector artifacts, and
  unnatural slot/JSON-like language drift.
- Reported but not counted as errors: `###TRANSFER###` and `###STOP###`, because
  manual trace review shows they are normally terminal markers caused by the
  agent's transfer or completion behavior.

Usage:
  uv run analyze-user-reliability --experiments-csv experiments/experiments.csv --output experiments/errors.csv
  uv run analyze-user-reliability --experiments-csv experiments/experiments.csv --progress DONE --output experiments/errors.csv
  uv run analyze-user-reliability data/simulations/<run_dir> --output experiments/errors.csv
  uv run analyze-user-reliability --experiments-csv experiments/experiments.csv --failure-modes-csv experiments/failure_modes.csv --details-output /tmp/user_reliability_details.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ._common import load_simulations, resolve_paths
from .model_names import canonical_model_name
from .user_language import analyze as analyze_user_language

CRITICAL_LANGUAGE_SCORE = 0.8
AGENT_LANGUAGE_DRIFT_SCORE = 0.95
NON_AGENT_MODES = {"success", "non_agent_infrastructure"}
RELATED_LANGUAGE_CONFUSIONS = {
    "id": {"jv", "ms"},
    "tl": {"ceb"},
    "zh": {"ja", "ko"},
}


def _pct(numerator: int, denominator: int) -> str:
    """Format a percentage with one decimal place."""
    if denominator == 0:
        return "0.0"
    return f"{numerator / denominator * 100:.1f}"


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write rows to CSV, preserving first-seen field order."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_float(value: Any) -> float | None:
    """Parse a float from a CSV or JSON field."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> int:
    """Parse an integer from a CSV or JSON field, defaulting to zero."""
    if value is None or value == "":
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _model_name(model: Any) -> str:
    """Return a readable model name from metadata."""
    return canonical_model_name(model)


def _key(row: dict) -> tuple[str, str, str]:
    """Return the stable run/task/trial key used across analysis outputs."""
    return (str(row.get("run")), str(row.get("task_id")), str(row.get("trial")))


def paths_from_experiments_csv(
    experiments_csv: Path,
    simulations_root: Path,
    progress: set[str] | None = None,
) -> list[Path]:
    """Resolve tracker rows to existing results.json paths."""
    paths: list[Path] = []
    seen: set[Path] = set()
    with experiments_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if progress and row.get("progress", "") not in progress:
                continue
            source = row.get("simulation_source")
            if not source:
                continue
            path = simulations_root / source / "results.json"
            if path.exists() and path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def _user_messages(messages: list[dict]) -> list[tuple[int, str]]:
    """Extract user messages with turn indices for qualitative examples."""
    rows: list[tuple[int, str]] = []
    for index, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        rows.append((int(msg.get("turn_idx", index)), content.replace("\n", " ")))
    return rows


def _detectable_user_messages(messages: list[dict]) -> list[tuple[int, str]]:
    """Mirror analyze-user-language's turn filtering for drift inspection."""
    return [
        (turn_idx, content)
        for turn_idx, content in _user_messages(messages)
        if not content.startswith("###") and len(content) >= 5
    ]


def _has_user_marker(messages: list[dict], marker: str) -> bool:
    """Return whether a user message contains a simulator marker token."""
    return any(marker in content for _, content in _user_messages(messages))


def _sample_user_text(messages: list[dict], drift_turn_indices: list[int]) -> str:
    """Return a compact user text example, preferring drifted turns."""
    user_messages = _user_messages(messages)
    if not user_messages:
        return ""
    drift_turns = set(drift_turn_indices)
    for turn_idx, content in user_messages:
        if turn_idx in drift_turns and not content.startswith("###"):
            return content[:260]
    for _, content in user_messages:
        if not content.startswith("###"):
            return content[:260]
    return user_messages[0][1][:260]


def _substantial_language_drift_turns(
    messages: list[dict],
    language_row: dict | None,
) -> list[int]:
    """Return drifted turn indices with enough natural language to be critical.

    Manual validation showed fastText often flags IDs, emails, airport codes,
    payment IDs, JSON fragments, and one-word confirmations. Those are useful
    language-drift signals but not task-critical simulator errors.
    """
    if not language_row:
        return []

    expected_lang = str(language_row.get("expected_lang") or "")
    drift_indices = {
        _parse_int(value) for value in language_row.get("drift_turn_indices") or []
    }
    detected_langs = list(language_row.get("detected_langs") or [])
    detectable_messages = _detectable_user_messages(messages)

    substantial: list[int] = []
    for index, (turn_idx, content) in enumerate(detectable_messages):
        if turn_idx not in drift_indices:
            continue
        detected_lang = detected_langs[index] if index < len(detected_langs) else ""
        if detected_lang in RELATED_LANGUAGE_CONFUSIONS.get(expected_lang, set()):
            continue
        if _is_substantial_natural_language(content):
            substantial.append(turn_idx)
    return substantial


def _is_substantial_natural_language(text: str) -> bool:
    """Return whether text is a substantial natural-language drift signal."""
    cleaned = re.sub(r"[\w.+-]+@[\w.-]+", " ", text)
    cleaned = re.sub(r"\b[\w-]*\d[\w-]*\b", " ", cleaned)
    cleaned = re.sub(r"\b[A-Z]{2,}\b", " ", cleaned)
    cleaned = re.sub(
        r"\b(user|order|reservation|payment|gift|card|credit|paypal|certificate|id|zip)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    letter_tokens = re.findall(r"[^\W\d_]{3,}", cleaned, flags=re.UNICODE)
    letter_count = sum(len(token) for token in letter_tokens)
    cjk_or_thai_chars = re.findall(r"[\u0E00-\u0E7F\u4E00-\u9FFF]", cleaned)
    return len(letter_tokens) >= 6 and (
        letter_count >= 40 or len(cjk_or_thai_chars) >= 20
    )


def _run_metadata(results_json: Path) -> tuple[dict, list[dict]]:
    """Load run-level metadata and simulations."""
    info, sims = load_simulations(results_json)
    seatau_info = info.get("seatau_info") or {}
    return (
        {
            "run": results_json.parent.name,
            "experiment": seatau_info.get("experiment_name", ""),
            "domain": (info.get("environment_info") or {}).get("domain_name", ""),
            "lang": info.get("lang_id", "") or seatau_info.get("run_language", ""),
            "agent_llm": _model_name((info.get("agent_info") or {}).get("llm")),
            "user_llm": _model_name((info.get("user_info") or {}).get("llm")),
        },
        sims,
    )


def _classify_user_reliability(
    language_row: dict | None,
    has_out_of_scope: bool,
    substantial_drift_turns: list[int],
) -> tuple[str, list[str], list[str]]:
    """Classify a simulator outcome as critical, benign, or none."""
    critical_reasons: list[str] = []
    benign_reasons: list[str] = []

    if has_out_of_scope:
        critical_reasons.append("user_out_of_scope")

    score = _parse_float((language_row or {}).get("score"))
    if score is not None and score < 1.0:
        if score < CRITICAL_LANGUAGE_SCORE:
            if substantial_drift_turns:
                benign_reasons.append("substantial_user_language_drift")
            else:
                benign_reasons.append(
                    "language_drift_short_identifier_or_detector_artifact"
                )
        else:
            benign_reasons.append("mild_user_language_drift")

    if critical_reasons:
        return "critical", critical_reasons, []
    if benign_reasons:
        return "benign", [], benign_reasons
    return "none", [], []


def detail_rows(results_jsons: list[Path]) -> list[dict]:
    """Build per-simulation user-simulator reliability rows."""
    rows: list[dict] = []
    for results_json in results_jsons:
        metadata, sims = _run_metadata(results_json)
        language_by_key = {
            _key(row): row for row in analyze_user_language(results_json)
        }

        for sim in sims:
            messages = sim.get("messages") or []
            row_key = (
                metadata["run"],
                str(sim.get("task_id")),
                str(sim.get("trial")),
            )
            language_row = language_by_key.get(row_key)
            drift_turn_indices = [
                _parse_int(value)
                for value in (language_row or {}).get("drift_turn_indices") or []
            ]
            has_out_of_scope = _has_user_marker(messages, "###OUT-OF-SCOPE###")
            substantial_drift_turns = _substantial_language_drift_turns(
                messages, language_row
            )
            severity, critical_reasons, benign_reasons = _classify_user_reliability(
                language_row,
                has_out_of_scope=has_out_of_scope,
                substantial_drift_turns=substantial_drift_turns,
            )

            user_turns_total = _parse_int((language_row or {}).get("user_turns_total"))
            user_turns_correct = _parse_int(
                (language_row or {}).get("user_turns_correct")
            )
            rows.append(
                {
                    **metadata,
                    "task_id": sim.get("task_id"),
                    "trial": sim.get("trial"),
                    "termination_reason": sim.get("termination_reason"),
                    "reward": (sim.get("reward_info") or {}).get("reward"),
                    "severity": severity,
                    "critical_reasons": ";".join(critical_reasons),
                    "benign_reasons": ";".join(benign_reasons),
                    "user_language_score": (language_row or {}).get("score"),
                    "expected_user_language": (language_row or {}).get("expected_lang"),
                    "detected_user_languages": ";".join(
                        (language_row or {}).get("detected_langs") or []
                    ),
                    "drift_turn_indices": ";".join(map(str, drift_turn_indices)),
                    "substantial_drift_turn_indices": ";".join(
                        map(str, substantial_drift_turns)
                    ),
                    "user_turns_total": user_turns_total,
                    "user_turns_correct": user_turns_correct,
                    "user_drift_turn_count": max(
                        0, user_turns_total - user_turns_correct
                    ),
                    "user_out_of_scope": has_out_of_scope,
                    "user_transfer_marker": _has_user_marker(
                        messages, "###TRANSFER###"
                    ),
                    "user_stop_marker": _has_user_marker(messages, "###STOP###"),
                    "example_user_text": _sample_user_text(
                        messages, drift_turn_indices
                    ),
                }
            )
    return rows


def _failure_context(
    failure_modes_csv: Path | None,
) -> dict[tuple[str, str, str], dict]:
    """Load optional agent-failure context keyed by domain/language/agent."""
    if failure_modes_csv is None or not failure_modes_csv.exists():
        return {}

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    with failure_modes_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (
                str(row.get("domain", "")),
                str(row.get("lang", "")),
                str(row.get("agent_llm", "")),
            )
            grouped[key].append(row)

    context: dict[tuple[str, str, str], dict] = {}
    for key, rows in grouped.items():
        primary_counts = Counter(
            row.get("primary_failure_mode", "")
            for row in rows
            if row.get("primary_failure_mode") not in NON_AGENT_MODES
        )
        top_mode, top_count = (
            primary_counts.most_common(1)[0] if primary_counts else ("", 0)
        )
        agent_language_eval_count = 0
        agent_language_drift_sim_count = 0
        for row in rows:
            score = _parse_float(row.get("agent_language_score"))
            if score is None:
                continue
            agent_language_eval_count += 1
            if score < AGENT_LANGUAGE_DRIFT_SCORE:
                agent_language_drift_sim_count += 1

        context[key] = {
            "agent_language_eval_count": agent_language_eval_count,
            "agent_language_drift_sim_count": agent_language_drift_sim_count,
            "top_agent_failure_mode": top_mode,
            "top_agent_failure_mode_count": top_count,
            "top_agent_failure_mode_percent": _pct(top_count, len(rows)),
        }
    return context


def summary_rows(
    rows: list[dict],
    failure_modes_csv: Path | None = None,
) -> list[dict]:
    """Aggregate per-simulation reliability rows by domain/language/agent."""
    failure_context = _failure_context(failure_modes_csv)
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["domain"]), str(row["lang"]), str(row["agent_llm"]))].append(
            row
        )

    out: list[dict] = []
    notes = (
        "critical=###OUT-OF-SCOPE### because it is an irrecoverable simulator exit; "
        "benign=language drift, including substantial drift, mild drift, and "
        "short identifier/slot-value detector artifacts. ###TRANSFER### and "
        "###STOP### are reported but not counted as simulator errors."
    )
    for (domain, language, agent_llm), group_rows in sorted(grouped.items()):
        total = len(group_rows)
        critical_error_count = sum(
            1 for row in group_rows if row["severity"] == "critical"
        )
        benign_error_count = sum(1 for row in group_rows if row["severity"] == "benign")
        user_language_eval_count = sum(
            1 for row in group_rows if row["user_language_score"] not in (None, "")
        )
        user_language_drift_sim_count = sum(
            1
            for row in group_rows
            if (score := _parse_float(row["user_language_score"])) is not None
            and score < 1.0
        )
        severe_user_language_drift_sim_count = sum(
            1
            for row in group_rows
            if (score := _parse_float(row["user_language_score"])) is not None
            and score < CRITICAL_LANGUAGE_SCORE
        )
        substantial_user_language_drift_sim_count = sum(
            1 for row in group_rows if row["substantial_drift_turn_indices"]
        )
        mild_user_language_drift_sim_count = sum(
            1
            for row in group_rows
            if "mild_user_language_drift" in str(row["benign_reasons"]).split(";")
        )
        user_turns_total = sum(
            _parse_int(row["user_turns_total"]) for row in group_rows
        )
        user_turns_correct = sum(
            _parse_int(row["user_turns_correct"]) for row in group_rows
        )
        user_drift_turn_count = sum(
            _parse_int(row["user_drift_turn_count"]) for row in group_rows
        )
        out_of_scope_count = sum(1 for row in group_rows if row["user_out_of_scope"])
        transfer_marker_count = sum(
            1 for row in group_rows if row["user_transfer_marker"]
        )
        stop_marker_count = sum(1 for row in group_rows if row["user_stop_marker"])
        context = failure_context.get((domain, language, agent_llm), {})
        agent_language_eval_count = _parse_int(context.get("agent_language_eval_count"))
        agent_language_drift_sim_count = _parse_int(
            context.get("agent_language_drift_sim_count")
        )

        out.append(
            {
                "scope": "all_tracked",
                "domain": domain,
                "language": language,
                "agent_llm": agent_llm,
                "num_runs": len({row["run"] for row in group_rows}),
                "num_tasks": len({str(row["task_id"]) for row in group_rows}),
                "num_simulations": total,
                "critical_error_count": critical_error_count,
                "critical_error_percent": _pct(critical_error_count, total),
                "benign_error_count": benign_error_count,
                "benign_error_percent": _pct(benign_error_count, total),
                "total_error_count": critical_error_count + benign_error_count,
                "total_error_percent": _pct(
                    critical_error_count + benign_error_count, total
                ),
                "user_language_eval_count": user_language_eval_count,
                "user_language_drift_sim_count": user_language_drift_sim_count,
                "user_language_drift_sim_percent": _pct(
                    user_language_drift_sim_count, user_language_eval_count
                ),
                "severe_user_language_drift_sim_count": (
                    severe_user_language_drift_sim_count
                ),
                "substantial_user_language_drift_sim_count": (
                    substantial_user_language_drift_sim_count
                ),
                "mild_user_language_drift_sim_count": mild_user_language_drift_sim_count,
                "user_language_drift_turn_count": user_drift_turn_count,
                "user_language_drift_turn_percent": _pct(
                    user_drift_turn_count, user_turns_total
                ),
                "user_turns_total": user_turns_total,
                "user_turns_correct": user_turns_correct,
                "user_out_of_scope_count": out_of_scope_count,
                "user_transfer_marker_count": transfer_marker_count,
                "user_stop_marker_count": stop_marker_count,
                "agent_language_eval_count": agent_language_eval_count,
                "agent_language_drift_sim_count": agent_language_drift_sim_count,
                "agent_language_drift_sim_percent": _pct(
                    agent_language_drift_sim_count, agent_language_eval_count
                ),
                "top_agent_failure_mode": context.get("top_agent_failure_mode", ""),
                "top_agent_failure_mode_count": context.get(
                    "top_agent_failure_mode_count", ""
                ),
                "top_agent_failure_mode_percent": context.get(
                    "top_agent_failure_mode_percent", ""
                ),
                "user_language_drift": (
                    f"{user_language_drift_sim_count}/{user_language_eval_count} sims; "
                    f"{user_drift_turn_count}/{user_turns_total} turns"
                ),
                "agent_language_drift": (
                    f"{agent_language_drift_sim_count}/{agent_language_eval_count} sims"
                ),
                "notes": notes,
            }
        )
    return out


def _print_summary(rows: list[dict]) -> None:
    """Print compact aggregate reliability summary."""
    summary = summary_rows(rows)
    if not summary:
        return
    print(
        f"Analyzed {len(rows)} simulations across {len(summary)} domain/language/agent groups."
    )
    print(f"{'domain':<9} {'lang':<5} {'agent':<38} {'critical':>9} {'benign':>8}")
    for row in summary:
        print(
            f"{row['domain']:<9} {row['language']:<5} {row['agent_llm']:<38} "
            f"{row['critical_error_percent']:>8}% {row['benign_error_percent']:>7}%"
        )


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="results.json files or run directories",
    )
    parser.add_argument(
        "--experiments-csv",
        type=Path,
        help="Add existing simulation_source paths from an experiments.csv tracker",
    )
    parser.add_argument(
        "--simulations-root",
        type=Path,
        default=Path("data/simulations"),
        help="Root directory for simulation_source values from --experiments-csv",
    )
    parser.add_argument(
        "--progress",
        action="append",
        help=(
            "With --experiments-csv, include only tracker rows with this progress "
            "value. Repeat for multiple values, e.g. --progress DONE --progress PARTIAL."
        ),
    )
    parser.add_argument(
        "--failure-modes-csv",
        type=Path,
        help="Optional failure_modes.csv for top agent failure/language context",
    )
    parser.add_argument("--output", type=Path, help="Write aggregate errors.csv")
    parser.add_argument(
        "--details-output",
        type=Path,
        help="Write per-simulation reliability classification rows",
    )
    args = parser.parse_args()

    paths = list(args.paths)
    if args.experiments_csv:
        paths.extend(
            paths_from_experiments_csv(
                args.experiments_csv,
                args.simulations_root,
                progress=set(args.progress) if args.progress else None,
            )
        )
    if not paths:
        parser.error("provide paths or --experiments-csv")

    results_jsons = []
    seen_results: set[Path] = set()
    for results_json in resolve_paths(paths):
        if results_json in seen_results:
            continue
        results_jsons.append(results_json)
        seen_results.add(results_json)

    rows = detail_rows(results_jsons)
    if not rows:
        print("No simulations found.")
        return

    _print_summary(rows)

    if args.details_output:
        _write_csv(args.details_output, rows)
        print(f"\nWrote {len(rows)} per-simulation rows -> {args.details_output}")

    if args.output:
        summaries = summary_rows(rows, failure_modes_csv=args.failure_modes_csv)
        _write_csv(args.output, summaries)
        print(f"\nWrote {len(summaries)} reliability summaries -> {args.output}")


if __name__ == "__main__":
    main()
