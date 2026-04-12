"""Translation toolkit for multilingual Tau2 domain assets."""

from __future__ import annotations

from typing import Any

__all__ = [
    "run_pipeline",
    "load_docstrings_json",
    "localized_toolkit",
    "patch_toolkit_docstrings",
    "restore_toolkit_docstrings",
    "translated_asset_path",
]


def __getattr__(name: str) -> Any:
    """Lazily import public helpers to avoid package import cycles."""
    if name == "run_pipeline":
        from translation.pipeline import run_pipeline

        return run_pipeline
    if name == "translated_asset_path":
        from translation.language import translated_asset_path

        return translated_asset_path
    if name in {
        "load_docstrings_json",
        "localized_toolkit",
        "patch_toolkit_docstrings",
        "restore_toolkit_docstrings",
    }:
        from translation.loader import (
            load_docstrings_json,
            localized_toolkit,
            patch_toolkit_docstrings,
            restore_toolkit_docstrings,
        )

        return {
            "load_docstrings_json": load_docstrings_json,
            "localized_toolkit": localized_toolkit,
            "patch_toolkit_docstrings": patch_toolkit_docstrings,
            "restore_toolkit_docstrings": restore_toolkit_docstrings,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
