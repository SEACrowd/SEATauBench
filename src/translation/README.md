# Tau2 Domain Translation Toolkit

This folder contains a modular translation pipeline for Tau2 domains.  
It is designed for multilingual benchmark creation where language changes but evaluation logic stays stable.

## Goals

- Translate multiple domains (not only `mock`) with one CLI.
- Route model calls through LiteLLM so you can use different providers or a LiteLLM proxy.
- Translate only user-facing text.
- Preserve canonical benchmark tokens (tool names, IDs, statuses, enum values, reward basis, etc.).
- Write translated files to a separate output tree so English source data/code remains untouched.

## Core Ideas (Selective Translation Strategy)

1. Translate only needed text:
- `tasks.json` user-facing instructions and natural-language assertions.
- `policy*.md`.
- `db.json` / `user_db.json` natural text fields such as titles/descriptions/names.
- Python docstrings and `Field(description="...")` in domain files (`data_model.py`, `tools.py`, optional user-side variants).

2. Never translate canonical structures:
- Tool/function names (`create_task`, `update_task_status`, etc.).
- IDs (`task_1`, `user_1`, `call_1`, `action_id`, ...).
- Status enums and reward enums (`pending`, `completed`, `DB`, `ACTION`, ...).
- Schema/control keys (`env_type`, `func_name`, `role`, etc.).

3. Placeholder-protection before model calls:
- Protected tokens are masked as placeholders like `__PH_0__`.
- The selected LLM translates masked text.
- Placeholders are restored and validated (fails if dropped/altered).

4. Keep benchmark semantics stable:
- Action graphs, evaluation criteria structure, and tool call contracts remain unchanged.
- Translation changes linguistic surface only.

## Module Layout

- `translation/config.py`: rules, patterns, defaults.
- `translation/models.py`: dataclasses for files/segments/config.
- `translation/path_match.py`: wildcard path matching.
- `translation/protect.py`: placeholder masking/unmasking.
- `translation/litellm_translator.py`: LiteLLM-based translator client.
- `translation/extractors.py`: file discovery, extraction rules, and file patching logic.
- `translation/pipeline.py`: orchestration (extract -> translate -> write).
- `translation/cli.py`: command line entrypoint.

## Usage

### 1. Set API key (example: Gemini)

```bash
export GEMINI_API_KEY="<your_key>"
```

For proxy use, you can also set:

```bash
export LITELLM_API_BASE="http://localhost:4000"
```

`.env` is loaded automatically when `python-dotenv` is installed.

### 2. Dry run (no API call)

```bash
python -m translation.cli \
  --domains mock telecom \
  --target-language Thai \
  --dry-run
```

### 3. Run translation

```bash
python -m translation.cli \
  --domains mock \
  --source-language English \
  --target-language Thai \
  --model gemini/gemini-3-flash-preview \
  --max-rpm 5
```

### 4. Run via LiteLLM proxy (provider-agnostic)

```bash
python -m translation.cli \
  --domains mock retail \
  --target-language Thai \
  --model openai/gpt-4o-mini \
  --api-key-env OPENAI_API_KEY \
  --api-base http://localhost:4000
```

### 5. Azure OpenAI example

Put these in `.env`:

```bash
AZURE_API_KEY=...
AZURE_API_BASE=https://<resource>.openai.azure.com
AZURE_API_VERSION=2024-12-01-preview
```

Then run:

```bash
python -m translation.cli \
  --domains mock \
  --target-language Thai \
  --model azure/<deployment_name> \
  --batch-size 4
```

Note: for Azure, the part after `azure/` must be your deployment name, not necessarily the raw model name.

Output is written to:

`translation/output/<target-language-lowercase>/...`

Example:

`translation/output/thai/data/tau2/domains/mock/tasks.json`

## Notes

- The pipeline is intentionally conservative.  
  If a field is ambiguous between natural text and canonical control data, it is skipped.
- You can extend rules in `translation/config.py` for new domain-specific schemas.
- Since this uses LiteLLM, model naming and required env vars depend on your provider/proxy configuration.
- Progress bars are shown during translation and file writing.
- Requests are rate-limited by `--max-rpm` (default `5.0`) to stay under Gemini free-tier RPM.

## Troubleshooting

- Error: `DefaultCredentialsError ... default credentials were not found`  
This means LiteLLM routed to Vertex AI. Use Gemini AI Studio routing instead:
  - `--model gemini/gemini-3-flash-preview`
  - `--api-key-env GEMINI_API_KEY`
  - set `GEMINI_API_KEY` in your shell

- Error: `Quota exceeded ... Please retry in Xs`  
Use lower throughput:
  - keep `--max-rpm 5` for Gemini free tier
  - reduce `--batch-size` (for stability) e.g. `--batch-size 8`
