"""Language registry and translation asset utilities."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from seatau.paths import DATA_DIR as PROJECT_DATA_DIR
from seatau.paths import LANGUAGES_PATH as DEFAULT_LANGUAGES_PATH
from seatau.paths import resolve_project_path
from seatau.translation.config import DB_FILE_NAMES, MARKDOWN_GLOBS


def _resolve_data_dir() -> Path:
    data_dir_env = os.getenv("TAU2_DATA_DIR")
    if data_dir_env:
        return Path(data_dir_env)
    return PROJECT_DATA_DIR


DATA_DIR = _resolve_data_dir()

LANGUAGES_PATH = DEFAULT_LANGUAGES_PATH
TRANSLATION_MANIFEST_NAME = "translation_manifest.json"
LANGUAGE_COMPONENT_CHOICES = (
    "user_system",
    "agent_system",
    "greeting",
    "tools",
    "mixed_tools",  # For SEA-Tau Experiment 1: mixed-language tools
    "policy",
    "db",
    "tasks",
    "context",
    "all",
)
DEFAULT_LANGUAGE_COMPONENTS = (
    "user_system",
    "agent_system",
    "greeting",
    "tools",
    "policy",
    "db",
    "tasks",
)
DEFAULT_USER_SYSTEM_INSTRUCTION_TEMPLATE = (
    "You must converse with the agent entirely in {instruction_label}. "
    "Do not use English except for proper nouns, product IDs, or technical terms "
    "that have no {display_name} equivalent. "
    "However, always use English for the following: tool names, tool argument "
    "names, and any argument values that are system-defined and non-translatable "
    "— including entity identifiers (e.g., IDs, reference codes, alphanumeric "
    "keys), enumerated constants (e.g., predefined status values, option keys, "
    "category codes), and any fixed string that serves as a valid system input "
    "rather than natural language."
)
DEFAULT_AGENT_SYSTEM_INSTRUCTION_TEMPLATE = (
    "You must respond to the user entirely in the same language they use. If the "
    "user writes in {display_name}, you must reply in {display_name}. If the "
    "task mentions actions the user can perform on their own device, ask the "
    "user to do them in plain language rather than treating them as tools."
)


@dataclass(frozen=True)
class LanguageConfig:
    code: str
    display_name: str
    instruction_label: str
    greeting: str
    user_instruction: str | None = None
    agent_instruction: str | None = None

    @property
    def user_system_instruction(self) -> str:
        """Return the effective user system instruction for this language."""
        if self.user_instruction:
            return self.user_instruction
        return DEFAULT_USER_SYSTEM_INSTRUCTION_TEMPLATE.format(
            instruction_label=self.instruction_label,
            display_name=self.display_name,
        )

    @property
    def agent_system_instruction(self) -> str:
        """Return the effective agent system instruction for this language."""
        if self.agent_instruction:
            return self.agent_instruction
        return DEFAULT_AGENT_SYSTEM_INSTRUCTION_TEMPLATE.format(
            display_name=self.display_name,
        )


def resolve_language_components(
    components: Iterable[str] | None,
) -> set[str]:
    """Resolve selected language components to a validated set.

    When ``components`` is ``None``, all supported components are enabled.
    """
    if components is None:
        return set(DEFAULT_LANGUAGE_COMPONENTS)

    resolved = set(components)
    unknown = resolved - set(LANGUAGE_COMPONENT_CHOICES)
    if unknown:
        available = ", ".join(LANGUAGE_COMPONENT_CHOICES)
        raise ValueError(
            f"Unknown language component(s): {sorted(unknown)}. Available: {available}"
        )
    if "all" in resolved:
        resolved.update(DEFAULT_LANGUAGE_COMPONENTS)
    if "context" in resolved:
        resolved.update({"policy", "db", "tasks"})
    resolved.discard("all")
    resolved.discard("context")
    return resolved


def translated_asset_path(
    data_domains_root: Path,
    lang: str,
    domain: str,
    filename: str,
) -> Path:
    """Return ``{data_domains_root}/{domain}/{lang}/{filename}`` without existence check.

    Use this when writing translated assets or constructing expected paths.
    For reading with English fallback, use :func:`get_translated_asset_path`.

    Args:
        data_domains_root: Root of domain data (e.g. ``Path("data/tau2/domains")``).
        lang: Language code (e.g. ``"th"``). Case-insensitive.
        domain: Domain name (e.g. ``"retail"``).
        filename: File name (e.g. ``"tools.json"``).

    Returns:
        Path to the translated file (may not exist yet).
    """
    return data_domains_root / domain / lang.lower() / filename


def get_missing_translation_component_warnings(
    domain: str,
    language: str,
    components: Iterable[str],
) -> list[str]:
    """Return warnings for enabled translated-asset components with no artifacts."""
    warnings: list[str] = []
    resolved = resolve_language_components(components)
    translated_root = DATA_DIR / "tau2" / "domains" / domain / language

    if "tools" in resolved and not (translated_root / "tools.json").exists():
        warnings.append(
            "Language component 'tools' was requested, but translated asset "
            f"'{translated_root / 'tools.json'}' does not exist."
        )

    if "tasks" in resolved and not (translated_root / "tasks.json").exists():
        warnings.append(
            "Language component 'tasks' was requested, but translated asset "
            f"'{translated_root / 'tasks.json'}' does not exist."
        )

    policy_exists = any(
        file_path
        for pattern in MARKDOWN_GLOBS
        for file_path in translated_root.glob(pattern)
    )
    if "policy" in resolved and not policy_exists:
        patterns = ", ".join(MARKDOWN_GLOBS)
        warnings.append(
            "Language component 'policy' was requested, but no translated policy "
            f"artifacts were found under '{translated_root}' matching: {patterns}."
        )

    if "db" in resolved and not any(
        (translated_root / filename).exists() for filename in DB_FILE_NAMES
    ):
        expected = ", ".join(DB_FILE_NAMES)
        warnings.append(
            "Language component 'db' was requested, but no translated DB artifacts "
            f"were found under '{translated_root}' (expected one of: {expected})."
        )
    return warnings


@lru_cache(maxsize=1)
def load_language_registry() -> dict[str, LanguageConfig]:
    """Load the language registry from languages.json."""
    with LANGUAGES_PATH.open(encoding="utf-8") as f:
        raw: dict[str, dict] = json.load(f)
    return {code: LanguageConfig(**entry) for code, entry in raw.items()}


def get_language_config(language: str) -> LanguageConfig:
    """Get language config by code. Raises KeyError if not found."""
    registry = load_language_registry()
    if language not in registry:
        available = ", ".join(sorted(registry.keys()))
        raise KeyError(f"Unknown language code '{language}'. Available: {available}")
    return registry[language]


def list_non_english_languages() -> list[str]:
    """Return all registered language codes except ``en``, sorted."""
    return sorted(code for code in load_language_registry() if code != "en")


def get_translated_asset_path(
    domain: str,
    language: str,
    filename: str,
) -> Path:
    """Return the path to a translated asset, falling back to the English original.

    Args:
        domain: Domain name (e.g. ``"retail"``).
        language: Language code (e.g. ``"th"``).
        filename: File name (e.g. ``"tasks.json"``).

    Returns:
        Translated path if it exists, otherwise the untranslated path.
    """
    translated = DATA_DIR / "tau2" / "domains" / domain / language / filename
    if translated.exists():
        return translated
    return DATA_DIR / "tau2" / "domains" / domain / filename


def get_translation_manifest_path(domain: str, language: str) -> Path:
    """Return the manifest path for translated assets for a domain+language."""
    return DATA_DIR / "tau2" / "domains" / domain / language / TRANSLATION_MANIFEST_NAME


def load_translation_manifest(domain: str, language: str) -> dict | None:
    """Load translation manifest metadata if present."""
    manifest_path = get_translation_manifest_path(domain, language)
    if not manifest_path.exists():
        return None
    with manifest_path.open(encoding="utf-8") as f:
        return json.load(f)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_stale_translation_warnings(
    domain: str,
    language: str,
    filenames: Iterable[str],
) -> list[str]:
    """Return warnings for translated assets whose source fingerprints are stale."""
    warnings: list[str] = []
    manifest = load_translation_manifest(domain, language)
    translated_root = DATA_DIR / "tau2" / "domains" / domain / language

    for filename in filenames:
        translated_path = translated_root / filename
        if not translated_path.exists():
            continue
        if manifest is None:
            warnings.append(
                f"Translation manifest missing for {translated_path}. "
                "Rerun translation to record source fingerprints."
            )
            continue
        asset = manifest.get("assets", {}).get(filename)
        if asset is None:
            warnings.append(
                f"No source fingerprint recorded for {translated_path}. "
                "Rerun translation after updating source tools/context."
            )
            continue
        stale_sources: list[str] = []
        for source in asset.get("source_files", []):
            source_path = resolve_project_path(source["path"])
            if not source_path.exists():
                stale_sources.append(str(source_path))
                continue
            if _sha256(source_path) != source.get("sha256"):
                stale_sources.append(str(source_path))
        if stale_sources:
            warnings.append(
                f"Translated asset {translated_path} is stale because source file(s) changed: "
                + ", ".join(stale_sources)
                + ". Rerun translation for this language."
            )
    return warnings
