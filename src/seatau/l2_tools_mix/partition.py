"""Tool partitioning and docstring loading for mixed-language tools experiment.

This module provides functionality for partitioning tool descriptions across
multiple languages for SEA-Tau Experiment 1.
"""

from __future__ import annotations

import ast
import json
import random
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from paths import L2_TOOLS_MIX_DIR, resolve_project_path
from seatau.constants import get_domain_data_path
from seatau.l2_tools_mix.models import (
    MixedToolsConfig,
    MixedToolsLanguageConfig,
    MixedToolsPartition,
    MixedToolsPartitioningConfig,
    MixedToolsPartitionSummary,
    MixedToolsReproducibility,
    ToolAssignment,
    TranslationProvenance,
)
from seatau.translation.extractors import extract_decorated_tool_method_names


def load_tool_groups(domain: str) -> dict[str, list[str]] | None:
    """Load tool group definitions for a domain.

    Args:
        domain: Domain name (e.g., "airline", "retail").

    Returns:
        {group_name: [tool_names]} or None if no groups defined.
    """
    groups_path = get_domain_data_path(domain) / "tool_groups.json"
    if not groups_path.exists():
        return None
    return json.loads(groups_path.read_text(encoding="utf-8"))


_FIVE_LANG_FALLBACK_NAME = "5lang_uniform_en-th-vi-id-zh"
_FIVE_LANG_FALLBACK_LANGS = frozenset({"th", "vi", "id", "zh"})


def find_tool_mix_config(name: str) -> Path | None:
    """Return the path to a tool-mix config JSON, or None if missing.

    Args:
        name: Config name with or without the ``.json`` suffix.
    """
    filename = name if name.endswith(".json") else f"{name}.json"
    path = resolve_project_path(L2_TOOLS_MIX_DIR) / filename
    return path if path.exists() else None


def default_tool_mix_config_for_lang(lang: str) -> str | None:
    """Resolve the default tool-mix config name for a target language.

    Prefers a 2-language uniform config (``2lang_uniform_en-{lang}``) when
    available, otherwise falls back to the 5-language uniform config for the
    SEA-TAU core languages (th, vi, id, zh).
    """
    two_lang = f"2lang_uniform_en-{lang}"
    if find_tool_mix_config(two_lang) is not None:
        return two_lang
    if lang in _FIVE_LANG_FALLBACK_LANGS and find_tool_mix_config(
        _FIVE_LANG_FALLBACK_NAME
    ):
        return _FIVE_LANG_FALLBACK_NAME
    return None


def load_tool_mix_config(config_name: str) -> MixedToolsConfig:
    """Load a tool-mix config by name.

    Args:
        config_name: Config name (e.g., "3lang_uniform_en-th-vi").
                     Extension .json is added if not present.

    Returns:
        Parsed MixedToolsConfig.

    Raises:
        FileNotFoundError: If config file does not exist.
    """
    if not config_name.endswith(".json"):
        config_name = f"{config_name}.json"
    config_path = resolve_project_path(L2_TOOLS_MIX_DIR) / config_name
    if not config_path.exists():
        raise FileNotFoundError(f"Tool-mix config not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))

    # Parse nested dataclasses
    languages = MixedToolsLanguageConfig(**data["languages"])
    partitioning = MixedToolsPartitioningConfig(**data["partitioning"])
    provenance = {
        lang: TranslationProvenance(**prov)
        for lang, prov in data["translation_provenance"].items()
    }
    reproducibility = MixedToolsReproducibility(**data["reproducibility"])

    config = MixedToolsConfig(
        schema_version=data["schema_version"],
        name=data["name"],
        description=data["description"],
        languages=languages,
        partitioning=partitioning,
        translation_provenance=provenance,
        reproducibility=reproducibility,
    )
    config.validate()
    return config


def build_translation_provenance(
    languages: list[str],
    domain: str,
) -> dict[str, TranslationProvenance]:
    """Build provenance info from translation manifests.

    Args:
        languages: List of language codes (e.g., ["en", "th", "vi"]).
        domain: Domain name.

    Returns:
        {lang_id: TranslationProvenance} mapping.
    """
    provenance: dict[str, TranslationProvenance] = {}
    for lang in languages:
        if lang == "en":
            provenance["en"] = TranslationProvenance(
                source="original", model=None, translated_at=None
            )
        else:
            manifest_path = (
                get_domain_data_path(domain, lang) / "translation_manifest.json"
            )
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                provenance[lang] = TranslationProvenance(
                    source=f"data/tau2/domains/{domain}/{lang}/tools.json",
                    model=manifest.get("model"),
                    translated_at=manifest.get("generated_at"),
                    pipeline_version=manifest.get("pipeline_version"),
                )
            else:
                provenance[lang] = TranslationProvenance(
                    source="missing", model=None, translated_at=None
                )
    return provenance


def partition_tools_by_language(
    tool_names: list[str],
    languages: list[str],
    weights: list[float] | None = None,
    seed: int = 42,
    tool_groups: dict[str, list[str]] | None = None,
    partition_strategy: str = "weighted_random",
    tools_per_added_language: int | None = None,
) -> tuple[dict[str, ToolAssignment], dict[str, str] | None]:
    """Partition tools into non-overlapping language groups.

    Args:
        tool_names: All tool function names.
        languages: Language codes to distribute across.
        weights: Probability weights per language (default: uniform).
        seed: Random seed for reproducibility.
        tool_groups: Optional {group_name: [tool_names]} for grouped assignment.
            If provided, entire groups are assigned to same language.
        partition_strategy: Assignment strategy. ``weighted_random`` preserves the
            legacy independent weighted draws. ``nested_progressive`` makes
            language complexity monotonic across prefix configs by only moving
            additional English tools into newly introduced non-English languages.
        tools_per_added_language: Optional fixed number of partition units to
            assign to each non-English language under ``nested_progressive``.

    Returns:
        Tuple of:
        - {tool_name: ToolAssignment} complete tool assignments
        - {group_name: lang_id} group assignments (None if not using groups)

    Raises:
        ValueError: If weights don't match languages or don't sum to ~1.0.
    """
    if not languages:
        raise ValueError("languages must not be empty")
    if weights is None:
        weights = [1.0 / len(languages)] * len(languages)
    if len(weights) != len(languages):
        raise ValueError(
            f"weights length {len(weights)} != languages length {len(languages)}"
        )
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be non-negative")
    if abs(sum(weights) - 1.0) > 0.01:
        raise ValueError(f"weights must sum to 1.0, got {sum(weights)}")

    if partition_strategy not in {"weighted_random", "nested_progressive"}:
        raise ValueError(f"Unknown partition_strategy: {partition_strategy}")

    if partition_strategy == "nested_progressive":
        if languages[0] != "en":
            raise ValueError("nested_progressive requires English as the base language")
        if tools_per_added_language is not None and tools_per_added_language <= 0:
            raise ValueError("tools_per_added_language must be positive")
        return _partition_tools_nested_progressive(
            tool_names=tool_names,
            languages=languages,
            weights=weights,
            seed=seed,
            tool_groups=tool_groups,
            tools_per_added_language=tools_per_added_language,
        )

    return _partition_tools_weighted_random(
        tool_names=tool_names,
        languages=languages,
        weights=weights,
        seed=seed,
        tool_groups=tool_groups,
    )


def _partition_tools_weighted_random(
    *,
    tool_names: list[str],
    languages: list[str],
    weights: list[float],
    seed: int,
    tool_groups: dict[str, list[str]] | None,
) -> tuple[dict[str, ToolAssignment], dict[str, str] | None]:
    """Legacy independent weighted-random partitioning."""
    rng = random.Random(seed)
    tool_assignments: dict[str, ToolAssignment] = {}
    group_assignments: dict[str, str] | None = None

    if tool_groups:
        group_assignments = {}
        group_names = list(tool_groups.keys())
        rng.shuffle(group_names)

        for group_name in group_names:
            lang = rng.choices(languages, weights=weights, k=1)[0]
            group_assignments[group_name] = lang
            for tool in tool_groups[group_name]:
                if tool in tool_names:  # Only include tools that exist
                    tool_assignments[tool] = ToolAssignment(lang=lang, group=group_name)

        # Handle ungrouped tools (assign individually)
        grouped_tools = {t for tools in tool_groups.values() for t in tools}
        ungrouped = [t for t in tool_names if t not in grouped_tools]
        rng.shuffle(ungrouped)
        for tool in ungrouped:
            lang = rng.choices(languages, weights=weights, k=1)[0]
            tool_assignments[tool] = ToolAssignment(lang=lang, group=None)
    else:
        # Individual mode: assign each tool independently
        shuffled = list(tool_names)
        rng.shuffle(shuffled)
        for tool in shuffled:
            lang = rng.choices(languages, weights=weights, k=1)[0]
            tool_assignments[tool] = ToolAssignment(lang=lang, group=None)

    return tool_assignments, group_assignments


def _partition_tools_nested_progressive(
    *,
    tool_names: list[str],
    languages: list[str],
    weights: list[float],
    seed: int,
    tool_groups: dict[str, list[str]] | None,
    tools_per_added_language: int | None,
) -> tuple[dict[str, ToolAssignment], dict[str, str] | None]:
    """Partition tools with monotonic language-complexity semantics."""
    units = _build_partition_units(tool_names, tool_groups)
    rng = random.Random(seed)
    rng.shuffle(units)

    assignments_by_unit: dict[str, str] = {}
    cursor = 0
    progressive_counts = _nested_progressive_non_english_counts(
        total=len(units),
        languages=languages,
        weights=weights,
        tools_per_added_language=tools_per_added_language,
    )

    for lang, target_count in zip(languages[1:], progressive_counts):
        for unit_name, _unit_tools in units[cursor : cursor + target_count]:
            assignments_by_unit[unit_name] = lang
        cursor += target_count

    tool_assignments: dict[str, ToolAssignment] = {}
    group_assignments: dict[str, str] | None = {} if tool_groups else None
    for unit_name, unit_tools in units:
        lang = assignments_by_unit.get(unit_name, languages[0])
        group = (
            unit_name.removeprefix("group:") if unit_name.startswith("group:") else None
        )
        if group_assignments is not None and group is not None:
            group_assignments[group] = lang
        for tool in unit_tools:
            tool_assignments[tool] = ToolAssignment(lang=lang, group=group)

    return tool_assignments, group_assignments


def _build_partition_units(
    tool_names: list[str],
    tool_groups: dict[str, list[str]] | None,
) -> list[tuple[str, list[str]]]:
    """Build shuffle units from groups plus ungrouped tools."""
    tool_name_set = set(tool_names)
    if not tool_groups:
        return [(f"tool:{tool}", [tool]) for tool in sorted(tool_names)]

    units: list[tuple[str, list[str]]] = []
    grouped_tools: set[str] = set()
    for group_name in sorted(tool_groups):
        tools = sorted(
            tool for tool in tool_groups[group_name] if tool in tool_name_set
        )
        if not tools:
            continue
        units.append((f"group:{group_name}", tools))
        grouped_tools.update(tools)

    for tool in sorted(tool_name_set - grouped_tools):
        units.append((f"tool:{tool}", [tool]))
    return units


def _nested_progressive_non_english_counts(
    *,
    total: int,
    languages: list[str],
    weights: list[float],
    tools_per_added_language: int | None,
) -> list[int]:
    """Return additive counts for each non-English language."""
    if len(languages) == 1:
        return []

    if tools_per_added_language is not None:
        remaining = total
        counts: list[int] = []
        for _lang in languages[1:]:
            count = min(tools_per_added_language, remaining)
            counts.append(count)
            remaining -= count
        return counts

    quotas: list[int] = []
    for prefix_size in range(2, len(languages)):
        quotas.append(total - int(total / prefix_size))

    current_non_english = total - int(total * weights[0])
    quotas.append(current_non_english)

    monotonic_quotas: list[int] = []
    highest = 0
    for quota in quotas:
        highest = max(highest, min(total, quota))
        monotonic_quotas.append(highest)

    counts: list[int] = []
    previous = 0
    for quota in monotonic_quotas:
        counts.append(quota - previous)
        previous = quota
    return counts


def extract_function_docstrings(tools_py_path: Path) -> dict[str, str]:
    """Extract function docstrings from a tools.py file.

    Args:
        tools_py_path: Path to the tools.py source file.

    Returns:
        {function_name: docstring} mapping for decorated tool methods.
    """
    source = tools_py_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstrings: dict[str, str] = {}
    decorated_tool_names = extract_decorated_tool_method_names(tree)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get class docstring
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            ):
                docstrings[node.name] = node.body[0].value.value

            # Get method docstrings
            for item in node.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name in decorated_tool_names
                ):
                    if (
                        item.body
                        and isinstance(item.body[0], ast.Expr)
                        and isinstance(item.body[0].value, ast.Constant)
                    ):
                        docstrings[item.name] = item.body[0].value.value

    return docstrings


def _load_docstrings_for_lang(
    domain: str,
    lang: str,
    src_tools_path: Path,
) -> dict[str, str]:
    """Load docstrings for a specific language.

    Args:
        domain: Domain name.
        lang: Language code ("en" for original, others for translated).
        src_tools_path: Path to original tools.py.

    Returns:
        {function_name: docstring} mapping.

    Raises:
        FileNotFoundError: If translated tools.json doesn't exist for non-English.
    """
    if lang == "en":
        return extract_function_docstrings(src_tools_path)

    tools_json = get_domain_data_path(domain, lang) / "tools.json"
    if tools_json.exists():
        return json.loads(tools_json.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Missing translation for {lang}: {tools_json}")


def load_mixed_docstrings(
    domain: str,
    tool_names: list[str],
    config: MixedToolsConfig,
    src_tools_path: Path,
) -> tuple[dict[str, str], MixedToolsPartition]:
    """Build mixed-language docstring mapping.

    Args:
        domain: Domain name.
        tool_names: All tool function names.
        config: Tool-mix configuration.
        src_tools_path: Path to original tools.py for English docstrings.

    Returns:
        Tuple of:
        - {tool_name: docstring} with mixed languages
        - MixedToolsPartition with full assignment details
    """
    # Load tool groups if group_mode is enabled
    tool_groups = None
    if config.partitioning.group_mode:
        tool_groups = load_tool_groups(domain)

    # Partition tools
    tool_assignments, group_assignments = partition_tools_by_language(
        tool_names=tool_names,
        languages=config.languages.codes,
        weights=config.languages.weights,
        seed=config.partitioning.seed,
        tool_groups=tool_groups,
        partition_strategy=config.partitioning.partition_strategy,
        tools_per_added_language=config.partitioning.tools_per_added_language,
    )

    # Load docstrings per language (cache to avoid re-reading)
    lang_docstrings: dict[str, dict[str, str]] = {}
    needed_langs = {assign.lang for assign in tool_assignments.values()}

    for lang in needed_langs:
        lang_docstrings[lang] = _load_docstrings_for_lang(domain, lang, src_tools_path)

    # Build final docstring mapping
    result: dict[str, str] = {}
    missing_by_lang: dict[str, list[str]] = {}
    for tool, assign in tool_assignments.items():
        docs_for_lang = lang_docstrings.get(assign.lang, {})
        if tool in docs_for_lang:
            result[tool] = docs_for_lang[tool]
        else:
            missing_by_lang.setdefault(assign.lang, []).append(tool)

    if missing_by_lang:
        details = "; ".join(
            f"{lang}: {', '.join(sorted(tools))}"
            for lang, tools in sorted(missing_by_lang.items())
        )
        raise ValueError(f"Missing tool-mix docstrings for {details}")

    # Build summary
    by_language: dict[str, int] = {}
    for assign in tool_assignments.values():
        by_language[assign.lang] = by_language.get(assign.lang, 0) + 1

    by_group: dict[str, int] | None = None
    if group_assignments:
        by_group = {}
        for assign in tool_assignments.values():
            if assign.group:
                by_group[assign.group] = by_group.get(assign.group, 0) + 1

    summary = MixedToolsPartitionSummary(
        total_tools=len(tool_assignments),
        by_language=by_language,
        by_group=by_group,
    )

    # Build partition record
    partition = MixedToolsPartition(
        config_name=config.name,
        config_path=str(L2_TOOLS_MIX_DIR / f"{config.name}.json"),
        domain=domain,
        realized_at=datetime.now(timezone.utc).isoformat(),
        tool_assignments=tool_assignments,
        group_assignments=group_assignments,
        summary=summary,
    )

    return result, partition


def save_tool_mix_partition(partition: MixedToolsPartition, output_path: Path) -> None:
    """Save a realized partition to JSON.

    Args:
        partition: The partition to save.
        output_path: Path to write the JSON file.
    """
    data = {
        "config_name": partition.config_name,
        "config_path": partition.config_path,
        "domain": partition.domain,
        "realized_at": partition.realized_at,
        "group_assignments": partition.group_assignments,
        "tool_assignments": {
            tool: asdict(assign) for tool, assign in partition.tool_assignments.items()
        },
        "summary": asdict(partition.summary),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def create_tool_mix_config(
    name: str,
    description: str,
    languages: list[str],
    weights: list[float] | None,
    domain: str,
    seed: int = 42,
    group_mode: bool = True,
    created_by: str | None = None,
    notes: str | None = None,
) -> MixedToolsConfig:
    """Create a new MixedToolsConfig with auto-populated provenance.

    Args:
        name: Config name (e.g., "3lang_uniform_en-th-vi").
        description: Human-readable description.
        languages: Language codes (e.g., ["en", "th", "vi"]).
        weights: Weights per language (default: uniform).
        domain: Domain to pull provenance from.
        seed: Random seed.
        group_mode: Whether to use tool groups.
        created_by: Author name.
        notes: Additional notes.

    Returns:
        MixedToolsConfig ready to be saved.
    """
    if weights is None:
        weights = [1.0 / len(languages)] * len(languages)
        weight_desc = "uniform"
    else:
        # Infer weight description
        max_weight = max(weights)
        max_lang = languages[weights.index(max_weight)]
        if max_weight > 0.5:
            weight_desc = f"{int(max_weight * 100)}pct_{max_lang}"
        else:
            weight_desc = "custom"

    return MixedToolsConfig(
        schema_version="1.0",
        name=name,
        description=description,
        languages=MixedToolsLanguageConfig(
            codes=languages,
            weights=weights,
            weight_description=weight_desc,
        ),
        partitioning=MixedToolsPartitioningConfig(
            seed=seed,
            group_mode=group_mode,
            group_source="data/tau2/domains/{domain}/tool_groups.json",
            partition_strategy="nested_progressive",
            tools_per_added_language=3,
        ),
        translation_provenance=build_translation_provenance(languages, domain),
        reproducibility=MixedToolsReproducibility(
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by=created_by,
            codebase_commit=None,
            notes=notes,
        ),
    )


def save_tool_mix_config(
    config: MixedToolsConfig, output_dir: Path | None = None
) -> Path:
    """Save a MixedToolsConfig to JSON.

    Args:
        config: Config to save.
        output_dir: Directory to save to. Defaults to L2_TOOLS_MIX_DIR.

    Returns:
        Path to the saved config file.
    """
    if output_dir is None:
        output_dir = resolve_project_path(L2_TOOLS_MIX_DIR)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{config.name}.json"

    data = {
        "schema_version": config.schema_version,
        "name": config.name,
        "description": config.description,
        "languages": asdict(config.languages),
        "partitioning": asdict(config.partitioning),
        "translation_provenance": {
            lang: asdict(prov) for lang, prov in config.translation_provenance.items()
        },
        "reproducibility": asdict(config.reproducibility),
    }

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output_path
