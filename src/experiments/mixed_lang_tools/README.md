# Mixed-Language Tools Experiment

This module implements tool description partitioning across multiple languages to test agent robustness when tool documentation is heterogeneous (some tools described in English, others in Thai, Vietnamese, etc.).

## Concept

In a mixed-language tools experiment:

- Tool docstrings are assigned to different languages by a seeded strategy
- Each tool gets exactly one language (non-overlapping)
- Related tools can be grouped to the same language
- The user still converses in their L2 (target language)

For research comparisons, prefer `partition_strategy: "nested_progressive"`.
That strategy orders tools once per seed and then moves additional English tools
into newly introduced non-English languages as the language set grows. This makes
bi/tri/fourth/multi conditions a monotonic complexity ladder: prior non-English
assignments stay fixed, English coverage decreases, and the added condition
isolates the incremental language complexity. The legacy `weighted_random`
strategy remains available for exploratory stress tests.

The default SEA-Tau configs set `group_mode: false` with
`tools_per_added_language: 3` so every added language receives exactly three
individual tools across domains. If `group_mode: true`, the unit becomes a whole
tool group, so exact per-language tool counts are not guaranteed.

## Quick Start

### 1. Run with existing config

```bash
# 3-language uniform mix (en/th/vi)
tau2 run --domain airline --lang-id th \
  --lang-components user_system agent_system greeting mixed_tools \
  --mixed-tools-config 3lang_uniform_en-th-vi

# 2-language mix
tau2 run --domain airline --lang-id th \
  --lang-components user_system agent_system greeting mixed_tools \
  --mixed-tools-config 2lang_uniform_en-th
```

### 2. Create a new config

```python
from experiments.mixed_lang_tools import (
    create_mixed_tools_config,
    save_mixed_tools_config,
)

config = create_mixed_tools_config(
    name="4lang_weighted_en-th-vi-id",
    description="4-way split: 40% English, 20% each for Thai/Vietnamese/Indonesian",
    languages=["en", "th", "vi", "id"],
    weights=[0.4, 0.2, 0.2, 0.2],
    domain="airline",  # Used to auto-populate translation provenance
    seed=42,
    group_mode=True,
    notes="Testing weighted distribution",
)
output_path = save_mixed_tools_config(config)
print(f"Saved to: {output_path}")
```

## Config Files

Configs are stored in `config/sea-tau/mixed_tools/`:

```
config/sea-tau/mixed_tools/
├── 2lang_uniform_en-th.json
├── 3lang_uniform_en-th-vi.json
└── 5lang_uniform_en-th-vi-id-zh.json
```

### Config Schema

```json
{
  "schema_version": "1.0",
  "name": "3lang_uniform_en-th-vi",
  "description": "Uniform 3-way split...",

  "languages": {
    "codes": ["en", "th", "vi"],
    "weights": [0.34, 0.33, 0.33],
    "weight_description": "uniform"
  },

  "partitioning": {
    "seed": 42,
    "group_mode": false,
    "group_source": "data/tau2/domains/{domain}/tool_groups.json",
    "partition_strategy": "nested_progressive",
    "tools_per_added_language": 3
  },

  "translation_provenance": {
    "en": { "source": "original", "model": null, "translated_at": null },
    "th": {
      "source": "data/tau2/domains/{domain}/th/tools.json",
      "model": "...",
      "translated_at": "..."
    }
  },

  "reproducibility": {
    "created_at": "2026-04-20T00:00:00Z",
    "notes": "SEA-Tau Experiment 1"
  }
}
```

## Tool Groups

When `group_mode: true`, related tools are assigned to the same language. Define groups in `data/tau2/domains/{domain}/tool_groups.json`:

```json
{
  "reservation_management": ["book_reservation", "cancel_reservation", ...],
  "flight_search": ["search_direct_flight", "search_onestop_flight", ...],
  "user_management": ["get_user_details", "send_certificate"],
  "utility": ["calculate", "transfer_to_human_agents"]
}
```

This ensures semantic coherence—all flight search tools will be in the same language.

## Prerequisites

Before running mixed-language experiments, ensure translations exist:

```bash
# Translate tools for required languages
uv run python -m translation.cli --domains airline --lang-id th --components tools
uv run python -m translation.cli --domains airline --lang-id vi --components tools
```

Translations are saved to:

- `data/tau2/domains/airline/th/tools.json`
- `data/tau2/domains/airline/vi/tools.json`

## API Reference

### Loading configs

```python
from experiments.mixed_lang_tools import load_mixed_tools_config

config = load_mixed_tools_config("3lang_uniform_en-th-vi")
print(config.languages.codes)  # ["en", "th", "vi"]
print(config.partitioning.seed)  # 42
```

### Manual partitioning

```python
from experiments.mixed_lang_tools import partition_tools_by_language, load_tool_groups

tool_names = ["book_reservation", "search_direct_flight", "calculate", ...]
tool_groups = load_tool_groups("airline")

assignments, group_assignments = partition_tools_by_language(
    tool_names=tool_names,
    languages=["en", "th", "vi"],
    weights=[0.34, 0.33, 0.33],
    seed=42,
    tool_groups=tool_groups,
)

for tool, assign in assignments.items():
    print(f"{tool}: {assign.lang} (group: {assign.group})")
```

### Loading mixed docstrings

```python
from pathlib import Path
from experiments.mixed_lang_tools import load_mixed_tools_config, load_mixed_docstrings

config = load_mixed_tools_config("3lang_uniform_en-th-vi")
docstrings, partition = load_mixed_docstrings(
    domain="airline",
    tool_names=["book_reservation", "search_direct_flight", ...],
    config=config,
    src_tools_path=Path("src/tau2/domains/airline/tools.py"),
)

# docstrings: {tool_name: docstring_in_assigned_language}
# partition: MixedToolsPartition with full assignment details
```

## Output

After a run, the realized partition is attached to the environment object:

```python
# Inside evaluation code
partition = environment._mixed_tools_partition
print(partition.summary.by_language)  # {"en": 4, "th": 5, "vi": 5}
```

## Diagnostics

Use the diagnostics script to inspect the exact realized tool-language
assignment before interpreting scores as language-count effects:

```bash
uv run python scripts/diagnose_mixed_tools.py \
  --domain telecom \
  --results-dir data/simulations \
  --json-out data/simulations/mixed_tools_diagnostics.json
```

The report includes:

- language counts and per-tool assignments for each config
- translated docstring coverage and missing docstrings
- whether `tool_groups.json` was actually used
- adjacent config comparisons verifying the default configs are nested-progressive
- optional task-level reward deltas for mixed-tool result runs

Important: the default SEA-Tau configs use `nested_progressive`, so higher
language-count configs preserve lower-count non-English assignments and reduce
English tool coverage. This makes the setup reliable for research comparisons,
but it still cannot mathematically guarantee lower model scores on every sample;
use multiple seeds/trials and confidence intervals when reporting results.

## Module Structure

```
src/experiments/mixed_lang_tools/
├── __init__.py      # Public API exports
├── diagnostics.py   # Realized assignment and result diagnostics
├── models.py        # Dataclasses (MixedToolsConfig, ToolAssignment, etc.)
├── partition.py     # Core logic (partitioning, loading, saving)
└── README.md        # This file
```
