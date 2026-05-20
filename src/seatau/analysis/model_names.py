"""Model-name normalization for experiment tracking and analysis."""

from __future__ import annotations

from typing import Any

_CANONICAL_MODEL_NAMES = {
    "openrouter/moonshotai/kimi-k2.5": "azure/kimi-k2.5",
    "openrouter/qwen/qwen3-235b-a22b-2507": "Qwen3-235B-A22B-Instruct-2507-FP8",
    "qwen3-235b-a22b-2507": "Qwen3-235B-A22B-Instruct-2507-FP8",
    "Qwen3-235B-A22B-Instruct-2507-FP8": "Qwen3-235B-A22B-Instruct-2507-FP8",
}


def canonical_model_name(model: Any) -> str:
    """Return the experiment-tracker model label for a raw metadata value."""
    if not isinstance(model, str):
        return ""

    normalized = (
        model.rsplit("/", maxsplit=1)[-1] if model.startswith("/project/") else model
    )
    return _CANONICAL_MODEL_NAMES.get(normalized, normalized)
