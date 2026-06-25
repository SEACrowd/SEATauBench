"""AST-based docstring extraction from ``tools.py`` / ``user_tools.py``.

Used by both export (one row per agent tool) and import (write
``{lang}/tools.json`` keyed by tool name).

Distinct from ``seatau.translation.extractors``, which produces per-
docstring-part ``SourceSpan`` segments for the LLM translation pipeline.
The annotation pipeline needs the higher-level "one tool, one row" view.
"""

from __future__ import annotations

import ast
from pathlib import Path

_TOOL_DECORATORS = frozenset({"is_tool", "is_discoverable_tool"})


def _decorator_name(node: ast.AST) -> str | None:
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def extract_tool_docstrings(path: Path) -> dict[str, str]:
    """Return ``{method_name: docstring}`` for every agent tool in ``path``.

    Agent tools are class methods decorated with ``@is_tool`` or
    ``@is_discoverable_tool`` (matching ``seatau.translation.extractors``'s
    definition). Empty/whitespace-only docstrings are skipped.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(
                _decorator_name(dec) in _TOOL_DECORATORS for dec in item.decorator_list
            ):
                continue
            docstring = ast.get_docstring(item, clean=False)
            if docstring and docstring.strip():
                docs[item.name] = docstring.strip()
    return docs
