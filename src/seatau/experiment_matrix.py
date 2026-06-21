"""SEA-TAU scenario matrix helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import yaml

from seatau.paths import SCENARIOS_MAP

ScenarioAssetMode = Literal["original", "translated"]


@dataclass(frozen=True)
class ScenarioPreset:
    """Resolved SEA-TAU scenario preset."""

    scenario: str
    display_name: str
    asset_mode: ScenarioAssetMode
    lang_components: tuple[str, ...]
    mixed_tools: bool
    default_mixed_config: str | None = None


@lru_cache(maxsize=1)
def _load_matrix() -> dict:
    """Load and cache the scenario matrix YAML."""
    return yaml.safe_load(SCENARIOS_MAP.read_text(encoding="utf-8"))


def get_scenario_preset(scenario: str) -> ScenarioPreset:
    """Return the canonical preset definition for a scenario."""
    matrix = _load_matrix()
    scenarios = matrix.get("scenarios", {})
    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario}")

    data = scenarios[scenario]
    return ScenarioPreset(
        scenario=scenario,
        display_name=data.get("display_name", scenario),
        asset_mode=data.get("asset_mode", "original"),
        lang_components=tuple(data.get("lang_components", [])),
        mixed_tools=bool(data.get("mixed_tools", False)),
        default_mixed_config=data.get("default_mixed_config"),
    )


def get_scenario_display_name(scenario: str) -> str:
    """Return the display name for a canonical scenario."""
    return get_scenario_preset(scenario).display_name


def get_scenario_lang_components(scenario: str) -> tuple[str, ...]:
    """Return the runtime language components for a scenario."""
    return get_scenario_preset(scenario).lang_components


def get_scenario_asset_mode(scenario: str) -> ScenarioAssetMode:
    """Return the artifact mode for a scenario."""
    return get_scenario_preset(scenario).asset_mode


def scenario_uses_mixed_tools(scenario: str) -> bool:
    """Return whether a scenario uses mixed-language tool docs."""
    return get_scenario_preset(scenario).mixed_tools


def get_scenario_default_mixed_config(scenario: str) -> str | None:
    """Return the default mixed-tools config for a scenario, if any."""
    return get_scenario_preset(scenario).default_mixed_config


def list_all_scenarios() -> list[str]:
    """Return the scenario names to fan out for a full SEA-TAU run."""
    matrix = _load_matrix()
    return list(matrix.get("all_scenarios", matrix.get("scenarios", {}).keys()))


def list_supported_domains() -> list[str]:
    """Return SEA-TAU's supported tau2 domains."""
    return list(_load_matrix().get("supported_domains", []))
