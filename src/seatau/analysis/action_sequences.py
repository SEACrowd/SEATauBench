"""Analyze action sequences in results.json to identify read/write failure patterns.

Patterns reported per simulation:
  all_pass           – all expected reads and writes matched
  read_ok_write_fail – all reads matched, ≥1 write failed
  read_only_pass     – read-only task, all reads matched
  read_only_fail     – read-only task, ≥1 read failed
  read_fail          – ≥1 read failed (with or without writes)
  no_actions         – no action_checks present
  not_evaluated      – reward_info absent

Usage:
  uv run analyze-action-sequences <results.json|run_dir> [...]
  uv run analyze-action-sequences data/simulations/*/results.json --output output/action_seqs.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from ._common import load_simulations, resolve_paths


def _classify(
    action_checks: list[dict], actual_names: set[str]
) -> tuple[str, bool | None]:
    """Classify the action outcome for a simulation.

    Args:
        action_checks: List of action check dicts from reward_info.
        actual_names: Set of tool call names actually made in the conversation.

    Returns:
        (pattern, write_attempted) where write_attempted is only set for
        read_ok_write_fail (True = write tool was called but failed, False = never called).
    """
    reads = [ac for ac in action_checks if ac.get("tool_type") == "read"]
    writes = [ac for ac in action_checks if ac.get("tool_type") == "write"]

    if not reads and not writes:
        return "no_actions", None

    reads_pass = all(ac.get("action_match") for ac in reads) if reads else True

    if not writes:
        return ("read_only_pass" if reads_pass else "read_only_fail"), None

    writes_pass = all(ac.get("action_match") for ac in writes)

    if reads_pass and writes_pass:
        return "all_pass", None

    if reads_pass and not writes_pass:
        failed_write_names = {
            ac["action"]["name"] for ac in writes if not ac.get("action_match")
        }
        return "read_ok_write_fail", bool(failed_write_names & actual_names)

    return "read_fail", None


def analyze(results_json: Path) -> list[dict]:
    """Analyze action sequences for all simulations in a results file.

    Args:
        results_json: Path to results.json.

    Returns:
        List of per-simulation dicts with pattern classification.
    """
    info, sims = load_simulations(results_json)
    run_name = results_json.parent.name
    lang_id = info.get("lang_id", "")
    domain = (info.get("environment_info") or {}).get("domain_name", "")

    rows: list[dict] = []
    for sim in sims:
        task_id = sim.get("task_id")
        trial = sim.get("trial")
        term = sim.get("termination_reason", "")
        ri = sim.get("reward_info")
        reward = (ri or {}).get("reward")

        if ri is None:
            rows.append(
                dict(
                    run=run_name,
                    domain=domain,
                    lang=lang_id,
                    task_id=task_id,
                    trial=trial,
                    termination_reason=term,
                    reward=reward,
                    reads_total=0,
                    reads_matched=0,
                    writes_total=0,
                    writes_matched=0,
                    write_attempted=None,
                    pattern="not_evaluated",
                )
            )
            continue

        action_checks = ri.get("action_checks") or []
        actual_names = {
            tc["name"]
            for msg in (sim.get("messages") or [])
            for tc in (msg.get("tool_calls") or [])
            if tc.get("name")
        }

        reads = [ac for ac in action_checks if ac.get("tool_type") == "read"]
        writes = [ac for ac in action_checks if ac.get("tool_type") == "write"]
        pattern, write_attempted = _classify(action_checks, actual_names)

        rows.append(
            dict(
                run=run_name,
                domain=domain,
                lang=lang_id,
                task_id=task_id,
                trial=trial,
                termination_reason=term,
                reward=reward,
                reads_total=len(reads),
                reads_matched=sum(1 for r in reads if r.get("action_match")),
                writes_total=len(writes),
                writes_matched=sum(1 for w in writes if w.get("action_match")),
                write_attempted=write_attempted,
                pattern=pattern,
            )
        )

    return rows


_PATTERN_ORDER = (
    "all_pass",
    "read_only_pass",
    "read_ok_write_fail",
    "read_only_fail",
    "read_fail",
    "no_actions",
    "not_evaluated",
)


def _print_summary(rows: list[dict]) -> None:
    by_run: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_run[r["run"]].append(r)

    for run, run_rows in by_run.items():
        n = len(run_rows)
        print(f"\n{'='*72}")
        print(f"Run : {run}")
        print(f"Lang: {run_rows[0]['lang']}  Domain: {run_rows[0]['domain']}  Simulations: {n}")

        counts = Counter(r["pattern"] for r in run_rows)
        print(f"\n{'Pattern':<28} {'Count':>6}  {'%':>6}  Notes")
        print("-" * 60)
        for pat in _PATTERN_ORDER:
            c = counts.get(pat, 0)
            if not c:
                continue
            pct = c / n * 100
            notes = ""
            if pat == "read_ok_write_fail":
                attempted = sum(
                    1
                    for r in run_rows
                    if r["pattern"] == pat and r.get("write_attempted")
                )
                skipped = c - attempted
                notes = f"attempted={attempted}, skipped={skipped}"
            print(f"  {pat:<26} {c:>6}  {pct:>5.1f}%  {notes}")

        failing_pats = {"read_ok_write_fail", "read_only_fail", "read_fail"}
        failing = [r for r in run_rows if r["pattern"] in failing_pats]
        if not failing:
            continue

        by_task: dict[str, list[dict]] = defaultdict(list)
        for r in failing:
            by_task[str(r["task_id"])].append(r)

        print(f"\nTasks with failures ({len(by_task)} / {len({str(r['task_id']) for r in run_rows})}):")
        print(f"  {'task':<8} {'trials':<8} {'patterns (per trial)'}")
        print("  " + "-" * 56)

        def _sort_key(tid: str) -> tuple:
            return (0, int(tid)) if tid.isdigit() else (1, tid)

        for tid in sorted(by_task, key=_sort_key):
            trial_rows = sorted(by_task[tid], key=lambda r: r.get("trial") or 0)
            parts = []
            for r in trial_rows:
                detail = r["pattern"]
                if r["pattern"] == "read_ok_write_fail":
                    detail += "(attempted)" if r.get("write_attempted") else "(skipped)"
                parts.append(detail)
            print(f"  {tid:<8} {len(trial_rows):<8} {', '.join(parts)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
        with args.output.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nWrote {len(all_rows)} rows → {args.output}")


if __name__ == "__main__":
    main()

