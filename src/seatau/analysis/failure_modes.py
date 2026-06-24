"""Classify agent failure modes in SEA-Tau trajectories.

The classifier is intentionally heuristic: it turns qualitative trace patterns
from manual review into auditable counters that can be compared across runs.

Usage:
  uv run analyze-failure-modes <results.json|run_dir> [...]
  uv run analyze-failure-modes --experiments-csv experiments/experiments.csv --summary-dir experiments/failure_mode_tables/all_tracked
  uv run analyze-failure-modes --experiments-csv experiments/experiments.csv --progress DONE --summary-dir experiments/failure_mode_tables/done
  uv run analyze-failure-modes --experiments-csv experiments/experiments.csv --max-pass-hat 30 --summary-dir experiments/failure_mode_tables/low_metric
  uv run analyze-failure-modes data/simulations/<run_dir> --output failures.csv
  uv run analyze-failure-modes data/simulations/<run_dir> --summary-dir experiments/failure_mode_tables
  uv run analyze-failure-modes data/simulations/<run_dir> --examples 5
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ._common import load_simulations, resolve_paths
from .model_names import canonical_model_name

_LOOKUP_TOOL_NAMES = {
    "find_user_id_by_email",
    "find_user_id_by_name_zip",
    "get_customer_by_phone",
    "get_customer_by_id",
    "get_customer_by_name",
    "get_user_details",
}

_PLACEHOLDER_VALUES = {
    "",
    "?",
    "unknown",
    "unprovided",
    "n/a",
    "na",
    "user@example.com",
    "test@example.com",
    "12345",
    "1234567890",
    "0123456789",
    "0912345678",
}

_REFUSAL_TERMS = (
    "cannot",
    "can't",
    "unable",
    "not allowed",
    "not permitted",
    "policy",
    "ขออภัย",
    "ไม่สามารถ",
    "ไม่อนุญาต",
    "抱歉",
    "不能",
    "无法",
    "不可以",
    "không thể",
    "không được",
    "xin lỗi",
    "tidak dapat",
    "tidak bisa",
    "maaf",
    "hindi maaaring",
    "paumanhin",
)

_USER_DEVICE_ACTIONS = {
    "check_status_bar",
    "check_network_status",
    "check_network_mode_preference",
    "check_sim_status",
    "check_data_restriction_status",
    "check_apn_settings",
    "check_wifi_status",
    "check_wifi_calling_status",
    "check_vpn_status",
    "check_installed_apps",
    "check_app_status",
    "check_app_permissions",
    "run_speed_test",
    "can_send_mms",
    "set_network_mode_preference",
    "toggle_airplane_mode",
    "reseat_sim_card",
    "toggle_data",
    "toggle_roaming",
    "toggle_data_saver_mode",
    "set_apn_settings",
    "reset_apn_settings",
    "toggle_wifi",
    "toggle_wifi_calling",
    "connect_vpn",
    "disconnect_vpn",
    "grant_app_permission",
    "reboot_device",
}

_PRIMARY_MODE_ORDER = (
    "success",
    "non_agent_infrastructure",
    "credential_or_identifier_hallucination",
    "tool_error_loop",
    "missing_required_write",
    "wrong_write_arguments_or_state",
    "missing_user_device_instruction",
    "premature_refusal_or_policy_misread",
    "translated_identifier_lookup_failure",
    "non_action_assertion_failure",
    "dialogue_or_action_loop",
    "wrong_read_arguments",
    "missing_required_read",
    "max_steps_or_dialogue_loop",
    "no_tool_progress",
    "language_drift",
    "unclassified_failure",
)

_SUMMARY_GROUPS = {
    "by_domain": ("domain",),
    "by_language": ("lang",),
    "by_agent": ("agent_llm",),
    "by_domain_language": ("domain", "lang"),
    "by_domain_agent": ("domain", "agent_llm"),
    "by_language_agent": ("lang", "agent_llm"),
    "by_domain_language_agent": ("domain", "lang", "agent_llm"),
    "by_run": ("run",),
}


def _jsonish(value: Any) -> str:
    """Return a stable compact representation for matching and CSV output."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _contains_non_ascii(value: Any) -> bool:
    """Return whether any string inside a value contains non-ASCII characters."""
    if isinstance(value, str):
        return any(ord(ch) > 127 for ch in value)
    if isinstance(value, dict):
        return any(_contains_non_ascii(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_non_ascii(v) for v in value)
    return False


def _contains_placeholder(value: Any) -> bool:
    """Return whether a value contains obvious fake identifiers."""
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in _PLACEHOLDER_VALUES:
            return True
        digits = re.sub(r"\D", "", normalized)
        return bool(len(digits) >= 6 and len(set(digits)) == 1)
    if isinstance(value, dict):
        return any(_contains_placeholder(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_placeholder(v) for v in value)
    return False


def _message_text(messages: list[dict]) -> str:
    """Concatenate user-visible assistant and user message content."""
    return "\n".join(
        (msg.get("content") or "")
        for msg in messages
        if msg.get("role") in {"assistant", "user"} and msg.get("content")
    )


def _assistant_text(messages: list[dict]) -> str:
    """Concatenate assistant message content."""
    return "\n".join(
        (msg.get("content") or "")
        for msg in messages
        if msg.get("role") == "assistant" and msg.get("content")
    )


def _tool_calls(messages: list[dict]) -> list[dict]:
    """Extract tool calls with message role and turn index attached."""
    calls: list[dict] = []
    for msg in messages:
        for call in msg.get("tool_calls") or []:
            calls.append(
                {
                    **call,
                    "message_role": msg.get("role"),
                    "turn_idx": msg.get("turn_idx"),
                }
            )
    return calls


def _tool_errors(messages: list[dict]) -> list[str]:
    """Extract tool error messages."""
    errors: list[str] = []
    for msg in messages:
        if msg.get("role") != "tool":
            continue
        content = msg.get("content") or ""
        if "Error:" in content or content.lower().startswith("error"):
            errors.append(content)
    return errors


def _tasks_by_id(tasks: list[dict]) -> dict[str, dict]:
    """Index task definitions by string id."""
    return {str(task.get("id")): task for task in tasks}


def _task_actions(task: dict | None) -> list[dict]:
    """Return expected actions from a task definition."""
    if not task:
        return []
    criteria = task.get("evaluation_criteria") or {}
    return criteria.get("actions") or []


def _action_checks(reward_info: dict | None) -> list[dict]:
    """Return reward action checks, normalizing null to an empty list."""
    return (reward_info or {}).get("action_checks") or []


def _stored_language_score(reward_info: dict | None) -> float | None:
    """Return stored assistant language correctness score when available."""
    info = (reward_info or {}).get("info") or {}
    language_correctness = info.get("language_correctness") or {}
    score = language_correctness.get("score")
    return float(score) if score is not None else None


def _model_name(model: Any) -> str:
    """Return a readable model name from metadata."""
    return canonical_model_name(model)


def _expected_action_names(
    task: dict | None,
    action_checks: list[dict],
    requestor: str | None = None,
) -> set[str]:
    """Return expected action names, optionally filtered by requestor."""
    actions = _task_actions(task)
    if not actions:
        actions = [check.get("action") or {} for check in action_checks]
    names = set()
    for action in actions:
        if requestor is not None and action.get("requestor") != requestor:
            continue
        name = action.get("name")
        if name:
            names.add(name)
    return names


def _actual_action_names(calls: list[dict], requestor: str | None = None) -> set[str]:
    """Return actual tool call names, optionally filtered by requestor."""
    names = set()
    for call in calls:
        if requestor is not None and call.get("requestor") != requestor:
            continue
        name = call.get("name")
        if name:
            names.add(name)
    return names


def _failed_checks_by_type(action_checks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split failed action checks into read and write checks."""
    failed = [check for check in action_checks if not check.get("action_match")]
    read_failed = [check for check in failed if check.get("tool_type") == "read"]
    write_failed = [check for check in failed if check.get("tool_type") == "write"]
    return read_failed, write_failed


def _has_refusal(messages: list[dict]) -> bool:
    """Return whether assistant text includes refusal/policy language."""
    text = _assistant_text(messages).casefold()
    return any(term.casefold() in text for term in _REFUSAL_TERMS)


def _lookup_non_ascii_failure(calls: list[dict], errors: list[str]) -> bool:
    """Detect translated identifier values passed to lookup tools."""
    if not errors:
        return False
    for call in calls:
        if call.get("name") in _LOOKUP_TOOL_NAMES and _contains_non_ascii(
            call.get("arguments")
        ):
            return True
    return False


def _repeated_tool_error(
    calls: list[dict], errors: list[str]
) -> tuple[bool, str | None, Any, int]:
    """Detect repeated same-tool/same-arguments error loops."""
    if len(errors) < 3:
        return False, None, None, 0
    counter = Counter(
        (call.get("name"), _jsonish(call.get("arguments")))
        for call in calls
        if call.get("name")
    )
    if not counter:
        return False, None, None, 0
    (name, arguments_text), count = counter.most_common(1)[0]
    arguments = next(
        (
            call.get("arguments")
            for call in calls
            if call.get("name") == name
            and _jsonish(call.get("arguments")) == arguments_text
        ),
        None,
    )
    return count >= 3, name, arguments, count


def _primary_mode(
    *,
    sim: dict,
    task: dict | None,
    calls: list[dict],
    errors: list[str],
    secondary: set[str],
) -> str:
    """Choose one primary failure mode for a simulation."""
    reward_info = sim.get("reward_info")
    reward = (reward_info or {}).get("reward")
    termination_reason = sim.get("termination_reason") or ""
    action_checks = _action_checks(reward_info)
    read_failed, write_failed = _failed_checks_by_type(action_checks)

    if reward == 1.0:
        return "success"
    if termination_reason == "infrastructure_error" or reward is None:
        return "non_agent_infrastructure"

    repeated_error, repeated_name, repeated_arguments, _ = _repeated_tool_error(
        calls, errors
    )
    if (
        repeated_error
        and repeated_name in _LOOKUP_TOOL_NAMES
        and _contains_placeholder(repeated_arguments)
    ):
        return "credential_or_identifier_hallucination"
    if repeated_error:
        return "tool_error_loop"
    if _lookup_non_ascii_failure(calls, errors):
        return "translated_identifier_lookup_failure"

    actual_names = _actual_action_names(calls)
    expected_user_names = _expected_action_names(task, action_checks, "user")
    expected_assistant_names = _expected_action_names(task, action_checks, "assistant")

    missing_user = expected_user_names - actual_names
    missing_assistant = expected_assistant_names - actual_names
    missing_writes = {
        (check.get("action") or {}).get("name")
        for check in write_failed
        if (check.get("action") or {}).get("name") not in actual_names
    }
    matched_reads = [
        check
        for check in action_checks
        if check.get("tool_type") == "read" and check.get("action_match")
    ]

    if missing_user & _USER_DEVICE_ACTIONS:
        return "missing_user_device_instruction"
    if missing_assistant or missing_writes:
        if _has_refusal(sim.get("messages") or []) and matched_reads:
            return "premature_refusal_or_policy_misread"
        return "missing_required_write"
    if write_failed:
        return "wrong_write_arguments_or_state"
    if read_failed:
        read_names = {
            (check.get("action") or {}).get("name")
            for check in read_failed
            if (check.get("action") or {}).get("name")
        }
        if read_names & actual_names:
            return "wrong_read_arguments"
        return "missing_required_read"
    if termination_reason == "too_many_errors":
        return "dialogue_or_action_loop"
    if termination_reason == "max_steps":
        return "max_steps_or_dialogue_loop"
    if action_checks or termination_reason == "user_stop":
        return "non_action_assertion_failure"
    if not calls:
        return "no_tool_progress"
    if "language_drift" in secondary:
        return "language_drift"
    return "unclassified_failure"


def _secondary_modes(
    sim: dict,
    task: dict | None,
    calls: list[dict],
    errors: list[str],
) -> set[str]:
    """Return non-exclusive failure flags."""
    reward_info = sim.get("reward_info")
    action_checks = _action_checks(reward_info)
    read_failed, write_failed = _failed_checks_by_type(action_checks)
    secondary: set[str] = set()

    language_score = _stored_language_score(reward_info)
    if language_score is not None and language_score < 0.95:
        secondary.add("language_drift")

    if errors:
        secondary.add("tool_errors")
    if _lookup_non_ascii_failure(calls, errors):
        secondary.add("translated_identifier_lookup_failure")
    if any(_contains_placeholder(call.get("arguments")) for call in calls):
        secondary.add("placeholder_identifier")
    if any(
        call.get("name") in _LOOKUP_TOOL_NAMES
        and _contains_placeholder(call.get("arguments"))
        for call in calls
    ):
        secondary.add("placeholder_lookup")
    repeated_error, _, _, repeated_count = _repeated_tool_error(calls, errors)
    if repeated_error:
        secondary.add(f"repeated_tool_error_x{repeated_count}")

    for msg in sim.get("messages") or []:
        tool_calls = msg.get("tool_calls") or []
        if msg.get("role") == "assistant" and len(tool_calls) > 1:
            secondary.add("assistant_multi_tool_call")
            break

    assistant_text = _assistant_text(sim.get("messages") or [])
    if assistant_text.lstrip().startswith(("{", "[")):
        secondary.add("json_wrapped_response")
    if _has_refusal(sim.get("messages") or []):
        secondary.add("refusal_or_policy_language")

    expected_user_names = _expected_action_names(task, action_checks, "user")
    actual_names = _actual_action_names(calls)
    if (
        expected_user_names & _USER_DEVICE_ACTIONS
        and expected_user_names - actual_names
    ):
        secondary.add("missing_user_device_instruction")

    if read_failed:
        secondary.add("read_check_failed")
    if write_failed:
        secondary.add("write_check_failed")
    if action_checks and not read_failed and not write_failed:
        reward = (sim.get("reward_info") or {}).get("reward")
        if reward == 0.0:
            secondary.add("non_action_assertion_failure")

    return secondary


def _short_example(sim: dict, calls: list[dict], errors: list[str]) -> str:
    """Build a compact human-readable example for a CSV row."""
    messages = sim.get("messages") or []
    first_user = next(
        (
            (msg.get("content") or "").replace("\n", " ")
            for msg in messages
            if msg.get("role") == "user"
        ),
        "",
    )
    first_calls = ", ".join(
        f"{call.get('name')}({_jsonish(call.get('arguments'))})" for call in calls[:3]
    )
    first_error = errors[0].replace("\n", " ") if errors else ""
    parts = []
    if first_user:
        parts.append(f"user={first_user[:180]}")
    if first_calls:
        parts.append(f"calls={first_calls[:240]}")
    if first_error:
        parts.append(f"error={first_error[:180]}")
    return " | ".join(parts)


def analyze(results_json: Path) -> list[dict]:
    """Classify all simulations in a results file.

    Args:
        results_json: Path to a SEA-Tau results.json file.

    Returns:
        Per-simulation classification rows.
    """
    info, sims = load_simulations(results_json)
    raw = json.loads(results_json.read_text())
    tasks = _tasks_by_id(raw.get("tasks") or [])
    run_name = results_json.parent.name
    lang_id = info.get("lang_id", "")
    domain = (info.get("environment_info") or {}).get("domain_name", "")
    agent_llm = _model_name((info.get("agent_info") or {}).get("llm"))
    user_llm = _model_name((info.get("user_info") or {}).get("llm"))
    seatau_info = info.get("seatau_info") or {}
    experiment = seatau_info.get("experiment_name", "")

    rows: list[dict] = []
    for sim in sims:
        calls = _tool_calls(sim.get("messages") or [])
        errors = _tool_errors(sim.get("messages") or [])
        task = tasks.get(str(sim.get("task_id")))
        secondary = _secondary_modes(sim, task, calls, errors)
        primary = _primary_mode(
            sim=sim,
            task=task,
            calls=calls,
            errors=errors,
            secondary=secondary,
        )
        reward_info = sim.get("reward_info")
        action_checks = _action_checks(reward_info)
        read_failed, write_failed = _failed_checks_by_type(action_checks)
        expected_actions = _task_actions(task)

        rows.append(
            {
                "run": run_name,
                "experiment": experiment,
                "domain": domain,
                "lang": lang_id,
                "agent_llm": agent_llm,
                "user_llm": user_llm,
                "task_id": sim.get("task_id"),
                "trial": sim.get("trial"),
                "reward": (reward_info or {}).get("reward"),
                "termination_reason": sim.get("termination_reason"),
                "primary_failure_mode": primary,
                "secondary_failure_modes": ";".join(sorted(secondary)),
                "tool_call_count": len(calls),
                "tool_error_count": len(errors),
                "expected_action_count": len(expected_actions),
                "action_check_count": len(action_checks),
                "read_failed_count": len(read_failed),
                "write_failed_count": len(write_failed),
                "agent_language_score": _stored_language_score(reward_info),
                "example": _short_example(sim, calls, errors),
            }
        )
    return rows


def _pct(numerator: int, denominator: int) -> str:
    """Format a percentage with one decimal place."""
    if denominator == 0:
        return "0.0"
    return f"{numerator / denominator * 100:.1f}"


def _mode_names(rows: list[dict]) -> list[str]:
    """Return stable mode names present in rows."""
    present = {str(row["primary_failure_mode"]) for row in rows}
    ordered = [mode for mode in _PRIMARY_MODE_ORDER if mode in present]
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def aggregate_rows(rows: list[dict], group_fields: tuple[str, ...]) -> list[dict]:
    """Aggregate per-simulation rows by one or more fields.

    Args:
        rows: Per-simulation rows from :func:`analyze`.
        group_fields: Field names to group by.

    Returns:
        Wide table rows with total counts, rates, and primary mode counts.
    """
    mode_names = _mode_names(rows)
    grouped: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in group_fields)
        grouped[key].append(row)

    out: list[dict] = []
    for key, group_rows in sorted(grouped.items()):
        counts = Counter(str(row["primary_failure_mode"]) for row in group_rows)
        total = len(group_rows)
        success = counts.get("success", 0)
        infra = counts.get("non_agent_infrastructure", 0)
        agent_failures = total - success - infra

        summary = {field: value for field, value in zip(group_fields, key)}
        summary.update(
            {
                "total_simulations": total,
                "success_count": success,
                "success_rate": _pct(success, total),
                "non_agent_infrastructure_count": infra,
                "non_agent_infrastructure_rate": _pct(infra, total),
                "agent_failure_count": agent_failures,
                "agent_failure_rate": _pct(agent_failures, total),
            }
        )
        for mode in mode_names:
            count = counts.get(mode, 0)
            summary[f"{mode}_count"] = count
            summary[f"{mode}_rate"] = _pct(count, total)
            if mode not in {"success", "non_agent_infrastructure"}:
                summary[f"{mode}_share_of_agent_failures"] = _pct(count, agent_failures)
        out.append(summary)
    return out


def failure_mode_long_rows(
    rows: list[dict], group_name: str, group_fields: tuple[str, ...]
) -> list[dict]:
    """Build long-form primary-mode counts for one group definition."""
    grouped: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in group_fields)
        grouped[key].append(row)

    out: list[dict] = []
    for key, group_rows in sorted(grouped.items()):
        counts = Counter(str(row["primary_failure_mode"]) for row in group_rows)
        total = len(group_rows)
        success = counts.get("success", 0)
        infra = counts.get("non_agent_infrastructure", 0)
        agent_failures = total - success - infra
        group_values = {field: value for field, value in zip(group_fields, key)}
        for mode in _mode_names(group_rows):
            count = counts.get(mode, 0)
            out.append(
                {
                    "group": group_name,
                    "group_value": " / ".join(key),
                    **group_values,
                    "primary_failure_mode": mode,
                    "count": count,
                    "pct_all": _pct(count, total),
                    "pct_agent_failures": (
                        ""
                        if mode in {"success", "non_agent_infrastructure"}
                        else _pct(count, agent_failures)
                    ),
                    "total_simulations": total,
                    "agent_failure_count": agent_failures,
                }
            )
    return out


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write rows to CSV, preserving first-row field order."""
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


def write_summary_tables(rows: list[dict], summary_dir: Path) -> list[Path]:
    """Write reusable aggregate tables by domain, language, agent, and combos."""
    written: list[Path] = []
    for name, group_fields in _SUMMARY_GROUPS.items():
        path = summary_dir / f"failure_modes_{name}.csv"
        _write_csv(path, aggregate_rows(rows, group_fields))
        written.append(path)

    long_rows: list[dict] = []
    for name, group_fields in _SUMMARY_GROUPS.items():
        long_rows.extend(failure_mode_long_rows(rows, name, group_fields))
    long_path = summary_dir / "failure_modes_by_group_long.csv"
    _write_csv(long_path, long_rows)
    written.append(long_path)
    return written


def _parse_float(value: str | None) -> float | None:
    """Parse a float from a CSV field."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def paths_from_experiments_csv(
    experiments_csv: Path,
    simulations_root: Path,
    max_pass_hat: float | None = None,
    progress: set[str] | None = None,
) -> list[Path]:
    """Resolve tracker rows to existing results.json paths.

    Args:
        experiments_csv: Experiment tracker CSV.
        simulations_root: Directory containing simulation run directories.
        max_pass_hat: If set, include only rows where any `pass_hat_*` value is
            below this threshold.
        progress: If set, include only rows whose `progress` value is present.

    Returns:
        De-duplicated list of existing results.json paths.
    """
    paths: list[Path] = []
    seen: set[Path] = set()
    with experiments_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if progress and row.get("progress", "") not in progress:
                continue
            source = row.get("simulation_source")
            if not source:
                continue
            if max_pass_hat is not None:
                pass_hats = [
                    _parse_float(row.get(field))
                    for field in ("pass_hat_1", "pass_hat_2", "pass_hat_3")
                ]
                pass_hats = [value for value in pass_hats if value is not None]
                if not pass_hats or min(pass_hats) >= max_pass_hat:
                    continue
            path = simulations_root / source / "results.json"
            if path.exists() and path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def _print_summary(rows: list[dict], examples: int) -> None:
    """Print run-level summaries."""
    by_run: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_run[row["run"]].append(row)

    for run, run_rows in by_run.items():
        n = len(run_rows)
        failed = [row for row in run_rows if row["primary_failure_mode"] != "success"]
        print(f"\n{'=' * 72}")
        print(f"Run : {run}")
        print(
            f"Lang: {run_rows[0]['lang']}  Domain: {run_rows[0]['domain']}  "
            f"Simulations: {n}  Failures: {len(failed)}"
        )

        primary_counts = Counter(row["primary_failure_mode"] for row in run_rows)
        print(f"\n{'Primary failure mode':<42} {'Count':>6} {'%':>6}")
        print("-" * 58)
        for mode, count in primary_counts.most_common():
            print(f"{mode:<42} {count:>6} {count / n * 100:>5.1f}%")

        secondary_counts: Counter[str] = Counter()
        for row in run_rows:
            for mode in str(row["secondary_failure_modes"]).split(";"):
                if mode:
                    secondary_counts[mode] += 1
        if secondary_counts:
            print(f"\n{'Secondary flag':<42} {'Count':>6} {'%':>6}")
            print("-" * 58)
            for mode, count in secondary_counts.most_common(10):
                print(f"{mode:<42} {count:>6} {count / n * 100:>5.1f}%")

        if examples <= 0:
            continue
        print("\nExamples:")
        by_mode: dict[str, list[dict]] = defaultdict(list)
        for row in failed:
            by_mode[row["primary_failure_mode"]].append(row)
        for mode, mode_rows in sorted(by_mode.items()):
            print(f"  {mode}:")
            for row in mode_rows[:examples]:
                print(
                    f"    task={row['task_id']} trial={row['trial']} "
                    f"term={row['termination_reason']} :: {row['example'][:260]}"
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
        "--max-pass-hat",
        type=float,
        help="With --experiments-csv, include only rows with any pass_hat below this threshold",
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
        "--output", type=Path, help="Write per-simulation CSV to this path"
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        help=(
            "Write aggregate CSV tables by domain, language, agent, run, and "
            "their combinations to this directory"
        ),
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=0,
        help="Print this many compact examples per primary failure mode",
    )
    args = parser.parse_args()

    paths = list(args.paths)
    if args.experiments_csv:
        paths.extend(
            paths_from_experiments_csv(
                args.experiments_csv,
                args.simulations_root,
                max_pass_hat=args.max_pass_hat,
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

    all_rows: list[dict] = []
    for results_json in results_jsons:
        try:
            all_rows.extend(analyze(results_json))
        except Exception as exc:
            print(f"ERROR {results_json}: {exc}")

    if not all_rows:
        print("No simulations found.")
        return

    _print_summary(all_rows, examples=args.examples)

    if args.output:
        _write_csv(args.output, all_rows)
        print(f"\nWrote {len(all_rows)} rows -> {args.output}")

    if args.summary_dir:
        written = write_summary_tables(all_rows, args.summary_dir)
        print(f"\nWrote {len(written)} summary tables -> {args.summary_dir}")


if __name__ == "__main__":
    main()
