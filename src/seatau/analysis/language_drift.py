"""Shared helpers for SEA-Tau language drift analysis."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paths import EXPERIMENTS_CSV, PROJECT_ROOT
from seatau.constants import get_language_code_by_display_name
from seatau.experiment_matrix import get_scenario_display_name, list_all_scenarios
from seatau.metrics.language_use import (
    infer_expected_language as infer_role_expected_language,
)

DEFAULT_EXPERIMENTS_CSV = EXPERIMENTS_CSV
LANGUAGE_CODE_BY_DISPLAY_NAME = get_language_code_by_display_name()

SCENARIO_ORDER = [
    scenario for scenario in list_all_scenarios() if scenario != "english"
]
SCENARIO_LABELS = {
    scenario: get_scenario_display_name(scenario) for scenario in list_all_scenarios()
}
LANGUAGE_CODE_BY_KEY = {
    display_name.lower(): code
    for display_name, code in LANGUAGE_CODE_BY_DISPLAY_NAME.items()
}
LANGUAGE_LABELS = {
    **{language: code.upper() for language, code in LANGUAGE_CODE_BY_KEY.items()},
    **{
        display_name: code.upper()
        for display_name, code in LANGUAGE_CODE_BY_DISPLAY_NAME.items()
    },
    **{
        mix: f"Mix {mix.rsplit('_', maxsplit=1)[-1]}"
        for mix in ("tool_mix_2", "tool_mix_3", "tool_mix_4", "tool_mix_5")
    },
}


@dataclass(frozen=True)
class ExperimentRow:
    """A row in `experiments_all.csv` with a concrete simulation source."""

    line_number: int
    scenario: str
    domain: str
    language: str
    agent_llm: str
    normalized_agent_llm: str
    simulation_source: Path


def read_experiment_rows(path: Path) -> list[ExperimentRow]:
    """Load experiment rows that have an identified simulation source."""

    rows: list[ExperimentRow] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            source = str(row.get("simulation_source") or "").strip()
            if not source:
                continue
            simulation_source = PROJECT_ROOT / source
            csv_scenario = str(row["scenario"])
            scenario = scenario_from_simulation_source(
                simulation_source, fallback=csv_scenario
            )
            rows.append(
                ExperimentRow(
                    line_number=line_number,
                    scenario=scenario,
                    domain=str(row["domain"]),
                    language=str(row["language_senario"]),
                    agent_llm=str(row["agent_llm"]),
                    normalized_agent_llm=str(row.get("normalized_agent_llm") or ""),
                    simulation_source=simulation_source,
                )
            )
    return rows


def scenario_from_simulation_source(path: Path | str, fallback: str = "") -> str:
    """Map a `data/simulations/<scenario>/...` path to its scenario id.

    Args:
        path: Simulation source directory or nested results path.
        fallback: Scenario id to use when the path does not follow the expected
            `data/simulations/<scenario>` layout.

    Returns:
        Canonical scenario id, such as `l2_interaction`.
    """

    parts = Path(path).parts
    for idx, part in enumerate(parts[:-1]):
        if part == "simulations" and idx + 1 < len(parts):
            scenario_folder = parts[idx + 1]
            if scenario_folder in SCENARIO_LABELS:
                return scenario_folder
            return fallback
    for part in parts:
        if part in SCENARIO_LABELS:
            return part
    return fallback


def infer_lang_id(info: dict[str, Any], language: str) -> str:
    """Read the stored language id, falling back to the CSV language label."""

    return str(
        info.get("lang_id")
        or ((info.get("seatau_info") or {}).get("run_language"))
        or LANGUAGE_CODE_BY_DISPLAY_NAME.get(language)
        or LANGUAGE_CODE_BY_KEY.get(language.lower())
        or language
    )


def infer_expected_language(scenario: str, lang_id: str) -> str:
    """Infer which natural language the speaker should use in this scenario."""
    return infer_role_expected_language(
        role="assistant",
        lang_id=lang_id,
        scenario=scenario,
    )


def is_likely_system_error(sim: dict[str, Any]) -> bool:
    """Flag infrastructure/system errors that should not drive behavior analysis."""

    term = str(sim.get("termination_reason", "")).lower()
    if term in {"infrastructure_error", "user_error"}:
        return True
    needles = (
        "insufficient credit",
        "insufficient_quota",
        "connection error",
        "api error",
        "apierror",
        "timeout",
        "timed out",
        "rate limit",
        "litellm",
        "contentpolicyviolation",
        "internal server error",
        "bad gateway",
        "service unavailable",
        "user simulator",
    )
    parts = [term]
    for message in sim.get("messages") or []:
        content = message.get("content")
        if isinstance(content, str):
            parts.append(content[:1000])
        error = message.get("error")
        if error not in (None, False):
            parts.append(str(error)[:1000])
    return any(needle in "\n".join(parts).lower() for needle in needles)


def should_exclude_first_agent_turn(
    *, scenario: str, role: str, is_first_agent_text_turn: bool
) -> bool:
    """Return whether a text turn is excluded from agent language correctness."""

    return (
        scenario == "l2_interaction"
        and role in {"assistant", "agent"}
        and is_first_agent_text_turn
    )


def text_turns(messages: list[dict[str, Any]], role: str) -> list[tuple[int, str]]:
    """Extract substantial text turns for a role."""

    turns: list[tuple[int, str]] = []
    for idx, message in enumerate(messages):
        if message.get("role") != role:
            continue
        content = str(message.get("content") or "").strip()
        if len(content) < 5 or (content.startswith("###") and content.endswith("###")):
            continue
        turns.append((int(message.get("turn_idx") or idx), content))
    return turns
