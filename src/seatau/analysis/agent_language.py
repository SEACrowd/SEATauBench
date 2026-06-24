"""Compute agent language correctness from results.json trajectories.

Uses stored language_correctness from reward_info when available; falls back
to fastText detection on assistant message content otherwise. Pass
--recalculate to force re-detection even when a stored score exists.

Requires fastText + lid model (see tau2/evaluator/language_correctness.py).

Usage:
  uv run analyze-agent-language <results.json|run_dir> [...]
  uv run analyze-agent-language data/simulations/*/results.json --output output/agent_lang.csv
  uv run analyze-agent-language data/simulations/old_run/ --recalculate
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from tau2.evaluator.language_correctness import (
    _batch_detect_fasttext,
    _load_fasttext_model,
    _normalize_lang_code,
    infer_expected_assistant_language,
)

from ._common import load_simulations, resolve_paths


def _detect_from_messages(
    messages: list[dict],
    expected_lang: str,
    model: object,
) -> dict:
    """Run fastText detection on assistant text turns.

    Args:
        messages: List of message dicts from a simulation.
        expected_lang: ISO language code expected for agent turns.
        model: Loaded fastText model.

    Returns:
        Dict matching the language_correctness schema.
    """
    assistant_turns = [
        (msg.get("turn_idx", i), (msg.get("content") or "").strip())
        for i, msg in enumerate(messages)
        if msg.get("role") == "assistant" and (msg.get("content") or "").strip()
    ]

    if not assistant_turns:
        return dict(
            expected_language=expected_lang,
            assistant_turn_count=0,
            detected_turn_count=0,
            correct_turn_count=0,
            score=None,
            incorrect_turn_indices=[],
            source="computed",
        )

    turn_indices = [idx for idx, _ in assistant_turns]
    texts = [text for _, text in assistant_turns]
    raw_labels = _batch_detect_fasttext(model, texts)

    detected_count = 0
    correct_count = 0
    incorrect_indices: list[int] = []

    for turn_idx, label in zip(turn_indices, raw_labels):
        if label is None:
            incorrect_indices.append(turn_idx)
            continue
        detected_count += 1
        if _normalize_lang_code(label) == expected_lang:
            correct_count += 1
        else:
            incorrect_indices.append(turn_idx)

    total = len(assistant_turns)
    return dict(
        expected_language=expected_lang,
        assistant_turn_count=total,
        detected_turn_count=detected_count,
        correct_turn_count=correct_count,
        score=round(correct_count / total, 4) if total else None,
        incorrect_turn_indices=incorrect_indices,
        source="computed",
    )


def analyze(results_json: Path, recalculate: bool = False) -> list[dict]:
    """Analyze agent language correctness for all simulations in a results file.

    Args:
        results_json: Path to results.json.
        recalculate: If True, ignore stored language_correctness and recompute.

    Returns:
        List of per-simulation dicts with agent language detection results.
    """
    model, model_error = _load_fasttext_model()

    info, sims = load_simulations(results_json)
    run_name = results_json.parent.name
    lang_id = info.get("lang_id", "")
    seatau_info = info.get("seatau_info") or {}
    lang_components = info.get("lang_components")

    expected_lang = infer_expected_assistant_language(
        lang_id=lang_id,
        lang_components=lang_components,
        seatau_experiment=seatau_info.get("experiment_name"),
    )

    rows: list[dict] = []
    for sim in sims:
        task_id = sim.get("task_id")
        trial = sim.get("trial")
        ri = sim.get("reward_info")
        stored_lc = ((ri or {}).get("info") or {}).get("language_correctness")

        base = dict(
            run=run_name,
            lang=lang_id,
            expected_lang=expected_lang,
            task_id=task_id,
            trial=trial,
        )

        if stored_lc and not recalculate:
            rows.append(
                {
                    **base,
                    "assistant_turn_count": stored_lc.get("assistant_turn_count", 0),
                    "detected_turn_count": stored_lc.get("detected_turn_count", 0),
                    "correct_turn_count": stored_lc.get("correct_turn_count", 0),
                    "score": stored_lc.get("score"),
                    "incorrect_turn_indices": stored_lc.get("incorrect_turn_indices", []),
                    "source": "stored",
                    "detector_warning": None,
                }
            )
            continue

        if model is None:
            rows.append(
                {
                    **base,
                    "assistant_turn_count": 0,
                    "detected_turn_count": 0,
                    "correct_turn_count": 0,
                    "score": None,
                    "incorrect_turn_indices": [],
                    "source": "unavailable",
                    "detector_warning": model_error,
                }
            )
            continue

        lc = _detect_from_messages(sim.get("messages") or [], expected_lang, model)
        rows.append({**base, **lc, "detector_warning": None})

    return rows


def _print_summary(rows: list[dict]) -> None:
    by_run: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_run[r["run"]].append(r)

    for run, run_rows in by_run.items():
        scorable = [r for r in run_rows if r["score"] is not None]
        n = len(run_rows)
        print(f"\n{'='*72}")
        print(f"Run : {run}")
        print(f"Lang: {run_rows[0]['lang']}  Expected: {run_rows[0]['expected_lang']}  Simulations: {n}")

        sources = Counter(r["source"] for r in run_rows)
        print(f"Source: {dict(sources)}")

        if run_rows[0].get("detector_warning"):
            print(f"WARNING: {run_rows[0]['detector_warning']}")

        if not scorable:
            print("No assistant turns scored.")
            continue

        scores = [r["score"] for r in scorable]
        mean_score = sum(scores) / len(scores)
        perfect_sims = sum(1 for s in scores if s == 1.0)
        drift_sims = len(scorable) - perfect_sims
        total_turns = sum(r["assistant_turn_count"] for r in scorable)
        correct_turns = sum(r["correct_turn_count"] for r in scorable)

        print(f"\nAggregate ({len(scorable)} evaluated simulations):")
        print(f"  Mean score          : {mean_score:.3f}")
        print(f"  Perfect sims (1.0)  : {perfect_sims} / {len(scorable)}")
        print(f"  Drift sims  (<1.0)  : {drift_sims} / {len(scorable)}")
        if total_turns:
            print(f"  Turn-level accuracy : {correct_turns} / {total_turns} = {correct_turns/total_turns:.3f}")

        worst = sorted(scorable, key=lambda r: (r["score"] or 0, r["task_id"]))[:5]
        if worst and worst[0]["score"] < 1.0:
            print(f"\n  Lowest-scoring simulations:")
            print(f"  {'task':<8} {'trial':<7} {'score':<8} {'source':<10} {'incorrect_turns'}")
            for r in worst:
                if r["score"] == 1.0:
                    break
                print(
                    f"  {str(r['task_id']):<8} {str(r['trial']):<7} {r['score']:<8.3f} "
                    f"{r['source']:<10} {r['incorrect_turn_indices']}"
                )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+", type=Path, help="results.json files or run directories")
    ap.add_argument("--output", type=Path, help="Write per-simulation CSV to this path")
    ap.add_argument(
        "--recalculate",
        action="store_true",
        help="Re-detect from messages even when stored language_correctness exists",
    )
    args = ap.parse_args()

    all_rows: list[dict] = []
    for results_json in resolve_paths(args.paths):
        try:
            all_rows.extend(analyze(results_json, recalculate=args.recalculate))
        except Exception as exc:
            print(f"ERROR {results_json}: {exc}")

    if not all_rows:
        print("No simulations found.")
        return

    _print_summary(all_rows)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        csv_rows = [
            {
                **{k: v for k, v in r.items() if k != "incorrect_turn_indices"},
                "incorrect_turn_indices": ";".join(
                    map(str, r.get("incorrect_turn_indices") or [])
                ),
            }
            for r in all_rows
        ]
        with args.output.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"\nWrote {len(csv_rows)} rows → {args.output}")


if __name__ == "__main__":
    main()

