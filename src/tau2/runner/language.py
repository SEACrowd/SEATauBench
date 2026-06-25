"""Language-aware runner helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from loguru import logger

from seatau.translation.language import (
    get_language_config,
    get_stale_translation_warnings,
    get_translated_asset_path,
)
from tau2.data_model.simulation import RunConfig
from tau2.environment.environment import Environment
from tau2.utils.utils import DATA_DIR


def _language_component_enabled(
    lang_components: Optional[set[str]],
    component: str,
) -> bool:
    """Return whether a language component is enabled."""
    return lang_components is None or component in lang_components


def _prepend_user_system_instruction(
    instructions: str,
    *,
    runtime_lang_id: Optional[str],
    lang_components: Optional[set[str]],
) -> str:
    """Inject user system instruction from languages.json when enabled."""
    if not (
        runtime_lang_id and _language_component_enabled(lang_components, "user_system")
    ):
        return instructions

    lang_config = get_language_config(runtime_lang_id)
    return f"{lang_config.user_system_instruction}\n\n{instructions}"


def apply_language_config(environment: Environment, config: RunConfig) -> Optional[str]:
    """Patch environment with translated assets when lang_id is set.

    Patches tool docstrings, swaps policy, and swaps DB if translated
    versions exist under ``data/tau2/domains/{domain}/{lang_id}/``.

    Args:
        environment: The environment to patch in-place.
        config: Run config with optional lang_id.

    Returns:
        The localized greeting string, or None if lang_id is not set.
    """
    if config.lang_id is None:
        return None

    lang_components = config.effective_lang_components
    if not lang_components:
        return None

    domain = config.domain
    asset_language_id = config.language_asset_id
    runtime_lang_id = config.runtime_lang_id
    domain_root = DATA_DIR / "tau2" / "domains" / domain
    translated_root = domain_root / asset_language_id
    src_domain_root = Path(__file__).resolve().parents[1] / "domains" / domain

    def _warn_if_stale(*filenames: str) -> None:
        for warning in get_stale_translation_warnings(
            domain, asset_language_id, filenames
        ):
            logger.warning(warning)

    if {"tools", "db"} & lang_components:
        from seatau.translation.runtime_localization import (
            apply_schema_runtime_localization,
        )

        apply_schema_runtime_localization(
            environment,
            domain=domain,
            translated_root=translated_root,
            src_domain_root=src_domain_root,
            localize_tools="tools" in lang_components,
            localize_outputs="db" in lang_components,
            warn_if_stale=_warn_if_stale,
        )

    if "tool_mix" in lang_components and config.tool_mix_config:
        from seatau.l2_tools_mix import (
            load_mixed_docstrings,
            load_tool_mix_config,
        )
        from seatau.translation.loader import patch_toolkit_docstrings

        mixed_config = load_tool_mix_config(config.tool_mix_config)
        tool_class = type(environment.tools)
        tool_names = sorted(environment.tools.get_tools().keys())

        docs, partition = load_mixed_docstrings(
            domain, tool_names, mixed_config, src_domain_root / "tools.py"
        )
        patch_toolkit_docstrings(tool_class, docs)
        logger.info(
            f"Tool-mix partition: {partition.summary.by_language} "
            f"(groups: {partition.group_assignments})"
        )
        environment._tool_mix_partition = partition  # type: ignore[attr-defined]

    elif "tools" in lang_components:
        tools_path = get_translated_asset_path(domain, asset_language_id, "tools.json")
        if asset_language_id in str(tools_path) and tools_path.exists():
            _warn_if_stale("tools.json")
            from seatau.translation.loader import (
                load_docstrings_json,
                patch_toolkit_docstrings,
            )

            docs = load_docstrings_json(tools_path)
            patch_toolkit_docstrings(type(environment.tools), docs)

    policy_candidates = sorted(domain_root.glob("*.md"))
    policy = environment.policy
    translated_policy_names: list[str] = []
    if "policy" in lang_components:
        for source_policy_path in policy_candidates:
            translated_policy_path = translated_root / source_policy_path.name
            if not translated_policy_path.exists():
                continue
            source_policy = source_policy_path.read_text(encoding="utf-8")
            translated_policy = translated_policy_path.read_text(encoding="utf-8")
            if source_policy in policy:
                policy = policy.replace(source_policy, translated_policy)
            elif source_policy_path.name == "policy.md":
                policy = translated_policy
            translated_policy_names.append(source_policy_path.name)
        if translated_policy_names:
            _warn_if_stale(*translated_policy_names)
    if "agent_system" in lang_components:
        lang_config = get_language_config(runtime_lang_id)
        policy = policy + "\n\n" + lang_config.agent_system_instruction
    environment.policy = policy

    if "db" in lang_components:
        db_candidates = ("db.json", "db.toml")
        for filename in db_candidates:
            db_path = translated_root / filename
            if not db_path.exists() or not hasattr(environment.tools, "db"):
                continue
            _warn_if_stale(filename)
            db_class = type(environment.tools.db)
            environment.tools.db = db_class.load(str(db_path))
            break

        if hasattr(environment, "user_tools") and environment.user_tools is not None:
            for filename in ("user_db.json", "user_db.toml"):
                user_db_path = translated_root / filename
                if not user_db_path.exists() or not hasattr(
                    environment.user_tools, "db"
                ):
                    continue
                _warn_if_stale(filename)
                user_db_class = type(environment.user_tools.db)
                environment.user_tools.db = user_db_class.load(str(user_db_path))
                break

    if "greeting" in lang_components:
        lang_config = get_language_config(runtime_lang_id)
        return lang_config.greeting
    return None
