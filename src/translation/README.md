# Tau2 Domain Translation Toolkit

This folder contains a modular translation pipeline for Tau2 domains.
It is designed for multilingual benchmark creation where language changes but evaluation logic stays stable.

## Architecture: Translation vs Injection

The pipeline is **decoupled into two independent phases**:

```
Phase 1: TRANSLATE (offline, one-time per language)
  tools.py  ──extract──▶  segments  ──LLM──▶  tools.json
  tasks*.json ────────────────────────────────▶  tasks*.json (translated)
  policy*.md / main_policy*.md / tech_support*.md ─▶ translated copies
  db.json / db.toml / user_db.* ─────────────▶ translated copies

Phase 2: INJECT (at eval time, zero LLM calls)
  tau2 run --domain retail --lang-id th
  → auto-loads translated assets from data/tau2/domains/{domain}/{lang_id}/
  → patches tool docstrings, policy, DB, tasks, and user instructions
```

- **Phase 1** calls the LLM, costs money, and writes JSON files to disk.
- **Phase 2** reads the files at eval time. No LLM needed — just pass `--lang-id`.

This means you translate once, then run evaluations for that language as many times as you want.

Runtime language behavior is also configurable:

- `--lang-id` selects the target language
- `--lang-components` decides whether to apply that language to
  the agent, the greeting, and/or translated assets. By default, the system prompt is added to simulated user to converse in a language

## Output Locations

All translated assets are unified under `data/tau2/domains/{domain}/{lang_id}/`:

| File type                 | Output path                                                      |
| ------------------------- | ---------------------------------------------------------------- | ----- |
| Tool docstrings (`.json`) | `data/tau2/domains/{domain}/{lang_id}/tools.json`                |
| Task files                | `data/tau2/domains/{domain}/{lang_id}/tasks*.json`               |
| Policies (`.md`)          | `data/tau2/domains/{domain}/{lang_id}/*.md`                      |
| DB data                   | `data/tau2/domains/{domain}/{lang_id}/db.json                    | toml` |
| Translation manifest      | `data/tau2/domains/{domain}/{lang_id}/translation_manifest.json` |

## Quick Start

### Step 1: Translate domain assets

Set an API key and run the pipeline:

```bash
# Option A: Gemini API (direct)
export GEMINI_API_KEY="your-key"
uv run python -m translation.cli \
  --domains retail \
  --domains airline \
  --lang-id th \
  --components all \
  --model gemini/gemini-3.1-flash-lite-preview

# Option B: OpenRouter
export OPENROUTER_API_KEY="your-key"
uv run python -m translation.cli \
  --domains retail \
  --domains airline \
  --lang-id vi \
  --components context \
  --model openrouter/google/gemini-3.1-flash-lite-preview \
  --api-key-env OPENROUTER_API_KEY \
  --api-base https://openrouter.ai/api/v1

# Option C: Dry run (preview segments, no API call)
uv run python -m translation.cli \
  --domains retail \
  --lang-id th \
  --components tools \
  --dry-run
```

This writes all assets to `data/tau2/domains/retail/th/`.

Useful rerun modes:

- `--components tools` translates tool descriptions only.
- `--components context` translates policy + DB + tasks, but not tools.
- `--components all` translates both.

The pipeline writes `translation_manifest.json` with source fingerprints. If you later edit tools, policies, DB files, or tasks, `tau2 run --lang-id ...` will warn that the translation is stale and suggest retranslation.

### Step 2: Run multilingual evaluation

```bash
# Thai evaluation — automatically loads all Thai assets
tau2 run --domain retail --lang-id th --agent-llm gpt-4.1 --user-llm gpt-4.1 \
  --num-trials 1 --num-tasks 5

# Cross-lingual evaluation — user + agent speak Thai, assets remain English
tau2 run --domain retail --lang-id th --lang-components user_system agent_system greeting \
  --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 1 --num-tasks 5

# English baseline (no regression)
tau2 run --domain retail --agent-llm gpt-4.1 --user-llm gpt-4.1 \
  --num-trials 1 --num-tasks 5

# SITAW preset helper: experiment -> lang-components, all other args pass to tau2 run
scripts/run_sitaw_experiments.sh --experiment trans_tool \
  --domain retail --lang-id th --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5
```

For SITAW-style batches, use:

```bash
# Run all four multilingual presets with shared tau2 args
scripts/run_sitaw_experiments.sh --all-experiments \
  --domain retail --lang-id th --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5
```

By default, `--lang-id` enables all language-aware runtime components for
backward compatibility. Use `--lang-components` to choose a subset from:
`user_system`, `agent_system`, `greeting`, `tools`, `policy`, `db`, `tasks`.
Runtime also supports aliases: `context` = `policy`+`db`+`tasks`, and
`all` = all components. `user_system` is always enabled whenever `--lang-id`
is set.

**Important:** Even when `--lang-components` is explicitly set, `user_system`
is still injected as long as `--lang-id` is provided.

SITAW preset mapping in `scripts/run_sitaw_experiments.sh`:

- `trans_tool` → `user_system agent_system greeting tools`
- `crosslingual` → `user_system agent_system greeting`
- `translated` / `localized` → `user_system agent_system greeting tools policy db tasks`
- `baseline` → no `--lang-components` preset

When the corresponding component is enabled, `tau2 run` can:

1. Patch tool docstrings with translated versions
2. Swap the policy and/or append an agent language instruction
3. Swap the DB and user DB if translated versions exist
4. Load translated `tasks.json` if present
5. Prepend a language instruction to user simulator instructions

### Step 3: Run end-to-end test

```bash
# Dry run (no API key needed)
uv run python scripts/test_translation_e2e.py --dry-run

# With real translation
GEMINI_API_KEY=... uv run python scripts/test_translation_e2e.py \
  --model gemini/gemini-3.1-flash-lite-preview \
  --lang-id th \
  --limit 3

# With OpenRouter
OPENROUTER_API_KEY=... uv run python scripts/test_translation_e2e.py \
  --model openrouter/google/gemini-3.1-flash-lite-preview \
  --api-key-env OPENROUTER_API_KEY \
  --lang-id vi
```

## How It Works (Detail)

### Extraction (`extractors.py`)

Uses Python AST to find all docstrings in `tools.py`:

```python
from translation.extractors import _extract_python
from translation.models import DomainFile

df = DomainFile(domain="retail", path=tools_path, relative_path=tools_path, kind="python")
result = _extract_python(df)

# Each segment has:
#   segment.name    = "cancel_pending_order"  (function name, or None for module docstring)
#   segment.text    = "Cancel a pending order..."
#   segment.address = SourceSpan(start=..., end=...)  (char offsets)
```

### Translation (`litellm_translator.py`)

Sends batches to any LLM provider via LiteLLM. The prompt instructs the model to return JSON with translations. Protected terms (tool names, IDs, enums) are masked as `__PH_N__` placeholders before translation and restored after.

### Storage

For Python files (tools, data models), the pipeline writes a flat JSON:

```json
{
  "RetailTools": "ชุดเครื่องมือทั้งหมดสำหรับโดเมนค้าปลีก",
  "cancel_pending_order": "ยกเลิกคำสั่งซื้อที่รอดำเนินการ ...",
  "get_order_details": "รับสถานะและรายละเอียดของคำสั่งซื้อ ...",
  ...
}
```

Stored at `data/tau2/domains/{domain}/{lang_id}/tools.json`.

### Injection at Eval Time

When `tau2 run --lang-id th` is used, `apply_language_config()` in `src/tau2/runner/build.py` handles all patching automatically. No manual code needed.

For programmatic use (e.g. custom eval scripts):

```python
from translation.loader import (
    load_docstrings_json,
    patch_toolkit_docstrings,
    restore_toolkit_docstrings,
)
from tau2.domains.retail.tools import RetailTools

docs = load_docstrings_json(Path("data/tau2/domains/retail/th/tools.json"))
originals = patch_toolkit_docstrings(RetailTools, docs)
# ... run evaluation ...
restore_toolkit_docstrings(RetailTools, originals)
```

### Inspecting source docstrings (no translation needed)

```python
from translation.loader import extract_function_docstrings
from pathlib import Path

docs = extract_function_docstrings(Path("src/tau2/domains/retail/tools.py"))
```

## Selective Translation Strategy

### What gets translated

- `tasks.json` — user-facing instructions, natural-language assertions
- `tasks_full.json`, `tasks_small.json`, etc. when present
- `policy*.md`, `main_policy*.md`, `tech_support*.md`
- `db.json`, `db.toml`, `user_db.json`, `user_db.toml`
- Python docstrings and `Field(description="...")` in `tools.py`, `data_model.py`

### What is never translated

- Tool/function names (`create_task`, `update_task_status`)
- IDs (`task_1`, `user_1`, `#W0000000`)
- Status enums and reward enums (`pending`, `completed`, `DB`, `ACTION`)
- Schema/control keys (`env_type`, `func_name`, `role`)

Protected tokens are masked as `__PH_N__` placeholders before translation and validated after.

## Module Layout

| File                    | Purpose                                              |
| ----------------------- | ---------------------------------------------------- |
| `config.py`             | Rules, patterns, defaults                            |
| `models.py`             | Dataclasses for files, segments, config              |
| `path_match.py`         | Wildcard path matching                               |
| `protect.py`            | Placeholder masking/unmasking                        |
| `litellm_translator.py` | LiteLLM-based translator client                      |
| `extractors.py`         | File discovery, AST extraction, JSON/Python patching |
| `pipeline.py`           | Orchestration (extract → translate → write)          |
| `loader.py`             | Load translated JSON + inject into tool classes      |
| `cli.py`                | Command-line entrypoint                              |

## CLI Reference

```
uv run python -m translation.cli \
  --domains DOMAIN                  # repeat for multiple domains
                                   # e.g., --domains retail --domains airline
  --lang-id CODE                     # e.g., th, vi, id, zh, tl
  [--components tools|policy|db|tasks|context|all ...]
  --model MODEL                      # LiteLLM model ID (default: gemini/gemini-3.1-flash-lite-preview)
  [--source-language LANG]           # default: English
  [--api-key-env VAR]                # auto-detected from model prefix
  [--api-base URL]                   # for proxies / OpenRouter
  [--api-version VER]                # for Azure
  [--max-rpm N]                      # default: 5.0 (Gemini free tier safe)
  [--batch-size N]                   # segments per API call (default: 24)
  [--dry-run]                        # preview only, no API call
  [--data-domains-root PATH]         # default: data/tau2/domains
  [--src-domains-root PATH]          # default: src/tau2/domains
```

Notes:

- `context` expands to `policy + db + tasks`.
- `banking_knowledge` and voice-only task files are intentionally excluded from this pipeline.

## Available Languages

Defined in `data/languages.json`:

| Code | Language             |
| ---- | -------------------- |
| `th` | Thai                 |
| `vi` | Vietnamese           |
| `id` | Indonesian           |
| `zh` | Chinese (Simplified) |
| `tl` | Filipino             |

## Model Options

| Provider        | `--model`                                         | `--api-key-env`      | Notes                                         |
| --------------- | ------------------------------------------------- | -------------------- | --------------------------------------------- |
| Gemini (direct) | `gemini/gemini-3.1-flash-lite-preview`            | `GEMINI_API_KEY`     | Free tier: 5 RPM                              |
| OpenRouter      | `openrouter/google/gemini-3.1-flash-lite-preview` | `OPENROUTER_API_KEY` | Add `--api-base https://openrouter.ai/api/v1` |
| Azure OpenAI    | `azure/<deployment>`                              | `AZURE_API_KEY`      | Set `AZURE_API_BASE`, `AZURE_API_VERSION`     |
| OpenAI          | `openai/gpt-4o-mini`                              | `OPENAI_API_KEY`     |                                               |
| LiteLLM proxy   | `openai/<any>`                                    | depends              | `--api-base http://localhost:4000`            |

## Troubleshooting

- **`DefaultCredentialsError ... default credentials were not found`**
  LiteLLM routed to Vertex AI. Use Gemini AI Studio routing:
  `--model gemini/gemini-3.1-flash-lite-preview --api-key-env GEMINI_API_KEY`

- **`Quota exceeded ... Please retry in Xs`**
  Lower throughput: `--max-rpm 5 --batch-size 8`

- **`audioop` import error on Python 3.13**
  This is a pre-existing issue in `tau2/__init__.py` (imports `tau2.voice`). Use Python 3.12 or earlier.
