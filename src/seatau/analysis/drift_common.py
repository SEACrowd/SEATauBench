"""Shared helpers for SEA-Tau language drift analysis."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from seatau.experiment_matrix import get_scenario_display_name
from seatau.paths import EXPERIMENTS_CSV

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXPERIMENTS_CSV = EXPERIMENTS_CSV
DEFAULT_ANALYSES_DIR = PROJECT_ROOT / "data" / "analyses"

SCENARIO_ORDER = ["l2_tools", "l2_interaction", "l2_domain"]
FIGURE_SCENARIOS = ["l2_interaction", "l2_domain"]
SCENARIO_LABELS = {
    scenario: get_scenario_display_name(scenario)
    for scenario in ["english", "l2_tools", "l2_interaction", "l2_domain"]
}
LANGUAGE_ORDER = ["indonesian", "thai", "filipino", "vietnamese", "chinese"]
LANGUAGE_LABELS = {
    "indonesian": "ID",
    "thai": "TH",
    "filipino": "TL",
    "vietnamese": "VI",
    "chinese": "ZH",
    "english": "EN",
    "tool_mix_2": "Mix 2",
    "tool_mix_3": "Mix 3",
    "tool_mix_4": "Mix 4",
    "tool_mix_5": "Mix 5",
}
LANGUAGE_CODE_BY_NAME = {
    "english": "en",
    "indonesian": "id",
    "thai": "th",
    "filipino": "tl",
    "vietnamese": "vi",
    "chinese": "zh",
    "tool_mix_2": "en",
    "tool_mix_3": "en",
    "tool_mix_4": "en",
    "tool_mix_5": "en",
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
        or LANGUAGE_CODE_BY_NAME.get(language)
        or language
    )


def infer_expected_language(scenario: str, lang_id: str) -> str:
    """Infer which natural language the speaker should use in this scenario."""

    if scenario in {"english", "l2_tools"}:
        return "en"
    if scenario in {"l2_interaction", "l2_domain"}:
        return normalize_lang_code(lang_id)
    return "en"


def normalize_lang_code(code: str) -> str:
    """Normalize fastText and ISO language labels to the project code set."""

    normalized = code.replace("__label__", "").strip().lower()
    aliases = {
        "eng": "en",
        "ind": "id",
        "tgl": "tl",
        "tha": "th",
        "vie": "vi",
        "zho": "zh",
        "cmn": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh",
    }
    if normalized in aliases:
        return aliases[normalized]
    if "-" in normalized:
        return normalized.split("-", 1)[0]
    return normalized


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
