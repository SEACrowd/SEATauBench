# Tau2 Translation Toolkit

This module translates Tau2 domain artifacts into multilingual assets that runtime
can load via `--lang-id`. The focus here is translation and artifact generation.

## What this pipeline does

Given a domain (for example `retail`) and language id (for example `th`), it can
translate:

- Tool docstrings from `tools.py` / `user_tools.py`
- Context artifacts (`*.md`, `tasks*.json`, `db.json`, `db.toml`, `user_db.*`)
- Schema review artifacts from `data_model.py` / `user_data_model.py`

It writes outputs under:

`data/tau2/domains/{domain}/{lang_id}/`

Key outputs include:

- `tools.json`
- `tasks*.json`
- translated policy markdown files
- translated DB files
- `data_model.json` / `user_data_model.json` (schema review artifacts)
- `translation_manifest.json` (source fingerprints + metadata)

## Language registry

Language metadata is loaded from:

`config/languages.json`

Add a new entry there before using a new `--lang-id`.

## Quick start

### 1) Translate tools only

```bash
uv run python -m translation.cli \
  --domains retail \
  --lang-id th \
  --components tools
```

### 2) Translate context only (policy + db + tasks)

```bash
uv run python -m translation.cli \
  --domains retail \
  --lang-id th \
  --components context
```

### 3) Translate everything

```bash
uv run python -m translation.cli \
  --domains retail \
  --domains airline \
  --lang-id vi \
  --components all
```

### 4) Dry run (no LLM call)

```bash
uv run python -m translation.cli \
  --domains retail \
  --lang-id id \
  --components tools \
  --dry-run
```

## CLI reference

```bash
uv run python -m translation.cli \
  --domains DOMAIN                  # repeat for multiple domains
  --lang-id CODE                    # from config/languages.json
  [--components tools|policy|db|tasks|schema|context|all ...]
  [--source-language LANG]          # default: English
  [--model MODEL]                   # must be vertex_ai/gemini-3.1-flash-lite-preview
  [--max-concurrency N]
  [--batch-size N]
  [--timeout N]
  [--retries N]
  [--dry-run]
  [--max-preview N]
  [--data-domains-root PATH]        # default: data/tau2/domains
  [--src-domains-root PATH]         # default: src/tau2/domains
```

Notes:

- `context` expands to `policy + db + tasks`.
- `all` expands to all supported components.
- Default translation uses Vertex AI via gcloud/ADC with
  `vertex_ai/gemini-3.1-flash-lite-preview`. Set `VERTEXAI_PROJECT` and
  `VERTEXAI_LOCATION` before running.
- Excluded domains are defined by `SKIPPED_TRANSLATION_DOMAINS` in
  `src/translation/config.py`.

## Selective translation rules

### Translated

- Natural-language content in policy/tasks/DB text leaves
- Tool and schema docstrings/descriptions
- Schema display/localized labels in review artifacts

### Not translated

- Tool/function identifiers
- IDs/reference codes
- Runtime enum values used as canonical system inputs
- Structural keys in JSON/TOML/Python schema structures

Protected tokens are masked before LLM translation and restored after.

## Staleness tracking

Each translation run writes `translation_manifest.json` with source fingerprints.
At runtime, language loading warns when source artifacts changed since translation.

## Troubleshooting

- `DefaultCredentialsError ... default credentials were not found`
  - Authenticate with gcloud/ADC and set `VERTEXAI_PROJECT` and
    `VERTEXAI_LOCATION` for the Vertex route.
- `Quota exceeded`
  - Lower throughput, e.g. `--max-concurrency 2 --batch-size 8`.
