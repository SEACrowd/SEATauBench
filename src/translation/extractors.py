from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import toml
from docstring_parser import DocstringStyle
from docstring_parser import parse as parse_docstring

from translation.config import (
    CANONICAL_KEYS,
    DB_FILE_NAMES,
    DB_TRANSLATABLE_LEAF_KEYS,
    FIXED_PROTECTED_TERMS,
    MARKDOWN_GLOBS,
    PYTHON_FILES,
    SKIPPED_TASK_FILES,
    TASK_FILE_GLOBS,
    TASK_ONLY_PROTECTED_TERMS,
    TASK_TRANSLATABLE_PATTERNS,
)
from translation.models import DomainFile, ExtractionResult, Segment, SourceSpan
from translation.path_match import matches_any, path_matches


def discover_domain_files(
    domain: str,
    data_domains_root: Path,
    src_domains_root: Path,
    components: tuple[str, ...],
) -> list[DomainFile]:
    files: list[DomainFile] = []
    data_dir = data_domains_root / domain
    src_dir = src_domains_root / domain

    if data_dir.exists():
        if "tasks" in components:
            for pattern in TASK_FILE_GLOBS:
                for file_path in sorted(data_dir.glob(pattern)):
                    if file_path.name in SKIPPED_TASK_FILES:
                        continue
                    files.append(
                        DomainFile(
                            domain=domain,
                            path=file_path,
                            relative_path=file_path,
                            kind="json",
                        )
                    )
        if "db" in components:
            for name in DB_FILE_NAMES:
                file_path = data_dir / name
                if not file_path.exists():
                    continue
                kind = "toml" if file_path.suffix == ".toml" else "json"
                files.append(
                    DomainFile(
                        domain=domain,
                        path=file_path,
                        relative_path=file_path,
                        kind=kind,
                    )
                )
        if "policy" in components:
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

    if src_dir.exists() and "tools" in components:
        for name in PYTHON_FILES:
            file_path = src_dir / name
            if not file_path.exists():
                continue
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
        elif file.kind in {"json", "toml"}:
            if file.path.name.startswith("tasks") and file.path.suffix == ".json":
                result.extend(_extract_tasks_json(file))
            elif file.path.name in {
                "db.json",
                "user_db.json",
                "db.toml",
                "user_db.toml",
            }:
                result.extend(_extract_db_json(file))
        elif file.kind == "python":
            if file.path.name in {"tools.py", "user_tools.py"}:
                python_result = _extract_python(file)
                python_result.segments = [
                    segment
                    for segment in python_result.segments
                    if segment.name is not None
                    and segment.name[0].islower()
                    and not segment.name.startswith("_")
                ]
                result.extend(python_result)
    return result


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _has_translatable_text(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value))


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


def _should_translate_task_path(
    task_obj: dict[str, Any], local_path: tuple[str, ...]
) -> bool:
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
    if file.path.suffix != ".json":
        raise ValueError(f"Tasks file must be JSON: {file.path}")
    raw = _read_text(file.path)
    data = json.loads(raw)
    result = ExtractionResult()
    result.protected_terms.update(TASK_ONLY_PROTECTED_TERMS)
    if not isinstance(data, list):
        return result

    _collect_canonical_terms(data, result)

    for task_idx, task in enumerate(data):
        if not isinstance(task, dict):
            continue
        for local_path, value in _iter_string_leaves(task):
            if not value.strip():
                continue
            if not _has_translatable_text(value):
                continue
            if not _should_translate_task_path(task, local_path):
                continue
            full_path = (str(task_idx),) + local_path
            result.segments.append(
                Segment(
                    segment_id=(
                        f"{file.relative_path.as_posix()}::json::" + "/".join(full_path)
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
    if file.path.suffix == ".json":
        data = json.loads(raw)
    elif file.path.suffix == ".toml":
        data = toml.loads(raw)
    else:
        raise ValueError(f"Unsupported DB file type: {file.path}")
    result = ExtractionResult()
    _collect_canonical_terms(data, result)

    for path, value in _iter_string_leaves(data):
        if not value.strip():
            continue
        if not _has_translatable_text(value):
            continue
        if not _should_translate_db_leaf(path):
            continue
        result.segments.append(
            Segment(
                segment_id=f"{file.relative_path.as_posix()}::json::" + "/".join(path),
                domain=file.domain,
                file_path=file.path,
                relative_path=file.relative_path,
                kind=file.kind,
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


def _extract_docstring_parts(docstring: str) -> list[tuple[str, str]]:
    doc = parse_docstring(docstring, style=DocstringStyle.GOOGLE)
    parts: list[tuple[str, str]] = []

    if doc.short_description:
        text = doc.short_description.strip()
        if text:
            parts.append(("short", text))

    if doc.long_description:
        text = doc.long_description.strip()
        if text:
            parts.append(("long", text))

    for param in doc.params:
        desc = (param.description or "").strip()
        if desc:
            parts.append((f"param:{param.arg_name}", desc))

    if doc.returns and doc.returns.description:
        desc = doc.returns.description.strip()
        if desc:
            parts.append(("returns", desc))

    for idx, exc in enumerate(doc.raises):
        desc = (exc.description or "").strip()
        if desc:
            parts.append((f"raises:{idx}", desc))

    return parts


def _extract_python(file: DomainFile) -> ExtractionResult:
    source = _read_text(file.path)
    tree = ast.parse(source)
    starts = _line_starts(source)
    result = ExtractionResult()

    # Each entry: (constant node, owner name or None)
    tagged: list[tuple[ast.Constant, str | None]] = []

    # Module docstring (no owner name)
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and _is_string_constant(tree.body[0].value)
    ):
        tagged.append((tree.body[0].value, None))

    # Class/function docstrings — record the owner name
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and _is_string_constant(node.body[0].value)
            ):
                tagged.append((node.body[0].value, node.name))

    # Pydantic Field(description="...") strings (no owner name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) != "Field":
            continue
        for keyword in node.keywords:
            if keyword.arg == "description" and _is_string_constant(keyword.value):
                tagged.append((keyword.value, None))

    # Deduplicate by span
    seen: set[tuple[int, int]] = set()
    for const, name in tagged:
        span = _string_span(const, starts)
        key = (span.start, span.end)
        if key in seen:
            continue
        seen.add(key)
        text = const.value
        if not text.strip():
            continue
        if name is not None:
            parts = _extract_docstring_parts(text)
            if not parts:
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
                        name=name,
                    )
                )
                continue
            for part_key, part_text in parts:
                result.segments.append(
                    Segment(
                        segment_id=(
                            f"{file.relative_path.as_posix()}::py::"
                            f"{span.start}:{span.end}::{part_key}"
                        ),
                        domain=file.domain,
                        file_path=file.path,
                        relative_path=file.relative_path,
                        kind="python",
                        address=span,
                        text=part_text,
                        name=name,
                        source_text=text,
                        python_doc_key=part_key,
                    )
                )
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
                name=name,
            )
        )
    return result


def _apply_structured_updates(
    obj: Any,
    segments: list[Segment],
    translated: dict[str, str],
) -> Any:
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
    return obj


def apply_json_updates(
    source_text: str,
    segments: list[Segment],
    translated: dict[str, str],
) -> str:
    obj = json.loads(source_text)
    obj = _apply_structured_updates(obj, segments, translated)
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def apply_toml_updates(
    source_text: str,
    segments: list[Segment],
    translated: dict[str, str],
) -> str:
    obj = toml.loads(source_text)
    obj = _apply_structured_updates(obj, segments, translated)
    return toml.dumps(obj)
