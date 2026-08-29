"""Translation toolkit for multilingual Tau2 domain assets.

Module structure:
- ``loader``: Docstring injection (patch/restore) for eval time
- ``language``: Language registry and component resolution
- ``pipeline``: Translation pipeline orchestration
- ``extractors``: File discovery and AST extraction
- ``litellm_translator``: LLM-based translation client
- ``config``: Domain-level constants and protected terms
- ``paths``: Centralized path utilities
- ``protect``: Placeholder masking/unmasking
- ``runtime_localization``: Runtime localization for schema artifacts

For mixed-language tools experiments, see :mod:`seatau.l2_tools_mix`.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    # Pipeline
    "run_pipeline",
    # Loader (docstring injection)
    "load_docstrings_json",
    "load_schema_json",
    "localized_toolkit",
    "patch_toolkit_docstrings",
    "restore_toolkit_docstrings",
    # Language utilities
    "translated_asset_path",
]


def __getattr__(name: str) -> Any:
    """Lazily import public helpers to avoid package import cycles."""
    if name == "run_pipeline":
        from seatau.translation.pipeline import run_pipeline

        return run_pipeline

    if name == "translated_asset_path":
        from seatau.translation.language import translated_asset_path

        return translated_asset_path

    if name in {
        "load_docstrings_json",
        "load_schema_json",
        "localized_toolkit",
        "patch_toolkit_docstrings",
        "restore_toolkit_docstrings",
    }:
        from seatau.translation.loader import (
            load_docstrings_json,
            load_schema_json,
            localized_toolkit,
            patch_toolkit_docstrings,
            restore_toolkit_docstrings,
        )

        return {
            "load_docstrings_json": load_docstrings_json,
            "load_schema_json": load_schema_json,
            "localized_toolkit": localized_toolkit,
            "patch_toolkit_docstrings": patch_toolkit_docstrings,
            "restore_toolkit_docstrings": restore_toolkit_docstrings,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
