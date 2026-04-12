from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

FileKind = Literal["json", "markdown", "python", "toml"]
TranslationComponent = Literal["tools", "policy", "db", "tasks"]

# Centralized defaults - single source of truth
DEFAULT_SOURCE_LANGUAGE = "English"
DEFAULT_COMPONENTS: tuple[TranslationComponent, ...] = (
    "tools",
    "policy",
    "db",
    "tasks",
)
DEFAULT_DATA_DOMAINS_ROOT = Path("data/tau2/domains")
DEFAULT_SRC_DOMAINS_ROOT = Path("src/tau2/domains")
DEFAULT_MODEL = "openrouter/google/gemini-3.1-flash-lite-preview"
DEFAULT_API_KEY_ENV = "OPENROUTER_API_KEY"
DEFAULT_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MAX_RPM = 5.0
DEFAULT_BATCH_SIZE = 24
DEFAULT_MAX_PREVIEW = 20
DEFAULT_TIMEOUT_S = 120
DEFAULT_RETRIES = 3

# Component validation sets
COMPONENT_CHOICES = ("tools", "policy", "db", "tasks", "context", "all")
BASE_COMPONENTS = frozenset({"tools", "policy", "db", "tasks"})


@dataclass(frozen=True)
class SourceSpan:
    """Character span in a source file."""

    start: int
    end: int


@dataclass(frozen=True)
class DomainFile:
    """A domain file to be processed."""

    domain: str
    path: Path
    relative_path: Path
    kind: FileKind


@dataclass(frozen=True)
class Segment:
    """A translatable text segment."""

    segment_id: str
    domain: str
    file_path: Path
    relative_path: Path
    kind: FileKind
    address: tuple[str, ...] | SourceSpan | str
    text: str
    name: str | None = None  # function/class name for python kind segments
    source_text: str | None = None  # original full text for structured segments
    python_doc_key: str | None = None  # docstring part key for python segments


@dataclass
class ExtractionResult:
    """Segments plus terms that should stay canonical."""

    segments: list[Segment] = field(default_factory=list)
    protected_terms: set[str] = field(default_factory=set)

    def extend(self, other: "ExtractionResult") -> None:
        self.segments.extend(other.segments)
        self.protected_terms.update(other.protected_terms)


@dataclass(frozen=True)
class TranslationRequest:
    segment_id: str
    text: str


@dataclass(frozen=True)
class PipelineConfig:
    domains: list[str]
    target_language: str
    lang_id: str
    source_language: str = DEFAULT_SOURCE_LANGUAGE
    components: tuple[TranslationComponent, ...] = DEFAULT_COMPONENTS
    data_domains_root: Path = DEFAULT_DATA_DOMAINS_ROOT
    src_domains_root: Path = DEFAULT_SRC_DOMAINS_ROOT
    model: str = DEFAULT_MODEL
    api_key_env: str = DEFAULT_API_KEY_ENV
    api_base: str | None = DEFAULT_API_BASE
    api_version: str | None = None
    max_rpm: float | None = DEFAULT_MAX_RPM
    batch_size: int = DEFAULT_BATCH_SIZE
    dry_run: bool = False
    max_preview: int = DEFAULT_MAX_PREVIEW
    timeout_s: int = DEFAULT_TIMEOUT_S
    retries: int = DEFAULT_RETRIES


def normalize_components(raw: Sequence[str]) -> tuple[TranslationComponent, ...]:
    """Expand component aliases and return canonical component tuple.

    Args:
        raw: Sequence of component names, may include aliases 'all' or 'context'.

    Returns:
        Tuple of resolved TranslationComponent values in canonical order.
    """
    selected: set[str] = set()
    for c in raw:
        if c == "all":
            selected.update(BASE_COMPONENTS)
        elif c == "context":
            selected.update({"policy", "db", "tasks"})
        else:
            selected.add(c)
    return tuple(c for c in ("tools", "policy", "db", "tasks") if c in selected)  # type: ignore[return-value]
