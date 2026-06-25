"""Data models for mixed-language tools experiment (SEA-Tau Experiment 1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MixedToolsLanguageConfig:
    """Language distribution for tool-mix experiment."""

    codes: list[str]  # e.g., ["en", "th", "vi"]
    weights: list[float]  # e.g., [0.34, 0.33, 0.33]
    weight_description: str  # e.g., "uniform" or "50pct_thai"


@dataclass
class MixedToolsPartitioningConfig:
    """Partitioning settings for tool-mix experiment."""

    seed: int = 42
    group_mode: bool = True  # If True, use tool_groups.json
    group_source: str = "data/tau2/domains/{domain}/tool_groups.json"
    partition_strategy: str = "weighted_random"
    tools_per_added_language: int | None = None


@dataclass
class TranslationProvenance:
    """Provenance info for a single language's translations."""

    source: str  # "original" or path like "data/tau2/domains/{domain}/th/tools.json"
    model: str | None  # e.g., "gemini/gemini-2.5-flash-preview-05-20"
    translated_at: str | None  # ISO timestamp
    pipeline_version: str | None = None


@dataclass
class MixedToolsReproducibility:
    """Metadata for reproducibility."""

    created_at: str
    created_by: str | None = None
    codebase_commit: str | None = None
    notes: str | None = None


@dataclass
class MixedToolsConfig:
    """Full configuration for mixed-language tools experiment.

    This config contains all information needed to reproduce the experiment.
    """

    schema_version: str
    name: str  # e.g., "3lang_uniform_en-th-vi"
    description: str
    languages: MixedToolsLanguageConfig
    partitioning: MixedToolsPartitioningConfig
    translation_provenance: dict[str, TranslationProvenance]
    reproducibility: MixedToolsReproducibility

    def validate(self) -> None:
        """Validate config consistency."""
        codes = self.languages.codes
        weights = self.languages.weights
        if not codes:
            raise ValueError("languages.codes must not be empty")
        if len(codes) != len(weights):
            raise ValueError(
                f"languages.codes length {len(codes)} != weights length {len(weights)}"
            )
        if any(weight < 0 for weight in weights):
            raise ValueError("weights must be non-negative")
        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError(f"weights must sum to 1.0, got {sum(weights)}")
        for code in codes:
            if code != "en" and code not in self.translation_provenance:
                raise ValueError(f"Missing translation_provenance for language: {code}")
        if self.partitioning.partition_strategy not in {
            "weighted_random",
            "nested_progressive",
        }:
            raise ValueError(
                f"Unknown partition_strategy: {self.partitioning.partition_strategy}"
            )
        if (
            self.partitioning.partition_strategy == "nested_progressive"
            and codes[0] != "en"
        ):
            raise ValueError("nested_progressive requires English as the base language")
        if (
            self.partitioning.tools_per_added_language is not None
            and self.partitioning.tools_per_added_language <= 0
        ):
            raise ValueError("tools_per_added_language must be positive")


@dataclass
class ToolAssignment:
    """Assignment of a single tool to a language."""

    lang: str
    group: str | None = None


@dataclass
class MixedToolsPartitionSummary:
    """Summary statistics for a partition."""

    total_tools: int
    by_language: dict[str, int]
    by_group: dict[str, int] | None = None


@dataclass
class MixedToolsPartition:
    """Realized partition from a config (saved per-run).

    This is the output after applying a MixedToolsConfig to a specific domain,
    containing the actual tool-to-language assignments.
    """

    config_name: str
    config_path: str
    domain: str
    realized_at: str
    tool_assignments: dict[str, ToolAssignment]
    summary: MixedToolsPartitionSummary
    group_assignments: dict[str, str] | None = None

    def to_docstring_lang_map(self) -> dict[str, str]:
        """Return simple {tool_name: lang_id} mapping."""
        return {tool: assign.lang for tool, assign in self.tool_assignments.items()}
