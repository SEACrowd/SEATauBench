from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


FileKind = Literal["json", "markdown", "python"]


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
    source_language: str
    target_language: str
    data_domains_root: Path
    src_domains_root: Path
    output_root: Path
    model: str
    api_key_env: str
    api_base: str | None
    api_version: str | None
    max_rpm: float | None
    batch_size: int
    dry_run: bool
    max_preview: int
