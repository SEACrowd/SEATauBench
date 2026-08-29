from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import toml
from docstring_parser import DocstringStyle
from docstring_parser import parse as parse_docstring

from seatau.constants import matches_any, path_matches
from seatau.translation.config import (
    CANONICAL_KEYS,
    DB_FILE_NAMES,
    DOMAIN_SKIPPED_TASK_FILES,
    MARKDOWN_GLOBS,
    SCHEMA_PYTHON_FILES,
    SKIPPED_TASK_FILES,
    TASK_FILE_GLOBS,
    TASK_ONLY_PROTECTED_TERMS,
    TASK_TRANSLATABLE_PATTERNS,
    TOOL_PYTHON_FILES,
    get_domain_db_translatable_leaf_keys,
    get_domain_fixed_protected_terms,
)
from seatau.translation.models import DomainFile, ExtractionResult, Segment, SourceSpan


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
            domain_skipped_task_files = DOMAIN_SKIPPED_TASK_FILES.get(domain, set())
            for pattern in TASK_FILE_GLOBS:
                for file_path in sorted(data_dir.glob(pattern)):
                    if file_path.name in SKIPPED_TASK_FILES:
                        continue
                    if file_path.name in domain_skipped_task_files:
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

    if src_dir.exists():
        python_names: tuple[str, ...] = ()
        if "tools" in components:
            python_names += TOOL_PYTHON_FILES
        if "schema" in components:
            python_names += SCHEMA_PYTHON_FILES

        for name in python_names:
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
    for file in files:
        result.protected_terms.update(get_domain_fixed_protected_terms(file.domain))
        if file.kind == "markdown":
            result.extend(_extract_markdown(file))
        elif file.kind in {"json", "toml"}:
            if file.path.name.startswith("tasks") and file.path.suffix == ".json":
                result.extend(_extract_tasks_json(file))
            elif file.path.name in {"data_model.json", "user_data_model.json"}:
                result.extend(_extract_schema_json(file))
            elif file.path.name in {
                "db.json",
                "user_db.json",
                "db.toml",
                "user_db.toml",
            }:
                result.extend(_extract_db_json(file))
        elif file.kind == "python":
            if file.path.name in TOOL_PYTHON_FILES:
                python_result = _extract_python(file, decorated_tool_methods_only=True)
                result.extend(python_result)
                result.extend(_extract_tool_return_messages(file))
            elif file.path.name in SCHEMA_PYTHON_FILES:
                result.extend(_extract_schema_python(file))
    return result


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _has_translatable_text(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value))


def _should_protect_canonical_value(value: str) -> bool:
    """Skip numeric-only strings; masking them breaks ordinary dates and counts."""
    return not value.isdigit()


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
            if (
                key in CANONICAL_KEYS
                and isinstance(value, str)
                and _should_protect_canonical_value(value)
            ):
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


def _should_translate_db_leaf(
    path: tuple[str, ...], translatable_leaf_keys: frozenset[str]
) -> bool:
    if not path:
        return False
    leaf = path[-1]
    if leaf not in translatable_leaf_keys:
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
    translatable_leaf_keys = get_domain_db_translatable_leaf_keys(file.domain)
    _collect_canonical_terms(data, result)

    for path, value in _iter_string_leaves(data):
        if not value.strip():
            continue
        if not _has_translatable_text(value):
            continue
        if not _should_translate_db_leaf(path, translatable_leaf_keys):
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


def _template_to_pattern(template: str) -> str:
    """Convert {var_name} placeholders to named regex capture groups."""
    parts = re.split(r"(\{[^{}]+\})", template)
    pattern_parts = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            var_name = part[1:-1]
            pattern_parts.append(f"(?P<{var_name}>.+)")
        else:
            pattern_parts.append(re.escape(part))
    return "^" + "".join(pattern_parts) + "$"


def _find_tool_return_messages(tree: ast.AST) -> dict[str, str] | None:
    """Locate TOOL_RETURN_MESSAGES dict in the module body."""
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            if (
                isinstance(node.target, ast.Name)
                and node.target.id == "TOOL_RETURN_MESSAGES"
                and isinstance(node.value, ast.Dict)
            ):
                return _parse_string_dict(node.value)
        elif isinstance(node, ast.Assign):
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "TOOL_RETURN_MESSAGES"
                and isinstance(node.value, ast.Dict)
            ):
                return _parse_string_dict(node.value)
    return None


def _parse_string_dict(node: ast.Dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for key_node, val_node in zip(node.keys, node.values):
        if (
            isinstance(key_node, ast.Constant)
            and isinstance(key_node.value, str)
            and isinstance(val_node, ast.Constant)
            and isinstance(val_node.value, str)
        ):
            result[key_node.value] = val_node.value
    return result


def _extract_tool_return_messages(file: DomainFile) -> ExtractionResult:
    """Extract TOOL_RETURN_MESSAGES entries from a tools.py as tool_returns segments."""
    source = _read_text(file.path)
    tree = ast.parse(source)
    result = ExtractionResult()

    messages = _find_tool_return_messages(tree)
    if not messages:
        return result

    for key, value in messages.items():
        if not value.strip() or not _has_translatable_text(value):
            continue
        placeholders = re.findall(r"\{[^{}]+\}", value)
        result.protected_terms.update(placeholders)
        section = "templates" if placeholders else "exact"
        result.segments.append(
            Segment(
                segment_id=f"{file.relative_path.as_posix()}::tool_returns::{section}/{key}",
                domain=file.domain,
                file_path=file.path,
                relative_path=file.relative_path,
                kind="tool_returns",
                address=(section, key),
                text=value,
                name=key,
            )
        )

    return result


def _extract_tool_returns_json(file: DomainFile) -> ExtractionResult:
    raw = _read_text(file.path)
    data = json.loads(raw)
    result = ExtractionResult()

    def add_segment(path: tuple[str, ...], value: str) -> None:
        if not value.strip() or not _has_translatable_text(value):
            return
        result.protected_terms.update(re.findall(r"\{[^{}]+\}", value))
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

    exact = data.get("exact") if isinstance(data, dict) else None
    if isinstance(exact, dict):
        for key, value in exact.items():
            if isinstance(key, str) and isinstance(value, str):
                add_segment(("exact", key), value)

    templates = data.get("templates") if isinstance(data, dict) else None
    if isinstance(templates, dict):
        for key, value in templates.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            template = value.get("template")
            if isinstance(template, str):
                add_segment(("templates", key, "template"), template)

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


def _decorator_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return _call_name(node)


def extract_decorated_tool_method_names(tree: ast.AST) -> set[str]:
    tool_decorators = {"is_tool", "is_discoverable_tool"}
    method_names: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if any(
                _decorator_name(decorator) in tool_decorators
                for decorator in item.decorator_list
            ):
                method_names.add(item.name)

    return method_names


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


def _extract_python(
    file: DomainFile,
    *,
    decorated_tool_methods_only: bool = False,
) -> ExtractionResult:
    source = _read_text(file.path)
    tree = ast.parse(source)
    starts = _line_starts(source)
    result = ExtractionResult()
    decorated_tool_method_names = (
        extract_decorated_tool_method_names(tree)
        if decorated_tool_methods_only
        else None
    )

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
        if (
            decorated_tool_method_names is not None
            and name not in decorated_tool_method_names
        ):
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


def _unwrap_annotated(node: ast.AST) -> ast.AST:
    if isinstance(node, ast.Subscript) and _call_name(node.value) == "Annotated":
        slice_node = node.slice
        if isinstance(slice_node, ast.Tuple) and slice_node.elts:
            return slice_node.elts[0]
        return slice_node
    return node


def _literal_values(node: ast.AST | None) -> list[str]:
    if node is None:
        return []

    node = _unwrap_annotated(node)
    if isinstance(node, ast.Subscript) and _call_name(node.value) == "Literal":
        slice_node = node.slice
        raw_values = (
            slice_node.elts if isinstance(slice_node, ast.Tuple) else [slice_node]
        )
        values = [
            item.value
            for item in raw_values
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        ]
        return list(dict.fromkeys(values))

    values: list[str] = []
    for child in ast.iter_child_nodes(node):
        values.extend(_literal_values(child))
    return list(dict.fromkeys(values))


def _field_description(node: ast.AST | None) -> str | None:
    if not isinstance(node, ast.Call) or _call_name(node.func) != "Field":
        return None
    for keyword in node.keywords:
        if keyword.arg == "description" and _is_string_constant(keyword.value):
            text = keyword.value.value.strip()
            return text or None
    return None


def _annotation_text(node: ast.AST) -> str:
    return ast.unparse(node)


def _is_enum_class(node: ast.ClassDef) -> bool:
    return any(_call_name(base) == "Enum" for base in node.bases)


def _top_level_literal_alias(node: ast.AST) -> tuple[str, list[str]] | None:
    if isinstance(node, ast.Assign):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return None
        values = _literal_values(node.value)
        if values:
            return node.targets[0].id, values
        return None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        values = _literal_values(node.annotation) or _literal_values(node.value)
        if values:
            return node.target.id, values
    return None


def _enum_members(node: ast.ClassDef) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for child in node.body:
        if (
            isinstance(child, ast.Assign)
            and len(child.targets) == 1
            and isinstance(child.targets[0], ast.Name)
            and _is_string_constant(child.value)
        ):
            members.append((child.targets[0].id, child.value.value))
        elif (
            isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Name)
            and _is_string_constant(child.value)
        ):
            members.append((child.target.id, child.value.value))
    return members


def _schema_segment(
    file: DomainFile,
    address: tuple[str, ...],
    text: str,
    *,
    name: str | None = None,
    translate_runtime_labels: bool = False,
) -> Segment:
    path_str = "/".join(address)
    return Segment(
        segment_id=f"{file.relative_path.as_posix()}::schema::{path_str}",
        domain=file.domain,
        file_path=file.path,
        relative_path=file.relative_path,
        kind="python",
        address=address,
        text=text,
        name=name,
        translate_runtime_labels=translate_runtime_labels,
    )


def _should_translate_runtime_label(value: str) -> bool:
    """Return whether a schema literal should be translated as a label."""
    stripped = value.strip()
    if not stripped:
        return False
    if "_" not in stripped:
        return True
    if any(char.isdigit() for char in stripped):
        return False
    parts = [part for part in stripped.split("_") if part]
    if len(parts) < 2:
        return False
    return all(part.isalpha() for part in parts)


def _add_value_set_entry(
    artifact: dict[str, Any],
    result: ExtractionResult,
    file: DomainFile,
    key: str,
    *,
    kind: str,
    values: list[str],
    members: list[str] | None = None,
    owner_model: str | None = None,
    owner_field: str | None = None,
) -> None:
    if key in artifact["value_sets"]:
        return

    entry: dict[str, Any] = {"kind": kind, "values": []}
    if owner_model is not None:
        entry["owner_model"] = owner_model
    if owner_field is not None:
        entry["owner_field"] = owner_field

    for idx, value in enumerate(values):
        value_entry = {"canonical": value, "localized": value}
        if members is not None:
            value_entry["member"] = members[idx]
        entry["values"].append(value_entry)
        if _should_protect_canonical_value(value):
            result.protected_terms.add(value)
        if value.strip():
            result.segments.append(
                _schema_segment(
                    file,
                    ("value_sets", key, "values", str(idx), "localized"),
                    value,
                    name=key,
                    translate_runtime_labels=_should_translate_runtime_label(value),
                )
            )

    artifact["value_sets"][key] = entry


def build_schema_artifact(file: DomainFile) -> tuple[dict[str, Any], ExtractionResult]:
    source = _read_text(file.path)
    tree = ast.parse(source)
    result = ExtractionResult()
    artifact: dict[str, Any] = {
        "kind": "schema",
        "source_file": file.relative_path.as_posix(),
        "models": {},
        "value_sets": {},
    }

    known_value_set_names = {
        alias_name
        for node in tree.body
        if (alias := _top_level_literal_alias(node)) is not None
        for alias_name in [alias[0]]
    }
    known_value_set_names.update(
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and _is_enum_class(node)
    )

    module_doc = ast.get_docstring(tree, clean=False)
    if module_doc and module_doc.strip():
        text = module_doc.strip()
        artifact["module_description"] = text
        result.segments.append(_schema_segment(file, ("module_description",), text))

    for node in tree.body:
        alias = _top_level_literal_alias(node)
        if alias is not None:
            alias_name, values = alias
            _add_value_set_entry(
                artifact,
                result,
                file,
                alias_name,
                kind="literal",
                values=values,
            )
            continue

        if not isinstance(node, ast.ClassDef):
            continue

        if _is_enum_class(node):
            members = _enum_members(node)
            _add_value_set_entry(
                artifact,
                result,
                file,
                node.name,
                kind="enum",
                values=[value for _, value in members],
                members=[member for member, _ in members],
            )
            continue

        model_entry: dict[str, Any] = {"fields": {}}
        docstring = ast.get_docstring(node, clean=False)
        if docstring and docstring.strip():
            text = docstring.strip()
            model_entry["description"] = text
            result.segments.append(
                _schema_segment(
                    file, ("models", node.name, "description"), text, name=node.name
                )
            )

        for child in node.body:
            if not isinstance(child, ast.AnnAssign) or not isinstance(
                child.target, ast.Name
            ):
                continue

            field_name = child.target.id
            field_entry: dict[str, Any] = {
                "annotation": _annotation_text(child.annotation)
            }

            description = _field_description(child.value)
            if description:
                field_entry["description"] = description
                result.segments.append(
                    _schema_segment(
                        file,
                        ("models", node.name, "fields", field_name, "description"),
                        description,
                        name=node.name,
                    )
                )

            inline_values = _literal_values(child.annotation)
            if inline_values:
                value_set_key = f"{node.name}.{field_name}"
                _add_value_set_entry(
                    artifact,
                    result,
                    file,
                    value_set_key,
                    kind="literal",
                    values=inline_values,
                    owner_model=node.name,
                    owner_field=field_name,
                )
                field_entry["value_set"] = value_set_key
            else:
                annotation_node = _unwrap_annotated(child.annotation)
                type_name = _call_name(annotation_node)
                if type_name in known_value_set_names:
                    field_entry["value_set"] = type_name

            model_entry["fields"][field_name] = field_entry

        artifact["models"][node.name] = model_entry

    return artifact, result


def _extract_schema_python(file: DomainFile) -> ExtractionResult:
    _, result = build_schema_artifact(file)
    return result


def _extract_schema_json(file: DomainFile) -> ExtractionResult:
    source_text = _read_text(file.path)
    obj = json.loads(source_text)
    result = ExtractionResult()
    for path, value in _iter_string_leaves(obj):
        if not value.strip():
            continue
        if path == ("module_description",) or path[-1] in {"description", "localized"}:
            result.segments.append(
                Segment(
                    segment_id=f"{file.relative_path.as_posix()}::json::{'/'.join(path)}",
                    domain=file.domain,
                    file_path=file.path,
                    relative_path=file.relative_path,
                    kind="json",
                    address=path,
                    text=value,
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
