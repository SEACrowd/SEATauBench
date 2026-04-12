from __future__ import annotations

# Domain-level assets supported by the translation pipeline.
TASK_FILE_GLOBS = ("tasks*.json",)
DB_FILE_NAMES = ("db.json", "db.toml", "user_db.json", "user_db.toml")
MARKDOWN_GLOBS = ("policy*.md", "main_policy*.md", "tech_support*.md")
PYTHON_FILES = ("tools.py", "user_tools.py")
SKIPPED_TASK_FILES = {"tasks_voice.json", "split_tasks.json"}
SKIPPED_DOMAINS = {"banking_knowledge"}

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
    "processed",
    "pending (item modified)",
    "pending (items modified)",
    "delivered",
    "cancelled",
    "exchange requested",
    "return requested",
    "no longer needed",
    "ordered by mistake",
}

# Canonical task markers that should be preserved inside task JSON, but should
# not leak into general prose like policies.
TASK_ONLY_PROTECTED_TERMS = {
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
