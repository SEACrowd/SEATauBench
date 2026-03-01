from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from translation.config import (
    CANONICAL_KEYS,
    DATA_JSON_FILES,
    DB_TRANSLATABLE_LEAF_KEYS,
    FIXED_PROTECTED_TERMS,
    MARKDOWN_GLOBS,
    PYTHON_FILES,
    TASK_TRANSLATABLE_PATTERNS,
)
from translation.models import DomainFile, ExtractionResult, Segment, SourceSpan
from translation.path_match import matches_any, path_matches


def discover_domain_files(
    domain: str,
    data_domains_root: Path,
    src_domains_root: Path,
) -> list[DomainFile]:
    files: list[DomainFile] = []
    data_dir = data_domains_root / domain
    src_dir = src_domains_root / domain

    if data_dir.exists():
        for name in DATA_JSON_FILES:
            file_path = data_dir / name
            if file_path.exists():
                files.append(
                    DomainFile(
                        domain=domain,
                        path=file_path,
                        relative_path=file_path,
                        kind="json",
                    )
                )
        for pattern in MARKDOWN_GLOBS:
            for file_path in sorted(data_dir.glob(pattern)):
                files.append(
                    DomainFile(
                        domain=domain,
                        path=file_path,
                        relative_path=file_path,
                        kind="markdown",
                    )
                )

    if src_dir.exists():
        for name in PYTHON_FILES:
            file_path = src_dir / name
            if file_path.exists():
                files.append(
                    DomainFile(
                        domain=domain,
                        path=file_path,
                        relative_path=file_path,
                        kind="python",
                    )
                )

    return files


def extract_files(files: list[DomainFile]) -> ExtractionResult:
    result = ExtractionResult()
    result.protected_terms.update(FIXED_PROTECTED_TERMS)
    for file in files:
        if file.kind == "markdown":
            result.extend(_extract_markdown(file))
        elif file.kind == "json":
            if file.path.name == "tasks.json":
                result.extend(_extract_tasks_json(file))
            elif file.path.name in {"db.json", "user_db.json"}:
                result.extend(_extract_db_json(file))
        elif file.kind == "python":
            if file.path.name in {"data_model.py", "tools.py", "user_data_model.py", "user_tools.py"}:
                result.extend(_extract_python(file))
    return result


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_markdown(file: DomainFile) -> ExtractionResult:
    text = _read_text(file.path)
    result = ExtractionResult()
    if text.strip():
        result.segments.append(
            Segment(
                segment_id=f"{file.relative_path.as_posix()}::md::full",
                domain=file.domain,
                file_path=file.path,
                relative_path=file.relative_path,
                kind="markdown",
                address="full",
                text=text,
            )
        )
    return result


def _iter_string_leaves(
    node: Any,
    path: tuple[str, ...] = (),
):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _iter_string_leaves(value, path + (str(key),))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            yield from _iter_string_leaves(value, path + (str(idx),))
    elif isinstance(node, str):
        yield path, node


def _get_by_path(node: Any, path: tuple[str, ...]) -> Any:
    cur = node
    for key in path:
        if isinstance(cur, list):
            cur = cur[int(key)]
        else:
            cur = cur[key]
    return cur


def _collect_canonical_terms(
    node: Any, result: ExtractionResult, path: tuple[str, ...] = ()
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in CANONICAL_KEYS and isinstance(value, str):
                result.protected_terms.add(value)
            if (
                key == "name"
                and isinstance(value, str)
                and len(path) >= 1
                and path[-1] in {"actions", "tool_calls"}
            ):
                result.protected_terms.add(value)
            if key in {"reward_basis"} and isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        result.protected_terms.add(item)
            _collect_canonical_terms(value, result, path + (str(key),))
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _collect_canonical_terms(item, result, path + (str(idx),))


def _should_translate_task_path(task_obj: dict[str, Any], local_path: tuple[str, ...]) -> bool:
    if not matches_any(local_path, TASK_TRANSLATABLE_PATTERNS):
        return False

    # For initial message history, only translate user/assistant visible text.
    msg_pattern = ("initial_state", "message_history", "*", "content")
    if path_matches(local_path, msg_pattern):
        idx = local_path[-2]
        role_path = ("initial_state", "message_history", idx, "role")
        role = _get_by_path(task_obj, role_path)
        return role in {"user", "assistant"}

    return True


def _extract_tasks_json(file: DomainFile) -> ExtractionResult:
    raw = _read_text(file.path)
    data = json.loads(raw)
    result = ExtractionResult()
    if not isinstance(data, list):
        return result

    _collect_canonical_terms(data, result)

    for task_idx, task in enumerate(data):
        if not isinstance(task, dict):
            continue
        for local_path, value in _iter_string_leaves(task):
            if not value.strip():
                continue
            if not _should_translate_task_path(task, local_path):
                continue
            full_path = (str(task_idx),) + local_path
            result.segments.append(
                Segment(
                    segment_id=(
                        f"{file.relative_path.as_posix()}::json::"
                        + "/".join(full_path)
                    ),
                    domain=file.domain,
                    file_path=file.path,
                    relative_path=file.relative_path,
                    kind="json",
                    address=full_path,
                    text=value,
                )
            )
    return result


def _should_translate_db_leaf(path: tuple[str, ...]) -> bool:
    if not path:
        return False
    leaf = path[-1]
    if leaf not in DB_TRANSLATABLE_LEAF_KEYS:
        return False
    if len(path) >= 2 and path[-2] in {"actions", "tool_calls"}:
        return False
    return True


def _extract_db_json(file: DomainFile) -> ExtractionResult:
    raw = _read_text(file.path)
    data = json.loads(raw)
    result = ExtractionResult()
    _collect_canonical_terms(data, result)

    for path, value in _iter_string_leaves(data):
        if not value.strip():
            continue
        if not _should_translate_db_leaf(path):
            continue
        result.segments.append(
            Segment(
                segment_id=f"{file.relative_path.as_posix()}::json::" + "/".join(path),
                domain=file.domain,
                file_path=file.path,
                relative_path=file.relative_path,
                kind="json",
                address=path,
                text=value,
            )
        )
    return result


def _line_starts(source: str) -> list[int]:
    starts = [0]
    for idx, char in enumerate(source):
        if char == "\n":
            starts.append(idx + 1)
    return starts


def _offset(starts: list[int], lineno: int, col: int) -> int:
    return starts[lineno - 1] + col


def _string_span(node: ast.Constant, starts: list[int]) -> SourceSpan:
    return SourceSpan(
        start=_offset(starts, node.lineno, node.col_offset),
        end=_offset(starts, node.end_lineno, node.end_col_offset),
    )


def _is_string_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _extract_python(file: DomainFile) -> ExtractionResult:
    source = _read_text(file.path)
    tree = ast.parse(source)
    starts = _line_starts(source)
    result = ExtractionResult()

    constants: list[ast.Constant] = []

    # Module docstring
    if tree.body and isinstance(tree.body[0], ast.Expr) and _is_string_constant(tree.body[0].value):
        constants.append(tree.body[0].value)

    # Class/function docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and _is_string_constant(node.body[0].value):
                constants.append(node.body[0].value)

    # Pydantic Field(description="...") strings.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "Field":
            continue
        for keyword in node.keywords:
            if keyword.arg == "description" and _is_string_constant(keyword.value):
                constants.append(keyword.value)

    # Deduplicate by span
    seen: set[tuple[int, int]] = set()
    for const in constants:
        span = _string_span(const, starts)
        key = (span.start, span.end)
        if key in seen:
            continue
        seen.add(key)
        text = const.value
        if not text.strip():
            continue
        result.segments.append(
            Segment(
                segment_id=(
                    f"{file.relative_path.as_posix()}::py::{span.start}:{span.end}"
                ),
                domain=file.domain,
                file_path=file.path,
                relative_path=file.relative_path,
                kind="python",
                address=span,
                text=text,
            )
        )
    return result


def apply_json_updates(
    source_text: str,
    segments: list[Segment],
    translated: dict[str, str],
) -> str:
    obj = json.loads(source_text)
    for segment in segments:
        value = translated.get(segment.segment_id)
        if value is None:
            continue
        path = segment.address
        assert isinstance(path, tuple)
        parent = obj
        for key in path[:-1]:
            if isinstance(parent, list):
                parent = parent[int(key)]
            else:
                parent = parent[key]
        leaf = path[-1]
        if isinstance(parent, list):
            parent[int(leaf)] = value
        else:
            parent[leaf] = value
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


_QUOTE_RE = re.compile(
    r"^(?P<prefix>[rRuUbBfF]*)(?P<quote>'''|\"\"\"|'|\")(?P<body>.*)(?P=quote)$",
    re.DOTALL,
)


def _render_string_literal(original_fragment: str, new_text: str) -> str:
    fragment = original_fragment.strip()
    match = _QUOTE_RE.match(fragment)
    if not match:
        return json.dumps(new_text, ensure_ascii=False)

    prefix = match.group("prefix")
    quote = match.group("quote")
    if "f" in prefix.lower():
        # Conservative fallback: keep f-string semantics untouched.
        return original_fragment

    if quote in {"'''", '"""'}:
        escaped = new_text.replace(quote, "\\" + quote)
        return f"{prefix}{quote}{escaped}{quote}"

    dumped = json.dumps(new_text, ensure_ascii=False)
    if quote == '"':
        return f"{prefix}{dumped}"

    # Single-quote output
    inner = dumped[1:-1].replace("'", "\\'")
    return f"{prefix}'{inner}'"


def apply_python_updates(
    source_text: str,
    segments: list[Segment],
    translated: dict[str, str],
) -> str:
    updates: list[tuple[SourceSpan, str]] = []
    for segment in segments:
        value = translated.get(segment.segment_id)
        if value is None:
            continue
        span = segment.address
        assert isinstance(span, SourceSpan)
        updates.append((span, value))

    updates.sort(key=lambda row: row[0].start, reverse=True)
    out = source_text
    for span, text_value in updates:
        original_fragment = out[span.start : span.end]
        replacement = _render_string_literal(original_fragment, text_value)
        out = out[: span.start] + replacement + out[span.end :]
    return out
