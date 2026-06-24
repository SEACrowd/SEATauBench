"""SEA-TAU experiment matrix helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import yaml

from seatau.paths import EXPERIMENTS_YAML

ExperimentAssetMode = Literal["original", "translated", "localized"]


@dataclass(frozen=True)
class ExperimentPreset:
    """Resolved SEA-TAU experiment preset."""

    name: str
    asset_mode: ExperimentAssetMode
    lang_components: tuple[str, ...]
    mixed_tools: bool
    default_mixed_config: str | None = None


@lru_cache(maxsize=1)
def _load_matrix() -> dict:
    """Load and cache the experiment matrix YAML."""
    return yaml.safe_load(EXPERIMENTS_YAML.read_text(encoding="utf-8"))


def resolve_experiment_name(experiment: str) -> str:
    """Resolve an experiment alias to its canonical name."""
    matrix = _load_matrix()
    aliases = matrix.get("aliases", {})
    return aliases.get(experiment, experiment)


def get_experiment_preset(experiment: str) -> ExperimentPreset:
    """Return the canonical preset definition for an experiment."""
    matrix = _load_matrix()
    resolved = resolve_experiment_name(experiment)
    experiments = matrix.get("experiments", {})
    if resolved not in experiments:
        raise ValueError(f"Unknown experiment: {experiment}")

    data = experiments[resolved]
    return ExperimentPreset(
        name=resolved,
        asset_mode=data.get("asset_mode", "original"),
        lang_components=tuple(data.get("lang_components", [])),
        mixed_tools=bool(data.get("mixed_tools", False)),
        default_mixed_config=data.get("default_mixed_config"),
    )


def get_experiment_lang_components(experiment: str) -> tuple[str, ...]:
    """Return the runtime language components for an experiment."""
    return get_experiment_preset(experiment).lang_components


def get_experiment_asset_mode(experiment: str) -> ExperimentAssetMode:
    """Return the artifact mode for an experiment."""
    return get_experiment_preset(experiment).asset_mode


def experiment_uses_mixed_tools(experiment: str) -> bool:
    """Return whether an experiment uses mixed-language tool docs."""
    return get_experiment_preset(experiment).mixed_tools


def get_experiment_default_mixed_config(experiment: str) -> str | None:
    """Return the default mixed-tools config for an experiment, if any."""
    return get_experiment_preset(experiment).default_mixed_config


def list_all_experiments() -> list[str]:
    """Return the experiment names to fan out under ``--all-experiments``."""
    return list(_load_matrix().get("all_experiments", []))


def list_supported_domains() -> list[str]:
    """Return SEA-TAU's supported tau2 domains."""
    return list(_load_matrix().get("supported_domains", []))


def is_known_experiment(experiment: str) -> bool:
    """Return True if ``experiment`` resolves to a defined preset."""
    matrix = _load_matrix()
    resolved = resolve_experiment_name(experiment)
    return resolved in matrix.get("experiments", {})


def list_known_experiments() -> list[str]:
    """Return all defined preset names (canonical, no aliases)."""
    return sorted(_load_matrix().get("experiments", {}).keys())


def list_experiment_aliases() -> dict[str, str]:
    """Return the alias → canonical mapping."""
    return dict(_load_matrix().get("aliases", {}))
