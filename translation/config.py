from __future__ import annotations

from pathlib import Path

from translation.models import PipelineConfig

# File names expected in Tau2 domain folders.
DATA_JSON_FILES = ("tasks.json", "db.json", "user_db.json")
MARKDOWN_GLOBS = ("policy*.md",)
PYTHON_FILES = ("data_model.py", "tools.py", "user_data_model.py", "user_tools.py")

# Paths inside task objects (in tasks.json) that should be translated.
TASK_TRANSLATABLE_PATTERNS: tuple[tuple[str, ...], ...] = (
    ("description", "purpose"),
    ("description", "notes"),
    ("description", "relevant_policies"),
    ("user_scenario", "persona"),
    ("user_scenario", "instructions"),
    ("user_scenario", "instructions", "reason_for_call"),
    ("user_scenario", "instructions", "known_info"),
    ("user_scenario", "instructions", "unknown_info"),
    ("user_scenario", "instructions", "task_instructions"),
    ("ticket",),
    ("evaluation_criteria", "nl_assertions", "*"),
    ("evaluation_criteria", "communicate_info", "*"),
    ("evaluation_criteria", "actions", "*", "info"),
    ("evaluation_criteria", "actions", "*", "arguments", "summary"),
    ("initial_state", "message_history", "*", "content"),
    (
        "initial_state",
        "initialization_data",
        "agent_data",
        "tasks",
        "*",
        "title",
    ),
    (
        "initial_state",
        "initialization_data",
        "agent_data",
        "tasks",
        "*",
        "description",
    ),
    ("initial_state", "initialization_actions", "*", "arguments", "title"),
    ("initial_state", "initialization_actions", "*", "arguments", "description"),
    ("initial_state", "initialization_actions", "*", "arguments", "summary"),
)

# Conservative text keys for db/user_db values that are usually natural language.
DB_TRANSLATABLE_LEAF_KEYS = {
    "title",
    "description",
    "name",
    "summary",
    "notes",
}

# Keys whose string values are structural/canonical and must never be translated.
CANONICAL_KEYS = {
    "id",
    "action_id",
    "task_id",
    "user_id",
    "status",
    "env_type",
    "func_name",
    "requestor",
    "role",
}

# Common canonical values to preserve across languages.
FIXED_PROTECTED_TERMS = {
    "pending",
    "completed",
    "DB",
    "ACTION",
    "ENV_ASSERTION",
    "NL_ASSERTION",
    "COMMUNICATE",
}

# Regex patterns for placeholder masking.
DEFAULT_PROTECTED_PATTERNS = (
    r"\b(?:task|user|call|action|ticket|order|account|case|booking|reservation|flight)_[A-Za-z0-9_-]+\b",
    r"\b(?:###STOP###|###TRANSFER###|###OUT-OF-SCOPE###)\b",
)


def default_config(
    domains: list[str],
    source_language: str = "English",
    target_language: str = "Thai",
    data_domains_root: str | Path = "data/tau2/domains",
    src_domains_root: str | Path = "src/tau2/domains",
    output_root: str | Path = "translation/output",
    model: str = "gemini-3-flash-preview",
    api_key_env: str = "GEMINI_API_KEY",
    api_base: str | None = None,
    api_version: str | None = None,
    max_rpm: float | None = 5.0,
    batch_size: int = 24,
    dry_run: bool = False,
    max_preview: int = 20,
) -> PipelineConfig:
    return PipelineConfig(
        domains=domains,
        source_language=source_language,
        target_language=target_language,
        data_domains_root=Path(data_domains_root),
        src_domains_root=Path(src_domains_root),
        output_root=Path(output_root),
        model=model,
        api_key_env=api_key_env,
        api_base=api_base,
        api_version=api_version,
        max_rpm=max_rpm,
        batch_size=batch_size,
        dry_run=dry_run,
        max_preview=max_preview,
    )
