from __future__ import annotations

from pathlib import Path

# Translation pipeline defaults and exclusions.
DEFAULT_SOURCE_LANGUAGE = "English"
DEFAULT_DATA_DOMAINS_ROOT = Path("data/tau2/domains")
DEFAULT_SRC_DOMAINS_ROOT = Path("src/tau2/domains")
DEFAULT_VERTEX_MODEL = "vertex_ai/gemini-3.1-flash-lite-preview"
DEFAULT_MODEL = DEFAULT_VERTEX_MODEL
DEFAULT_MAX_CONCURRENCY = 8
DEFAULT_BATCH_SIZE = 24
DEFAULT_MAX_PREVIEW = 20
DEFAULT_TIMEOUT_S = 120
DEFAULT_RETRIES = 3
SKIPPED_TRANSLATION_DOMAINS = frozenset({"banking_knowledge", "mock"})

# Domain-level assets supported by the translation pipeline.
TASK_FILE_GLOBS = ("tasks*.json",)
DB_FILE_NAMES = ("db.json", "db.toml", "user_db.json", "user_db.toml")
MARKDOWN_GLOBS = ("*.md",)
TOOL_PYTHON_FILES = ("tools.py", "user_tools.py")
SCHEMA_PYTHON_FILES = ("data_model.py", "user_data_model.py")
PYTHON_FILES = TOOL_PYTHON_FILES + SCHEMA_PYTHON_FILES
SKIPPED_TASK_FILES = {"tasks_voice.json", "split_tasks.json"}
DOMAIN_SKIPPED_TASK_FILES = {
    "telecom": {"tasks_full.json", "tasks_small.json", "tasks_voice.json"}
}

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

# Domain-specific DB fields that are natural language but not shared across
# every domain schema.
DOMAIN_DB_TRANSLATABLE_LEAF_KEYS: dict[str, frozenset[str]] = {
    # Airline DB has user profile address text that improves multilingual UX
    # and is safe to translate (not enum/runtime literals).
    "airline": frozenset({"address1", "address2", "city"}),
}


def get_domain_db_translatable_leaf_keys(domain: str) -> frozenset[str]:
    """Return DB leaf keys that should be translated for a given domain."""
    return frozenset(DB_TRANSLATABLE_LEAF_KEYS) | DOMAIN_DB_TRANSLATABLE_LEAF_KEYS.get(
        domain, frozenset()
    )


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
COMMON_FIXED_PROTECTED_TERMS = frozenset(
    {
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
)

# Domain-specific fixed literals that should always be preserved whenever they
# appear as standalone tokens.
DOMAIN_FIXED_PROTECTED_TERMS: dict[str, frozenset[str]] = {
    "retail": frozenset(),
    "airline": frozenset(),
}

# Domain-specific contextual literals. These are runtime values that should be
# preserved only when they appear in the right semantic context, such as a
# status list, a cabin-class example, or a structured status field.
DOMAIN_CONTEXTUAL_PROTECTED_TERMS: dict[str, dict[str, frozenset[str]]] = {
    "airline": {
        "status": frozenset(
            {
                "available",
                "on time",
                "flying",
                "landed",
                "delayed",
                "cancelled",
            }
        ),
        "cabin": frozenset(
            {
                "basic_economy",
                "economy",
                "business",
                "basic economy",
            }
        ),
        "flight_type": frozenset(
            {
                "round_trip",
                "one_way",
                "round trip",
                "one way",
            }
        ),
        "membership": frozenset({"gold", "silver", "regular"}),
        "payment_source": frozenset(
            {
                "credit_card",
                "gift_card",
                "certificate",
                "credit card",
                "gift card",
                "travel certificate",
            }
        ),
    }
}

CONTEXTUAL_BUCKET_PATH_HINTS: dict[str, frozenset[str]] = {
    "status": frozenset({"status"}),
    "cabin": frozenset({"cabin"}),
    "flight_type": frozenset({"flight_type", "trip_type", "flight type", "trip type"}),
    "membership": frozenset({"membership", "member", "member_level"}),
    "payment_source": frozenset({"source", "payment_method", "payment_methods"}),
}

CONTEXTUAL_BUCKET_TEXT_CUES: dict[str, tuple[str, ...]] = {
    "status": (r"\bstatus\b",),
    "cabin": (r"\bcabin\b", r"\bcabin class\b", r"\bclass\b"),
    "flight_type": (r"\bflight type\b", r"\btrip type\b"),
    "membership": (r"\bmembership\b", r"\bmembership level\b", r"\bmember(?:ship)?\b"),
    "payment_source": (
        r"\bpayment method\b",
        r"\bpayment methods\b",
        r"\bpayment source\b",
    ),
}

# Backward-compatible union of unconditional fixed terms only.
FIXED_PROTECTED_TERMS = COMMON_FIXED_PROTECTED_TERMS | frozenset().union(
    *DOMAIN_FIXED_PROTECTED_TERMS.values()
)

# Tool docstring keywords that should remain canonical in translated tool
# descriptions. This applies only to the tool translation component.
TOOL_DOC_PROTECTED_TERMS = frozenset(
    {
        "Args",
        "Returns",
        "Raises",
        "Parameters",
        "Parameter",
        "Errors",
        "Error",
        "Checks",
        "Logic",
        "Warning",
        "Warnings",
        "Note",
        "Notes",
        "Example",
        "Examples",
    }
)


def get_domain_fixed_protected_terms(domain: str) -> frozenset[str]:
    """Return unconditional protected terms scoped to the current domain."""
    return COMMON_FIXED_PROTECTED_TERMS | DOMAIN_FIXED_PROTECTED_TERMS.get(
        domain, frozenset()
    )


def get_domain_contextual_protected_terms(
    domain: str,
) -> dict[str, frozenset[str]]:
    """Return contextual protected terms bucketed by semantic use."""
    return DOMAIN_CONTEXTUAL_PROTECTED_TERMS.get(domain, {})


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
