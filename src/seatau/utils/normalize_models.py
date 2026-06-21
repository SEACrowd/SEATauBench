"""Model-name normalization helpers for SEA-Tau experiment tracking."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

NORMALIZED_MODEL_NAMES = ("gpt-5-mini", "kimi-k2.5", "qwen-3-235b-it")

_CANONICAL_MODEL_NAMES = {
    "openrouter/moonshotai/kimi-k2.5": "openrouter/moonshotai/kimi-k2.5",
    "openrouter/qwen/qwen3-235b-a22b-2507": "openrouter/qwen/qwen3-235b-a22b-2507",
    "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas": "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas",
    "Qwen3-235B-A22B-Instruct-2507-FP8": "Qwen3-235B-A22B-Instruct-2507-FP8",
    "Qwen3-235B-A22B-Instruct-2507": "Qwen3-235B-A22B-Instruct-2507",
}

_SHORT_MODEL_NAMES = {
    "openrouter/openai/gpt-5-mini": "gpt-5-mini",
    "openai/gpt-5-mini": "gpt-5-mini",
    "azure/gpt-5-mini": "gpt-5-mini",
    "gpt-5-mini": "gpt-5-mini",
    "azure/kimi-k2.5": "kimi-k2.5",
    "openai/moonshotai/Kimi-K2.5": "kimi-k2.5",
    "openrouter/moonshotai/kimi-k2.5": "kimi-k2.5",
    "openrouter/moonshotai/Kimi-K2.5": "kimi-k2.5",
    "nebius/moonshotai/Kimi-K2.5": "kimi-k2.5",
    "gmi/moonshotai/Kimi-K2.5": "kimi-k2.5",
    "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas": "qwen-3-235b-it",
    "openrouter/qwen/qwen3-235b-a22b-2507": "qwen-3-235b-it",
    "together_ai/Qwen/Qwen3-235B-A22B-Instruct-2507-tput": "qwen-3-235b-it",
    "Qwen3-235B-A22B-Instruct-2507": "qwen-3-235b-it",
    "Qwen3-235B-A22B-Instruct-2507-FP8": "qwen-3-235b-it",
}


def _model_tail(model: str) -> str:
    """Return the model-name segment from provider/developer/model IDs."""
    if "//project/" in model:
        return model.rsplit("/", maxsplit=1)[-1]
    if model.startswith("/project/"):
        return model.rsplit("/", maxsplit=1)[-1]
    return model.rsplit("/", maxsplit=1)[-1]


def canonical_model_name(model: Any) -> str:
    """Return the experiment-tracker model label for a raw metadata value."""
    if not isinstance(model, str):
        return ""

    normalized = (
        model.rsplit("/", maxsplit=1)[-1] if model.startswith("/project/") else model
    )
    return _CANONICAL_MODEL_NAMES.get(normalized, normalized)


def normalize_model_name(model: Any) -> str:
    """Normalize an observed LLM value to the supported SEA-Tau model options."""
    if not isinstance(model, str):
        return ""

    model = model.strip()
    if model in _SHORT_MODEL_NAMES:
        return _SHORT_MODEL_NAMES[model]

    tail = _model_tail(model).lower()
    if "gpt-5-mini" in tail:
        return "gpt-5-mini"
    if "kimi-k2.5" in tail:
        return "kimi-k2.5"
    if "qwen3-235b" in tail or "qwen-3-235b" in tail:
        return "qwen-3-235b-it"
    return ""


def short_model(model: str) -> str:
    """Normalize provider-prefixed model ids for plots."""
    return normalize_model_name(model) or model


def iter_observed_llms(simulations_dir: Path) -> Iterable[str]:
    """Yield raw agent and user LLM values observed in simulation results."""
    for results_path in simulations_dir.glob("**/results.json"):
        with results_path.open(encoding="utf-8") as f:
            info = json.load(f).get("info") or {}
        for key in ("agent_info", "user_simulator_info"):
            llm = (info.get(key) or {}).get("llm")
            if isinstance(llm, str) and llm:
                yield llm


def observed_model_normalizations(simulations_dir: Path) -> dict[str, str]:
    """Return observed raw LLM values mapped to supported normalized names."""
    return {
        model: normalize_model_name(model)
        for model in sorted(set(iter_observed_llms(simulations_dir)))
    }
