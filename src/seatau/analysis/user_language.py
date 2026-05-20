"""Detect language drift in user simulator messages.

Loads results.json, runs fastText language detection on each user turn,
and compares to the expected language for the run.

Requires fastText + lid model (see tau2/evaluator/language_correctness.py).

Usage:
  uv run analyze-user-language <results.json|run_dir> [...]
  uv run analyze-user-language data/simulations/*/results.json --output output/user_lang.csv
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


def _user_text_turns(messages: list[dict]) -> list[tuple[int, str]]:
    """Extract (turn_idx, text) for user turns with substantial text content."""
    turns = []
    for i, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue
        content = (msg.get("content") or "").strip()
        # Skip system markers and very short messages
        if content.startswith("###") or len(content) < 5:
            continue
        turns.append((msg.get("turn_idx", i), content))
    return turns


def analyze(results_json: Path) -> list[dict]:
    """Analyze user language for all simulations in a results file.

    Args:
        results_json: Path to results.json.

    Returns:
        List of per-simulation dicts with user language detection results.
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
        messages = sim.get("messages") or []
        turns = _user_text_turns(messages)

        base = dict(
            run=run_name,
            lang=lang_id,
            expected_lang=expected_lang,
            task_id=task_id,
            trial=trial,
            user_turns_total=len(turns),
            user_turns_detected=0,
            user_turns_correct=0,
            score=None,
            drift_turn_indices=[],
            detected_langs=[],
            detector_warning=model_error,
        )

        if not turns:
            base["score"] = None
            rows.append(base)
            continue

        if model is None:
            rows.append(base)
            continue

        texts = [text for _, text in turns]
        turn_indices = [idx for idx, _ in turns]
        raw_labels = _batch_detect_fasttext(model, texts)

        detected_count = 0
        correct_count = 0
        drift_indices: list[int] = []
        detected_langs: list[str] = []

        for turn_idx, label in zip(turn_indices, raw_labels):
            if label is None:
                drift_indices.append(turn_idx)
                detected_langs.append("unknown")
                continue
            lang = _normalize_lang_code(label)
            detected_langs.append(lang)
            detected_count += 1
            if lang == expected_lang:
                correct_count += 1
            else:
                drift_indices.append(turn_idx)

        total = len(turns)
        rows.append(
            dict(
                run=run_name,
                lang=lang_id,
                expected_lang=expected_lang,
                task_id=task_id,
                trial=trial,
                user_turns_total=total,
                user_turns_detected=detected_count,
                user_turns_correct=correct_count,
                score=round(correct_count / total, 4) if total else None,
                drift_turn_indices=drift_indices,
                detected_langs=detected_langs,
                detector_warning=model_error,
            )
        )

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

        if run_rows[0].get("detector_warning"):
            print(f"WARNING: {run_rows[0]['detector_warning']}")
            continue

        if not scorable:
            print("No user turns with detectable language.")
            continue

        scores = [r["score"] for r in scorable]
        mean_score = sum(scores) / len(scores)
        drift_sims = sum(1 for s in scores if s < 1.0)
        perfect_sims = sum(1 for s in scores if s == 1.0)
        total_turns = sum(r["user_turns_total"] for r in scorable)
        correct_turns = sum(r["user_turns_correct"] for r in scorable)

        print(f"\nAggregate ({len(scorable)} evaluated simulations):")
        print(f"  Mean score          : {mean_score:.3f}")
        print(f"  Perfect sims (1.0)  : {perfect_sims} / {len(scorable)}")
        print(f"  Drift sims  (<1.0)  : {drift_sims} / {len(scorable)}")
        print(f"  Turn-level accuracy : {correct_turns} / {total_turns} = {correct_turns/total_turns:.3f}")

        # Detected language distribution (only drift turns)
        drift_langs: list[str] = []
        for r in scorable:
            expected = r["expected_lang"]
            for lang in (r.get("detected_langs") or []):
                if lang != expected:
                    drift_langs.append(lang)
        if drift_langs:
            lang_counts = Counter(drift_langs)
            top = lang_counts.most_common(5)
            print(f"\n  Drift language breakdown (top {len(top)}):")
            for lang, cnt in top:
                print(f"    {lang:<6} {cnt}")

        # Worst sims
        worst = sorted(scorable, key=lambda r: r["score"])[:5]
        if worst and worst[0]["score"] < 1.0:
            print(f"\n  Lowest-scoring simulations:")
            print(f"  {'task':<8} {'trial':<7} {'score':<8} {'drift_turns'}")
            for r in worst:
                if r["score"] == 1.0:
                    break
                print(
                    f"  {str(r['task_id']):<8} {str(r['trial']):<7} {r['score']:<8.3f} "
                    f"{r['drift_turn_indices']}"
                )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("paths", nargs="+", type=Path, help="results.json files or run directories")
    ap.add_argument("--output", type=Path, help="Write per-simulation CSV to this path")
    args = ap.parse_args()

    all_rows: list[dict] = []
    for results_json in resolve_paths(args.paths):
        try:
            all_rows.extend(analyze(results_json))
        except Exception as exc:
            print(f"ERROR {results_json}: {exc}")

    if not all_rows:
        print("No simulations found.")
        return

    _print_summary(all_rows)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Flatten list fields for CSV
        csv_rows = [
            {
                **{k: v for k, v in r.items() if k not in ("drift_turn_indices", "detected_langs")},
                "drift_turn_indices": ";".join(map(str, r.get("drift_turn_indices") or [])),
                "detected_langs": ";".join(r.get("detected_langs") or []),
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

