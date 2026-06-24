"""Bidirectional address parsing for annotation workbook rows.

Each workbook row carries an `address` like:

    policy.md::001_retail-agent-policy_1   (markdown section_id)
    db.json::products/9523456873/name      (JSON tuple-path)
    db.toml::plans/0/name                  (TOML tuple-path)
    tools.py::cancel_pending_order         (python function name)
    data_model.py::models/User/fields/name/description (python schema tuple-path)

This module is the single source of truth for the workbook's address
taxonomy. Both the exporter and importer share these helpers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Address:
    """Parsed workbook row address."""

    filename: str  # e.g., "policy.md", "db.json", "tools.py"
    body: str  # everything after `::` (section_id / path / function_name)


def parse(addr: str) -> Address:
    """Split `<filename>::<body>` into an Address."""
    if "::" not in addr:
        return Address(filename="", body=addr)
    fn, rest = addr.split("::", 1)
    return Address(filename=fn, body=rest)


def format(filename: str, body: str) -> str:
    """Render an address string. Inverse of :func:`parse`."""
    return f"{filename}::{body}"


def body_from_segment(address: Any) -> str:
    """Stringify a ``Segment.address`` (tuple, str, or SourceSpan) for the workbook.

    Tuples join with ``/`` (matches the JSON/TOML tuple-path convention).
    Strings pass through. Anything else is ``str()``-coerced.
    """
    if isinstance(address, tuple):
        return "/".join(address)
    return str(address)


def file_kind(path: Path | str) -> str:
    """Map a source file's extension to the extractor's ``kind`` literal."""
    suffix = Path(path).suffix.lstrip(".")
    return {"md": "markdown", "toml": "toml", "py": "python"}.get(suffix, "json")


def is_blank(value: object) -> bool:
    """True for None, NaN, or empty/whitespace strings (pandas-friendly)."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def take_final(row: dict, lang: str, *, allow_machine_fallback: bool = True) -> object:
    """Resolve the effective translation for one workbook row.

    Order of preference:
      1. ``name.{lang}.final`` (human-reviewed, definitive)
      2. ``name.{lang}`` (machine-translation fallback) — only when allowed

    Args:
        row: One DataFrame row as a mapping (e.g. ``df.iloc[i]``).
        lang: Target language code matching the workbook's column suffix.
        allow_machine_fallback: When False, return ``None`` if ``.final``
            is empty; the importer treats this as a per-row reject signal.

    Returns:
        The string to write, or ``None`` when ``.final`` is empty and
        ``allow_machine_fallback`` is False.
    """
    final = row.get(f"name.{lang}.final")
    if not is_blank(final):
        return final
    if allow_machine_fallback:
        return row.get(f"name.{lang}")
    return None
