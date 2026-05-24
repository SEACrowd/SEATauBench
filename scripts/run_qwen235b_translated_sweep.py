"""Run translated Qwen3-235B sweeps with adaptive concurrency.

This launcher is intended for long unattended runs over airline, retail, and
telecom. It defaults to the OpenRouter Qwen3-235B agent and lets the user
simulator run either on localhost or OpenRouter.

Recommended workflow:
  1. Pick one domain.
  2. Run all five languages for that domain.
  3. Move to the next domain only after the current one is done.

Examples:
  # Run one domain across all languages first.
  uv run python scripts/run_qwen235b_translated_sweep.py --domains airline

  uv run python scripts/run_qwen235b_translated_sweep.py --dry-run

  uv run python scripts/run_qwen235b_translated_sweep.py \
    --user-backend localhost --resume-partials

  uv run python scripts/run_qwen235b_translated_sweep.py \
    --user-backend openrouter --user-api-key-env OPENROUTER_API_KEY
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.update_experiments_csv import compute_metrics, update_csv  # noqa: E402

EXP_NAME = "translated"
DEFAULT_DOMAINS = ("airline", "retail", "telecom")
LANGS = ("id", "th", "tl", "vi", "zh")
CSV_AGENT = "Qwen3-235B-A22B-Instruct-2507"

DEFAULT_AGENT_MODEL = "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas"
LOCAL_MODEL = (
    "/project/lt200394-thllmV/jab/seacrowd/models/"
    "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8"
)
LOCAL_API_BASE = "http://127.0.0.1:8000/v1"
NOTE_PATH = Path("experiments/translated_user-llm.md")

RATE_LIMIT_RE = re.compile(
    r"RateLimitError|rate_limit_exceeded|\b429\b|Too Many Requests|daily limit|weekly limit",
    re.IGNORECASE,
)
LIMIT_EXHAUSTED_RE = re.compile(
    r"Insufficient credits|Key limit exceeded|current quota|billing details",
    re.IGNORECASE,
)
TRANSIENT_RE = re.compile(
    r"Connection error|InternalServerError|RemoteProtocolError|ReadTimeout|"
    r"Timeout|HTTPStatusError|ServiceUnavailable|\b502\b|\b503\b|\b504\b|"
    r"\"auto\" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set|"
    r"AssistantMessage must have either content or tool_calls",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RunConfig:
    agent_llm: str
    user_llm: str
    agent_llm_args: dict[str, Any]
    user_llm_args: dict[str, Any]


@dataclass(frozen=True)
class LogSignals:
    rate_limited: bool
    limit_exhausted: bool
    transient_error: bool

    @property
    def retryable(self) -> bool:
        return self.rate_limited or self.transient_error

    @property
    def unhealthy(self) -> bool:
        return self.limit_exhausted or self.retryable


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="") as f:
        return list(csv.DictReader(f))


def _vertex_runtime_kwargs() -> dict[str, str]:
    project = os.environ.get("VERTEXAI_PROJECT", "").strip()
    if not project:
        raise RuntimeError("VERTEXAI_PROJECT is required for vertex runs")

    location = os.environ.get("VERTEXAI_LOCATION", "").strip() or "global"
    return {"vertex_project": project, "vertex_location": location}


def _pending_targets(
    rows: list[dict[str, str]],
    domains: tuple[str, ...],
    langs: tuple[str, ...],
    resume_partials: bool,
    clean_rerun_partials: bool,
) -> list[dict[str, str]]:
    lookup = {
        (row["domain"], row["language_or_scenario"]): row
        for row in rows
        if row["experiment"] == EXP_NAME and row["agent_llm"] == CSV_AGENT
    }
    allowed_progress = {"TODO"}
    if resume_partials:
        allowed_progress |= {"PARTIAL", "IN_PROGRESS", "NEEDS_CHECK"}
    elif clean_rerun_partials:
        allowed_progress |= {"PARTIAL", "IN_PROGRESS", "NEEDS_CHECK"}

    targets: list[dict[str, str]] = []
    for domain in domains:
        for lang in langs:
            row = lookup.get((domain, lang))
            if row is not None and row["progress"] in allowed_progress:
                targets.append(row)
    return targets


def _save_to(domain: str, lang: str, suffix: str) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return f"{stamp}_translated_{domain}_trial-3_{lang}_{CSV_AGENT}_{suffix}"


def _ensure_note_file(domain: str, lang: str) -> Path:
    if not NOTE_PATH.exists():
        NOTE_PATH.write_text(f"# translated / {CSV_AGENT}\n", encoding="utf-8")
    return NOTE_PATH


def _build_run_config(args: argparse.Namespace) -> RunConfig:
    agent_args: dict[str, Any] = {"temperature": args.temperature}
    if args.agent_llm.startswith("openrouter/"):
        agent_args["api_key_env"] = args.agent_api_key_env
    if args.agent_llm.startswith("vertex_ai/"):
        agent_args.update(_vertex_runtime_kwargs())

    if args.user_backend == "localhost":
        user_llm = args.local_user_llm
        user_args: dict[str, Any] = {
            "temperature": args.temperature,
            "api_base": args.local_api_base,
            "custom_llm_provider": "openai",
        }
    elif args.user_backend == "openrouter":
        user_llm = args.user_llm
        user_args = {
            "temperature": args.temperature,
            "api_key_env": args.user_api_key_env,
        }
    elif args.user_backend == "vertex":
        user_llm = args.user_llm
        user_args = {
            "temperature": args.temperature,
            **_vertex_runtime_kwargs(),
        }
    else:
        raise ValueError(f"unknown user backend: {args.user_backend}")

    return RunConfig(
        agent_llm=args.agent_llm,
        user_llm=user_llm,
        agent_llm_args=agent_args,
        user_llm_args=user_args,
    )


def _suffix_for_config(config: RunConfig, user_backend: str) -> str:
    if config.agent_llm.startswith("vertex_ai/"):
        agent = "vertex"
    elif config.agent_llm.startswith("openrouter/"):
        agent = "openrouter"
    else:
        agent = "local"
    return f"{agent}_agent_{user_backend}_user"


def _read_log_signals(log_path: Path) -> LogSignals:
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return LogSignals(False, False, False)
    return LogSignals(
        rate_limited=bool(RATE_LIMIT_RE.search(text)),
        limit_exhausted=bool(LIMIT_EXHAUSTED_RE.search(text)),
        transient_error=bool(TRANSIENT_RE.search(text)),
    )


def _mark_row(
    csv_path: Path,
    domain: str,
    lang: str,
    progress: str,
    save_to: str,
    note: str,
) -> None:
    rows = _read_rows(csv_path)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            if (
                row["experiment"] == EXP_NAME
                and row["agent_llm"] == CSV_AGENT
                and row["domain"] == domain
                and row["language_or_scenario"] == lang
            ):
                row["progress"] = progress
                row["progress_notes"] = note
                row["simulation_source"] = save_to
            writer.writerow(row)


def _run_one(
    domain: str,
    lang: str,
    save_to: str,
    config: RunConfig,
    log_dir: Path,
    max_concurrency: int,
    num_trials: int,
    num_tasks: int | None,
    timeout: int | None,
) -> tuple[Path, float]:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{save_to}.log"
    cmd = [
        "uv",
        "run",
        "tau2",
        "run",
        "--seatau-experiment",
        EXP_NAME,
        "--domain",
        domain,
        "--lang-id",
        lang,
        "--agent-llm",
        config.agent_llm,
        "--user-llm",
        config.user_llm,
        "--user-llm-args",
        json.dumps(config.user_llm_args),
        "--agent-llm-args",
        json.dumps(config.agent_llm_args),
        "--num-trials",
        str(num_trials),
        "--max-concurrency",
        str(max_concurrency),
        "--auto-resume",
        "--save-to",
        save_to,
    ]
    if num_tasks is not None:
        cmd.extend(["--num-tasks", str(num_tasks)])
    if timeout is not None:
        cmd.extend(["--timeout", str(timeout)])
    print(
        f"$ uv run tau2 run --seatau-experiment {EXP_NAME} --domain {domain} "
        f"--lang-id {lang} --agent-llm {config.agent_llm} --user-llm {config.user_llm} "
        f"--num-trials {num_trials} --max-concurrency {max_concurrency} --auto-resume "
        f"--save-to {save_to}",
        flush=True,
    )
    print(f"log: {log_path}", flush=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        start = time.perf_counter()
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
        return_code = proc.wait()
        elapsed = time.perf_counter() - start
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, cmd)
    return log_path, elapsed


def _update_csv(results_path: Path, csv_path: Path, progress: str) -> None:
    update_csv(results_path, csv_path, progress=progress, agent_llm_override=CSV_AGENT)


def _append_note_summary(note_path: Path, results_path: Path) -> None:
    metrics = compute_metrics(results_path)
    summary = (
        "\n## Completion Summary\n\n"
        f"- Save-to folder: `{metrics['simulation_source']}`\n"
        f"- Experiment: `{metrics['experiment']}`\n"
        f"- Domain: `{metrics['domain']}`\n"
        f"- Language: `{metrics['language_or_scenario']}`\n"
        f"- Agent LLM: `{metrics['agent_llm']}`\n"
        f"- Pass@1 / Pass@2 / Pass@3: "
        f"`{metrics['pass_hat_1']} / {metrics['pass_hat_2']} / {metrics['pass_hat_3']}`\n"
        f"- Total simulations: `{metrics['total_simulations']}`\n"
        f"- Total tasks: `{metrics['total_tasks']}`\n"
    )
    with note_path.open("a", encoding="utf-8") as f:
        f.write(summary)


def _next_concurrency(
    current: int,
    signals: LogSignals,
    elapsed_seconds: float,
    min_concurrency: int,
    max_concurrency: int,
    fast_row_seconds: int,
) -> int:
    if signals.limit_exhausted:
        return current
    if signals.rate_limited:
        return max(min_concurrency, max(min_concurrency, current // 2))
    if signals.transient_error:
        return max(min_concurrency, current - 2)
    if elapsed_seconds <= fast_row_seconds:
        return min(max_concurrency, current + 2)
    return min(max_concurrency, current + 1)


def _progress_for_completed_row(metrics: dict[str, object], signals: LogSignals) -> str:
    base_task_count = int(metrics["_base_task_count"])
    total_tasks = int(metrics["total_tasks"])
    total_sims = int(metrics["total_simulations"])
    evaluated_sims = int(metrics.get("_evaluated_simulations", total_sims))
    if total_tasks < base_task_count:
        return "PARTIAL"
    if evaluated_sims < total_sims or signals.unhealthy:
        return "NEEDS_CHECK"
    return "DONE"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run translated Qwen3-235B sweeps over airline/retail/telecom."
    )
    parser.add_argument("--csv", type=Path, default=Path("experiments/experiments.csv"))
    parser.add_argument("--logs", type=Path, default=Path("logs"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--domains", nargs="*", default=list(DEFAULT_DOMAINS))
    parser.add_argument("--langs", nargs="*", default=list(LANGS))
    parser.add_argument(
        "--resume-partials",
        action="store_true",
        help="Resume PARTIAL, NEEDS_CHECK, and IN_PROGRESS rows in-place.",
    )
    parser.add_argument(
        "--clean-rerun-partials",
        action="store_true",
        help="Rerun PARTIAL, NEEDS_CHECK, and IN_PROGRESS rows from fresh save folders.",
    )
    parser.add_argument("--agent-llm", default=DEFAULT_AGENT_MODEL)
    parser.add_argument("--agent-api-key-env", default="OPENROUTER_API_KEY")
    parser.add_argument(
        "--user-backend",
        choices=("localhost", "openrouter", "vertex"),
        default="localhost",
        help="Run the user simulator on localhost, OpenRouter, or Vertex.",
    )
    parser.add_argument("--user-llm", default=DEFAULT_AGENT_MODEL)
    parser.add_argument("--user-api-key-env", default="OPENROUTER_API_KEY_ALGOVERSE")
    parser.add_argument("--local-user-llm", default=LOCAL_MODEL)
    parser.add_argument("--local-api-base", default=LOCAL_API_BASE)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-trials", type=int, default=3)
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=None,
        help="Limit tasks per row. Useful for smoke tests.",
    )
    parser.add_argument(
        "--no-update-csv",
        action="store_true",
        help="Run without mutating experiments.csv. Useful for smoke tests.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Maximum wallclock seconds per simulation.",
    )
    parser.add_argument("--initial-concurrency", type=int, default=None)
    parser.add_argument("--min-concurrency", type=int, default=4)
    parser.add_argument("--max-concurrency", type=int, default=25)
    parser.add_argument("--max-row-attempts", type=int, default=4)
    parser.add_argument("--retry-sleep-seconds", type=int, default=60)
    parser.add_argument(
        "--fast-row-seconds",
        type=int,
        default=20 * 60,
        help="Increase concurrency more aggressively if a full row finishes faster than this.",
    )
    parser.add_argument(
        "--stop-on-limit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Stop the whole queue when credits or key limits are exhausted.",
    )
    args = parser.parse_args()

    if args.resume_partials and args.clean_rerun_partials:
        parser.error("--resume-partials and --clean-rerun-partials are mutually exclusive")

    config = _build_run_config(args)
    suffix = _suffix_for_config(config, args.user_backend)
    initial_concurrency = args.initial_concurrency
    if initial_concurrency is None:
        if args.user_backend == "localhost":
            initial_concurrency = 8
        elif args.user_backend == "vertex":
            initial_concurrency = args.max_concurrency
        else:
            initial_concurrency = 15
    concurrency = max(
        args.min_concurrency, min(args.max_concurrency, initial_concurrency)
    )

    rows = _read_rows(args.csv)
    targets = _pending_targets(
        rows,
        tuple(args.domains),
        tuple(args.langs),
        args.resume_partials,
        args.clean_rerun_partials,
    )
    if not targets:
        print("No pending Qwen3-235B rows found.", flush=True)
        return 0

    for row in targets:
        domain = row["domain"]
        lang = row["language_or_scenario"]
        note_path = _ensure_note_file(domain, lang)
        source = row.get("simulation_source", "").strip()
        save_to = (
            source
            if args.resume_partials
            and row["progress"] in {"PARTIAL", "IN_PROGRESS", "NEEDS_CHECK"}
            and source
            else _save_to(domain, lang, suffix)
        )

        if args.dry_run:
            print(
                f"{domain} {lang} -> {save_to} "
                f"(concurrency={concurrency}, user_backend={args.user_backend}, note={note_path})"
            )
            continue

        if not args.no_update_csv:
            _mark_row(
                args.csv,
                domain,
                lang,
                "IN_PROGRESS",
                save_to,
                f"Running Qwen3-235B sweep at concurrency {concurrency}; "
                f"user_backend={args.user_backend}.",
            )

        for attempt in range(1, args.max_row_attempts + 1):
            log_path, elapsed = _run_one(
                domain=domain,
                lang=lang,
                save_to=save_to,
                config=config,
                log_dir=args.logs,
                max_concurrency=concurrency,
                num_trials=args.num_trials,
                num_tasks=args.num_tasks,
                timeout=args.timeout,
            )
            signals = _read_log_signals(log_path)
            results_path = Path("data/simulations") / save_to / "results.json"

            if signals.limit_exhausted:
                if not args.no_update_csv:
                    _mark_row(
                        args.csv,
                        domain,
                        lang,
                        "PARTIAL",
                        save_to,
                        "Stopped because provider credits/key limit were exhausted. "
                        "Increase/reset the configured key limit and resume this row.",
                    )
                print(f"[limit] {domain}/{lang}: stopping after {log_path}", flush=True)
                if args.stop_on_limit:
                    return 2

            if not results_path.exists():
                concurrency = _next_concurrency(
                    concurrency,
                    signals,
                    elapsed,
                    args.min_concurrency,
                    args.max_concurrency,
                    args.fast_row_seconds,
                )
                if attempt == args.max_row_attempts:
                    raise FileNotFoundError(results_path)
                print(
                    f"[retry] {domain}/{lang}: missing results; "
                    f"next concurrency={concurrency}",
                    flush=True,
                )
                time.sleep(args.retry_sleep_seconds)
                continue

            metrics = compute_metrics(results_path)
            progress = _progress_for_completed_row(metrics, signals)
            if not args.no_update_csv:
                _update_csv(results_path, args.csv, progress=progress)
            _append_note_summary(note_path, results_path)

            base_task_count = int(metrics["_base_task_count"])
            total_tasks = int(metrics["total_tasks"])
            if progress == "PARTIAL" and total_tasks < base_task_count:
                concurrency = _next_concurrency(
                    concurrency,
                    signals,
                    elapsed,
                    args.min_concurrency,
                    args.max_concurrency,
                    args.fast_row_seconds,
                )
                print(
                    f"[retry] {domain}/{lang}: partial result "
                    f"({total_tasks}/{base_task_count}); next concurrency={concurrency}",
                    flush=True,
                )
                if attempt < args.max_row_attempts and not signals.limit_exhausted:
                    time.sleep(args.retry_sleep_seconds)
                    continue

            concurrency = _next_concurrency(
                concurrency,
                signals,
                elapsed,
                args.min_concurrency,
                args.max_concurrency,
                args.fast_row_seconds,
            )
            print(f"updated {domain} {lang} from {results_path}", flush=True)
            print(f"log: {log_path}", flush=True)
            print(f"note: {note_path}", flush=True)
            print(f"[concurrency] next row will start at {concurrency}", flush=True)
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
