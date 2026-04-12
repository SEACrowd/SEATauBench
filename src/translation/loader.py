"""Inject translated docstrings into tool classes at eval time.

Two injection patterns are supported:

1. **Patch/restore** for eval scripts — call :func:`patch_toolkit_docstrings` before
   ``run_domain()`` and :func:`restore_toolkit_docstrings` after (optional).
   This is the recommended pattern because ``get_tools()`` is called *outside*
   the environment factory, so a context manager inside ``get_environment()``
   would restore docstrings too early.

2. **Context manager** for unit tests and one-off verification::

       with localized_toolkit(RetailTools, docs) as cls:
           tools = cls(db).get_tools()   # must call get_tools inside the block
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from tau2.environment.toolkit import ToolKitBase


def load_docstrings_json(path: Path) -> dict[str, str]:
    """Load a translated docstrings JSON file produced by the pipeline.

    Args:
        path: Path to a JSON file mapping function/class name to translated
            docstring (e.g. ``data/tau2/domains/retail/th/tools.json``).

    Returns:
        Mapping of function/class name to translated docstring text.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def patch_toolkit_docstrings(
    tool_class: type[ToolKitBase],
    docstrings: dict[str, str],
) -> dict[str, str | None]:
    """Patch tool class method ``__doc__`` attributes with translated text.

    This is the recommended injection method for evaluation runs.  Call it
    **before** ``run_domain()`` / ``build_orchestrator()`` so that when
    ``get_tools()`` eventually reads ``func.__doc__``, it sees the translated
    version.

    Args:
        tool_class: The ``ToolKitBase`` subclass whose methods to patch.
        docstrings: ``{method_name: translated_docstring}``.
            Unknown names are silently skipped.

    Returns:
        ``{method_name: original_docstring}`` for every method that was
        patched.  Pass this to :func:`restore_toolkit_docstrings` to undo.

    Example::

        originals = patch_toolkit_docstrings(RetailTools, docs)
        try:
            run_domain(config)          # tools see translated docstrings
        finally:
            restore_toolkit_docstrings(RetailTools, originals)
    """
    originals: dict[str, str | None] = {}
    for func_name, doc in docstrings.items():
        method = getattr(tool_class, func_name, None)
        if method is not None and callable(method):
            originals[func_name] = method.__doc__
            method.__doc__ = doc
    return originals


def restore_toolkit_docstrings(
    tool_class: type[ToolKitBase],
    originals: dict[str, str | None],
) -> None:
    """Restore original ``__doc__`` attributes saved by :func:`patch_toolkit_docstrings`.

    Args:
        tool_class: The same class passed to :func:`patch_toolkit_docstrings`.
        originals: The dict returned by :func:`patch_toolkit_docstrings`.
    """
    for func_name, original_doc in originals.items():
        method = getattr(tool_class, func_name, None)
        if method is not None:
            method.__doc__ = original_doc


@contextlib.contextmanager
def localized_toolkit(
    tool_class: type[ToolKitBase],
    docstrings: dict[str, str],
) -> Iterator[type[ToolKitBase]]:
    """Temporarily patch tool method docstrings within a ``with`` block.

    ``__doc__`` is restored on exit.  **Important:** ``get_tools()`` must be
    called *inside* the block — otherwise the restored English docstrings are
    read instead.

    Args:
        tool_class: The ``ToolKitBase`` subclass whose methods to patch.
        docstrings: ``{method_name: translated_docstring}``.

    Yields:
        The same ``tool_class`` (with patched docstrings).
    """
    originals = patch_toolkit_docstrings(tool_class, docstrings)
    try:
        yield tool_class
    finally:
        restore_toolkit_docstrings(tool_class, originals)
