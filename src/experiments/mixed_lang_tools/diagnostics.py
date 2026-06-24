"""Diagnostics for mixed-language tool partitions and result summaries."""

from __future__ import annotations

import importlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from experiments.mixed_lang_tools.partition import (
    load_mixed_docstrings,
    load_mixed_tools_config,
    load_tool_groups,
)


def get_agent_visible_tool_names(domain: str) -> list[str]:
    """Return the agent-visible tool names for a domain."""
    try:
        module = importlib.import_module(f"tau2.domains.{domain}.environment")
        environment = module.get_environment()
        return sorted(environment.tools.get_tools().keys())
    except ModuleNotFoundError:
        src_tools_path = (
            Path(__file__).resolve().parents[2]
            / "tau2"
            / "domains"
            / domain
            / "tools.py"
        )
        return extract_agent_visible_tool_names(src_tools_path)


def extract_agent_visible_tool_names(tools_py_path: Path) -> list[str]:
    """Extract non-discoverable tool method names without importing tau2."""
    import ast

    def decorator_name(decorator: ast.expr) -> str | None:
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Call):
            return decorator_name(decorator.func)
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        return None

    source = tools_py_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorator_names = {
            name
            for decorator in node.decorator_list
            if (name := decorator_name(decorator)) is not None
        }
        if (
            "is_tool" in decorator_names
            and "is_discoverable_tool" not in decorator_names
        ):
            names.append(node.name)
    return sorted(names)


def diagnose_mixed_tools_config(
    *,
    domain: str,
    config_name: str,
    tool_names: list[str] | None = None,
    src_tools_path: Path | None = None,
) -> dict[str, Any]:
    """Build a realized mixed-tools diagnostic record for one config."""
    if tool_names is None:
        tool_names = get_agent_visible_tool_names(domain)
    if src_tools_path is None:
        src_tools_path = (
            Path(__file__).resolve().parents[2]
            / "tau2"
            / "domains"
            / domain
            / "tools.py"
        )

    config = load_mixed_tools_config(config_name)
    tool_groups = load_tool_groups(domain) if config.partitioning.group_mode else None
    docstrings, partition = load_mixed_docstrings(
        domain=domain,
        tool_names=tool_names,
        config=config,
        src_tools_path=src_tools_path,
    )

    assignments = {
        tool: assignment.lang
        for tool, assignment in sorted(partition.tool_assignments.items())
    }
    grouped_tools = sorted(
        {
            tool
            for tools in (tool_groups or {}).values()
            for tool in tools
            if tool in tool_names
        }
    )

    return {
        "domain": domain,
        "config_name": config.name,
        "languages": list(config.languages.codes),
        "weights": list(config.languages.weights),
        "seed": config.partitioning.seed,
        "partition_strategy": config.partitioning.partition_strategy,
        "tools_per_added_language": config.partitioning.tools_per_added_language,
        "group_mode_requested": config.partitioning.group_mode,
        "group_mode_used": bool(tool_groups),
        "group_count": len(tool_groups or {}),
        "grouped_tool_count": len(grouped_tools),
        "tool_count": len(tool_names),
        "docstring_count": len(docstrings),
        "missing_docstrings": sorted(set(tool_names) - set(docstrings)),
        "summary": {
            "total_tools": partition.summary.total_tools,
            "by_language": dict(sorted(partition.summary.by_language.items())),
            "by_group": partition.summary.by_group,
        },
        "tool_assignments": assignments,
        "group_assignments": partition.group_assignments,
    }


def diagnose_mixed_tools_configs(
    *,
    domain: str,
    config_names: list[str],
    tool_names: list[str] | None = None,
    src_tools_path: Path | None = None,
) -> dict[str, Any]:
    """Build diagnostics for several configs and compare adjacent partitions."""
    if tool_names is None:
        tool_names = get_agent_visible_tool_names(domain)

    configs = [
        diagnose_mixed_tools_config(
            domain=domain,
            config_name=config_name,
            tool_names=tool_names,
            src_tools_path=src_tools_path,
        )
        for config_name in config_names
    ]

    comparisons: list[dict[str, Any]] = []
    for previous, current in zip(configs, configs[1:]):
        previous_assignments = previous["tool_assignments"]
        current_assignments = current["tool_assignments"]
        new_languages = set(current["languages"]) - set(previous["languages"])
        changed = {
            tool: {
                "previous": previous_assignments[tool],
                "current": current_assignments[tool],
            }
            for tool in sorted(set(previous_assignments) & set(current_assignments))
            if previous_assignments[tool] != current_assignments[tool]
        }
        progressive_changes = {
            tool: change
            for tool, change in changed.items()
            if change["previous"] == previous["languages"][0]
            and change["current"] in new_languages
        }
        previous_non_english_changed = {
            tool: change
            for tool, change in changed.items()
            if change["previous"] != previous["languages"][0]
        }
        comparisons.append(
            {
                "previous_config": previous["config_name"],
                "current_config": current["config_name"],
                "changed_tool_count": len(changed),
                "unchanged_tool_count": len(previous_assignments) - len(changed),
                "is_nested_assignment": len(changed) == 0,
                "is_nested_progressive": changed == progressive_changes,
                "new_languages": sorted(new_languages),
                "previous_non_english_changed": previous_non_english_changed,
                "changed_tools": changed,
            }
        )

    return {
        "domain": domain,
        "configs": configs,
        "comparisons": comparisons,
    }


def load_results_payload(results_path: Path) -> dict[str, Any]:
    """Load monolithic or directory-format tau2 results."""
    data = json.loads(results_path.read_text(encoding="utf-8"))
    if data.get("simulations"):
        return data

    sims_dir = results_path.parent / "simulations"
    if sims_dir.is_dir():
        data["simulations"] = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(sims_dir.glob("*.json"))
        ]
    else:
        data["simulations"] = []
    return data


def find_results_files(results_dir: Path) -> list[Path]:
    """Find run-level results files below a results directory."""
    return [
        path
        for path in sorted(results_dir.rglob("results.json"))
        if path.parent.name != "simulations"
    ]


def _simulation_reward(simulation: dict[str, Any]) -> float:
    reward_info = simulation.get("reward_info") or {}
    reward = reward_info.get("reward", simulation.get("reward", 0.0))
    return float(reward or 0.0)


def summarize_mixed_results(results_dir: Path) -> dict[str, Any]:
    """Summarize mixed-tool result files by experiment and task."""
    runs: list[dict[str, Any]] = []
    task_scores: dict[str, dict[str, float]] = {}

    for results_path in find_results_files(results_dir):
        payload = load_results_payload(results_path)
        info = payload.get("info") or {}
        mixed_config = info.get("mixed_tools_config")
        if not mixed_config:
            continue

        experiment_name = info.get("experiment_name") or results_path.parent.name
        simulations = payload.get("simulations") or []
        rewards = [_simulation_reward(simulation) for simulation in simulations]
        by_task: dict[str, list[float]] = defaultdict(list)
        for simulation in simulations:
            by_task[str(simulation.get("task_id"))].append(
                _simulation_reward(simulation)
            )

        task_scores[experiment_name] = {
            task_id: sum(values) / len(values) for task_id, values in by_task.items()
        }
        runs.append(
            {
                "experiment_name": experiment_name,
                "mixed_tools_config": mixed_config,
                "results_path": str(results_path),
                "simulation_count": len(simulations),
                "unique_task_count": len(by_task),
                "trials": sorted(
                    {
                        simulation.get("trial")
                        for simulation in simulations
                        if simulation.get("trial") is not None
                    }
                ),
                "average_reward": sum(rewards) / len(rewards) if rewards else 0.0,
            }
        )

    runs.sort(key=lambda run: run["experiment_name"])
    return {
        "results_dir": str(results_dir),
        "runs": runs,
        "task_score_deltas": _task_score_deltas(task_scores),
    }


def _task_score_deltas(
    task_scores: dict[str, dict[str, float]],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Compute top task-level improvements relative to the first experiment."""
    if len(task_scores) < 2:
        return []

    baseline_name = sorted(task_scores)[0]
    baseline = task_scores[baseline_name]
    deltas: list[dict[str, Any]] = []
    for experiment_name in sorted(task_scores):
        if experiment_name == baseline_name:
            continue
        shared_tasks = sorted(set(baseline) & set(task_scores[experiment_name]))
        ranked = sorted(
            (
                {
                    "task_id": task_id,
                    "delta": task_scores[experiment_name][task_id] - baseline[task_id],
                    "baseline_score": baseline[task_id],
                    "experiment_score": task_scores[experiment_name][task_id],
                }
                for task_id in shared_tasks
            ),
            key=lambda row: row["delta"],
            reverse=True,
        )
        deltas.append(
            {
                "baseline_experiment": baseline_name,
                "experiment_name": experiment_name,
                "shared_task_count": len(shared_tasks),
                "top_improvements": ranked[:top_k],
            }
        )
    return deltas
