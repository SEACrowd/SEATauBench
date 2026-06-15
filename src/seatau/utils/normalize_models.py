"""Model-name normalization helpers for SEA-Tau experiment tracking."""

from __future__ import annotations

from typing import Any

_CANONICAL_MODEL_NAMES = {
    "openrouter/moonshotai/kimi-k2.5": "azure/kimi-k2.5",
    "openrouter/qwen/qwen3-235b-a22b-2507": "Qwen3-235B-A22B-Instruct-2507",
    "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas": "Qwen3-235B-A22B-Instruct-2507",
    "Qwen3-235B-A22B-Instruct-2507-FP8": "Qwen3-235B-A22B-Instruct-2507-FP8",
    "Qwen3-235B-A22B-Instruct-2507": "Qwen3-235B-A22B-Instruct-2507",
}

_SHORT_MODEL_NAMES = {
    "openrouter/openai/gpt-5-mini": "gpt-5-mini",
    "openai/gpt-5-mini": "gpt-5-mini",
    "azure/gpt-5-mini": "gpt-5-mini",
    "azure/kimi-k2.5": "kimi-k2.5",
    "openrouter/moonshotai/kimi-k2.5": "kimi-k2.5",
    "nebius/moonshotai/Kimi-K2.5": "kimi-k2.5",
    "openrouter/qwen/qwen3.6-35b-a3b": "qwen3.6-35b-a3b",
    "vertex_ai/qwen/qwen3-235b-a22b-instruct-2507-maas": "qwen3-235b",
    "together_ai/Qwen/Qwen3-235B-A22B-Instruct-2507-tput": "qwen3-235b",
}


def canonical_model_name(model: Any) -> str:
    """Return the experiment-tracker model label for a raw metadata value."""
    if not isinstance(model, str):
        return ""

    normalized = (
        model.rsplit("/", maxsplit=1)[-1] if model.startswith("/project/") else model
    )
    return _CANONICAL_MODEL_NAMES.get(normalized, normalized)


def short_model(model: str) -> str:
    """Normalize provider-prefixed model ids for plots."""
    if model in _SHORT_MODEL_NAMES:
        return _SHORT_MODEL_NAMES[model]
    if "Qwen3-235B" in model or "qwen3-235b" in model:
        return "qwen3-235b"
    return model
