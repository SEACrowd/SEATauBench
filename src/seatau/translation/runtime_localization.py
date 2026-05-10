from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import MethodType
from typing import Any, Callable

from tau2.data_model.message import ToolCall, ToolMessage
from tau2.environment.tool import Tool, as_tool


def _iter_value_entries(node: Any):
    if isinstance(node, dict):
        value_sets = node.get("value_sets")
        if isinstance(value_sets, dict):
            for value_set in value_sets.values():
                if not isinstance(value_set, dict):
                    continue
                values = value_set.get("values")
                if not isinstance(values, list):
                    continue
                for entry in values:
                    if isinstance(entry, dict):
                        yield entry


def _iter_descriptions_by_path(node: Any, path: tuple[str, ...] = ()):
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = path + (key,)
            if key in {"description", "module_description"} and isinstance(value, str):
                yield child_path, value
            yield from _iter_descriptions_by_path(value, child_path)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            yield from _iter_descriptions_by_path(item, path + (str(idx),))


class SchemaRuntimeLocalizer:
    """Runtime helper for localized agent-facing schema and tool I/O."""

    def __init__(
        self,
        *,
        description_map: dict[str, str],
        canonical_to_localized: dict[str, str],
        localized_to_canonicals: dict[str, set[str]],
    ) -> None:
        self.description_map = description_map
        self.canonical_to_localized = canonical_to_localized
        self.localized_to_canonicals = localized_to_canonicals

    @classmethod
    def from_artifact_pairs(
        cls,
        source_artifacts: list[dict[str, Any]],
        localized_artifacts: list[dict[str, Any]],
    ) -> "SchemaRuntimeLocalizer":
        description_map: dict[str, str] = {}
        canonical_to_localized: dict[str, str] = {}
        localized_to_canonicals: dict[str, set[str]] = {}

        for source_artifact, localized_artifact in zip(
            source_artifacts, localized_artifacts, strict=False
        ):
            source_descriptions = dict(_iter_descriptions_by_path(source_artifact))
            localized_descriptions = dict(
                _iter_descriptions_by_path(localized_artifact)
            )
            for path, source_text in source_descriptions.items():
                localized_text = localized_descriptions.get(path)
                if (
                    isinstance(source_text, str)
                    and isinstance(localized_text, str)
                    and source_text.strip()
                    and localized_text.strip()
                ):
                    description_map[source_text] = localized_text

            for entry in _iter_value_entries(localized_artifact):
                canonical = entry.get("canonical")
                localized = entry.get("localized")
                if not isinstance(canonical, str) or not isinstance(localized, str):
                    continue
                if canonical.strip():
                    canonical_to_localized[canonical] = localized
                aliases = entry.get("aliases", [])
                if not isinstance(aliases, list):
                    aliases = []
                for candidate in [localized, *aliases]:
                    if not isinstance(candidate, str) or not candidate.strip():
                        continue
                    localized_to_canonicals.setdefault(candidate, set()).add(canonical)

        return cls(
            description_map=description_map,
            canonical_to_localized=canonical_to_localized,
            localized_to_canonicals=localized_to_canonicals,
        )

    def localize_tool_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        localized = deepcopy(schema)
        self._localize_schema_node(localized)
        return localized

    def normalize_tool_arguments(
        self,
        arguments: dict[str, Any],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        return self._normalize_by_schema(
            deepcopy(arguments), schema, root_schema=schema
        )

    def localize_response_payload(self, payload: Any) -> Any:
        return self._localize_payload(deepcopy(payload))

    def canonicalize_payload_for_compare(self, payload: Any) -> Any:
        return self._canonicalize_payload(deepcopy(payload))

    def _localize_schema_node(self, node: Any) -> None:
        if isinstance(node, dict):
            description = node.get("description")
            if isinstance(description, str):
                node["description"] = self.description_map.get(description, description)

            enum_values = node.get("enum")
            if isinstance(enum_values, list):
                node["enum"] = [
                    self.canonical_to_localized.get(value, value)
                    if isinstance(value, str)
                    else value
                    for value in enum_values
                ]

            const_value = node.get("const")
            if isinstance(const_value, str):
                node["const"] = self.canonical_to_localized.get(
                    const_value, const_value
                )

            default_value = node.get("default")
            if isinstance(default_value, str):
                node["default"] = self.canonical_to_localized.get(
                    default_value, default_value
                )

            examples = node.get("examples")
            if isinstance(examples, list):
                node["examples"] = [
                    self.canonical_to_localized.get(value, value)
                    if isinstance(value, str)
                    else value
                    for value in examples
                ]

            for value in node.values():
                self._localize_schema_node(value)
        elif isinstance(node, list):
            for item in node:
                self._localize_schema_node(item)

    def _resolve_schema_ref(
        self,
        schema_node: dict[str, Any] | None,
        *,
        root_schema: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(schema_node, dict):
            return {}
        ref = schema_node.get("$ref")
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return schema_node

        resolved: Any = root_schema
        for key in ref[2:].split("/"):
            if not isinstance(resolved, dict):
                return schema_node
            resolved = resolved.get(key)
        if not isinstance(resolved, dict):
            return schema_node
        return resolved

    def _allowed_literals(
        self,
        schema_node: dict[str, Any] | None,
        *,
        root_schema: dict[str, Any],
    ) -> set[str]:
        resolved = self._resolve_schema_ref(schema_node, root_schema=root_schema)
        allowed: set[str] = set()

        enum_values = resolved.get("enum")
        if isinstance(enum_values, list):
            allowed.update(value for value in enum_values if isinstance(value, str))

        const_value = resolved.get("const")
        if isinstance(const_value, str):
            allowed.add(const_value)

        for branch_key in ("anyOf", "oneOf", "allOf"):
            branches = resolved.get(branch_key)
            if isinstance(branches, list):
                for branch in branches:
                    allowed.update(
                        self._allowed_literals(branch, root_schema=root_schema)
                    )

        return allowed

    def _normalize_literal_value(self, value: str, allowed_values: set[str]) -> str:
        if value in allowed_values:
            return value
        candidates = self.localized_to_canonicals.get(value, set()) & allowed_values
        if len(candidates) == 1:
            return next(iter(candidates))
        return value

    def _normalize_by_schema(
        self,
        value: Any,
        schema_node: dict[str, Any] | None,
        *,
        root_schema: dict[str, Any],
    ) -> Any:
        resolved = self._resolve_schema_ref(schema_node, root_schema=root_schema)
        allowed_values = self._allowed_literals(resolved, root_schema=root_schema)

        if isinstance(value, str):
            if allowed_values:
                return self._normalize_literal_value(value, allowed_values)
            return value

        if isinstance(value, list):
            item_schema = resolved.get("items")
            return [
                self._normalize_by_schema(item, item_schema, root_schema=root_schema)
                for item in value
            ]

        if isinstance(value, dict):
            properties = resolved.get("properties")
            additional = resolved.get("additionalProperties")
            normalized: dict[str, Any] = {}
            for key, item in value.items():
                child_schema = None
                if isinstance(properties, dict):
                    child_schema = properties.get(key)
                if child_schema is None and isinstance(additional, dict):
                    child_schema = additional
                normalized[key] = self._normalize_by_schema(
                    item, child_schema, root_schema=root_schema
                )
            return normalized

        return value

    def _localize_payload(self, payload: Any) -> Any:
        if isinstance(payload, str):
            return self.canonical_to_localized.get(payload, payload)
        if isinstance(payload, list):
            return [self._localize_payload(item) for item in payload]
        if isinstance(payload, tuple):
            return tuple(self._localize_payload(item) for item in payload)
        if isinstance(payload, dict):
            return {
                key: self._localize_payload(value) for key, value in payload.items()
            }
        return payload

    def _canonicalize_payload(self, payload: Any) -> Any:
        if isinstance(payload, str):
            candidates = self.localized_to_canonicals.get(payload, set())
            if len(candidates) == 1:
                return next(iter(candidates))
            return payload
        if isinstance(payload, list):
            return [self._canonicalize_payload(item) for item in payload]
        if isinstance(payload, tuple):
            return tuple(self._canonicalize_payload(item) for item in payload)
        if isinstance(payload, dict):
            return {
                key: self._canonicalize_payload(value) for key, value in payload.items()
            }
        return payload


class LocalizedToolProxy:
    """Proxy that localizes only the agent-facing tool schema."""

    def __init__(self, tool: Tool, localizer: SchemaRuntimeLocalizer) -> None:
        self._tool = tool
        self._localizer = localizer

    @property
    def openai_schema(self) -> dict[str, Any]:
        schema = deepcopy(self._tool.openai_schema)
        function = schema.get("function")
        if isinstance(function, dict):
            parameters = function.get("parameters")
            if isinstance(parameters, dict):
                function["parameters"] = self._localizer.localize_tool_schema(
                    parameters
                )
        return schema

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tool, name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._tool(*args, **kwargs)

    def __str__(self) -> str:
        return str(self._tool)


def _build_schema_runtime_localizer(
    *,
    domain: str,
    translated_root: Path,
    src_domain_root: Path,
    warn_if_stale: Callable[..., None] | None = None,
) -> SchemaRuntimeLocalizer | None:
    from seatau.translation.extractors import build_schema_artifact
    from seatau.translation.loader import load_schema_json
    from seatau.translation.models import DomainFile

    source_schema_artifacts: list[dict[str, Any]] = []
    localized_schema_artifacts: list[dict[str, Any]] = []
    for schema_json_name, schema_py_name in (
        ("data_model.json", "data_model.py"),
        ("user_data_model.json", "user_data_model.py"),
    ):
        schema_json_path = translated_root / schema_json_name
        schema_py_path = src_domain_root / schema_py_name
        if not schema_json_path.exists() or not schema_py_path.exists():
            continue
        if warn_if_stale is not None:
            warn_if_stale(schema_json_name)
        localized_schema_artifacts.append(load_schema_json(schema_json_path))
        source_artifact, _ = build_schema_artifact(
            DomainFile(
                domain=domain,
                path=schema_py_path,
                relative_path=schema_py_path,
                kind="python",
            )
        )
        source_schema_artifacts.append(source_artifact)

    if not localized_schema_artifacts:
        return None
    return SchemaRuntimeLocalizer.from_artifact_pairs(
        source_schema_artifacts,
        localized_schema_artifacts,
    )


def _normalize_arguments_for_tool_call(
    environment: Any,
    localizer: SchemaRuntimeLocalizer,
    *,
    requestor: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    toolkit = None
    if requestor == "user":
        toolkit = environment.user_tools
    elif requestor == "assistant":
        toolkit = environment.tools
        if (
            environment.solo_mode
            and environment.user_tools is not None
            and environment.user_tools.has_tool(tool_name)
        ):
            toolkit = environment.user_tools

    if toolkit is None or not toolkit.has_tool(tool_name):
        return arguments

    tool_method = toolkit.tools.get(tool_name)
    if tool_method is None:
        return arguments

    tool = as_tool(tool_method)
    return localizer.normalize_tool_arguments(
        arguments, tool.params.model_json_schema()
    )


def patch_environment_with_schema_localizer(
    environment: Any,
    localizer: SchemaRuntimeLocalizer,
    *,
    localize_tools: bool,
    localize_outputs: bool,
) -> None:
    if getattr(environment, "_translation_schema_localizer", None) is localizer:
        return

    if localize_tools:
        original_get_tools = getattr(
            environment, "_translation_original_get_tools", None
        )
        if original_get_tools is None:
            original_get_tools = environment.get_tools
            environment._translation_original_get_tools = original_get_tools

            def patched_get_tools(self):
                return [
                    LocalizedToolProxy(tool, self._translation_schema_localizer)
                    for tool in self._translation_original_get_tools()
                ]

            environment.get_tools = MethodType(patched_get_tools, environment)

        original_get_user_tools = getattr(
            environment, "_translation_original_get_user_tools", None
        )
        if original_get_user_tools is None:
            original_get_user_tools = environment.get_user_tools
            environment._translation_original_get_user_tools = original_get_user_tools

            def patched_get_user_tools(self, include=None):
                return [
                    LocalizedToolProxy(tool, self._translation_schema_localizer)
                    for tool in self._translation_original_get_user_tools(
                        include=include
                    )
                ]

            environment.get_user_tools = MethodType(patched_get_user_tools, environment)

    original_get_response = getattr(
        environment, "_translation_original_get_response", None
    )
    if original_get_response is None:
        original_get_response = environment.get_response
        environment._translation_original_get_response = original_get_response

        def patched_get_response(self, message: ToolCall) -> ToolMessage:
            localizer = self._translation_schema_localizer
            normalized_arguments = _normalize_arguments_for_tool_call(
                self,
                localizer,
                requestor=message.requestor,
                tool_name=message.name,
                arguments=message.arguments,
            )
            normalized_message = message.model_copy(
                update={"arguments": normalized_arguments}
            )
            response = self._translation_original_get_response(normalized_message)
            if not self._translation_localize_outputs or response.error:
                return response

            try:
                payload = json.loads(response.content)
                localized_content = json.dumps(
                    localizer.localize_response_payload(payload),
                    default=str,
                )
            except json.JSONDecodeError:
                localized_content = localizer.localize_response_payload(
                    response.content
                )

            return response.model_copy(update={"content": localized_content})

        environment.get_response = MethodType(patched_get_response, environment)

    original_normalize_payload_for_compare = getattr(
        environment,
        "_translation_original_normalize_tool_payload_for_compare",
        None,
    )
    if original_normalize_payload_for_compare is None:
        original_normalize_payload_for_compare = (
            environment.normalize_tool_payload_for_compare
        )
        environment._translation_original_normalize_tool_payload_for_compare = (
            original_normalize_payload_for_compare
        )

        def patched_normalize_tool_payload_for_compare(
            self,
            payload: Any,
            *,
            tool_call: ToolCall | None = None,
        ) -> Any:
            normalized = self._translation_original_normalize_tool_payload_for_compare(
                payload,
                tool_call=tool_call,
            )
            return self._translation_schema_localizer.canonicalize_payload_for_compare(
                normalized
            )

        environment.normalize_tool_payload_for_compare = MethodType(
            patched_normalize_tool_payload_for_compare,
            environment,
        )

    environment._translation_schema_localizer = localizer
    environment._translation_localize_outputs = localize_outputs


def apply_schema_runtime_localization(
    environment: Any,
    *,
    domain: str,
    translated_root: Path,
    src_domain_root: Path,
    localize_tools: bool,
    localize_outputs: bool,
    warn_if_stale: Callable[..., None] | None = None,
) -> SchemaRuntimeLocalizer | None:
    if not (localize_tools or localize_outputs):
        return None

    localizer = _build_schema_runtime_localizer(
        domain=domain,
        translated_root=translated_root,
        src_domain_root=src_domain_root,
        warn_if_stale=warn_if_stale,
    )
    if localizer is None:
        return None

    patch_environment_with_schema_localizer(
        environment,
        localizer,
        localize_tools=localize_tools,
        localize_outputs=localize_outputs,
    )
    return localizer
