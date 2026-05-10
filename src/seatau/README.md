# SEA-TAU

The multilingual experiment layer for τ-bench. Adds five experiment presets
(`baseline`, `mixed_tools`, `crosslingual`, `translated`, `localized`) on top
of upstream tau2 by translating domain artefacts into Southeast/East Asian
languages and wiring them into the tau2 runtime.

## Package layout

```
src/seatau/
  __init__.py
  paths.py                  # canonical filesystem paths (PROJECT_ROOT, DATA_DIR, etc.)
  languages.json            # language registry consumed by --lang-id
  experiments.yaml          # SEA-TAU preset matrix and aliases
  openrouter_cost.py        # OpenRouter balance/cost helpers
  README.md                 # this file
  translation/              # machine translation pipeline + runtime localizer
  annotation/               # human-review pipeline (workbook ↔ {lang}_loc/)
  mixed_lang_tools/         # SEA-TAU EXP #1 partition configs and code
  localization/             # synthetic-data and localization helpers (notebooks)
```

External directories owned by SEA-TAU:

```
data/tau2/domains/{domain}/{lang}/       # machine-translated artefacts
data/tau2/domains/{domain}/{lang}_loc/   # human-localized artefacts (annotation output)
data/seatau/annotation/                  # reviewer workbooks + manifests
config/sea-tau/                          # legacy preset config (kept for back-compat shims)
scripts/run_seatau.sh                    # canonical experiment fanout entry point
```

## Experiment matrix (source of truth: `experiments.yaml`)

| Preset         | User convo | Agent convo | Tools                         | Context (db/tasks/policy) | Asset root                                 |
| -------------- | ---------- | ----------- | ----------------------------- | ------------------------- | ------------------------------------------ |
| `baseline`     | English    | English     | English                       | English                   | original tau2 data                         |
| `mixed_tools`  | English    | English     | Mixed (English + selected L2) | English                   | original tau2 data + translated tool docs  |
| `crosslingual` | L2         | L2          | English                       | English                   | original tau2 data                         |
| `translated`   | L2         | L2          | L2                            | L2                        | `data/tau2/domains/{domain}/{lang}/`       |
| `localized`    | L2         | L2          | L2                            | L2                        | `data/tau2/domains/{domain}/{lang}_loc/`   |

Supported domains: `airline`, `retail`, `telecom`. Supported languages:
`en`, `id`, `th`, `vi`, `zh`, `tl` (see `languages.json`).

## Common commands

### Run experiments

```bash
# Single preset on one domain × one language
scripts/run_seatau.sh --experiment translated \
  --domain retail --lang-id vi --num-tasks 5 \
  --agent-llm gpt-4.1 --user-llm gpt-4.1

# Fan out one preset across every non-English language
scripts/run_seatau.sh --experiment crosslingual \
  --domain retail --num-tasks 5 \
  --agent-llm gpt-4.1 --user-llm gpt-4.1

# Run every preset (full matrix)
scripts/run_seatau.sh --all-experiments \
  --domain retail --lang-id vi --num-tasks 5 \
  --agent-llm gpt-4.1 --user-llm gpt-4.1

# Dry-run: print the tau2 invocations without executing
scripts/run_seatau.sh --all-experiments --dry-run \
  --domain retail --lang-id vi --num-tasks 5 \
  --agent-llm gpt-4.1 --user-llm gpt-4.1
```

The wrapper does not accept `--lang-components` directly — it sets that per
preset based on `experiments.yaml`.

### Translate domain artefacts (machine translation)

```bash
# Translate everything for one (domain, lang)
uv run python -m seatau.translation.cli \
  --domains retail --lang-id vi --components all \
  --model openrouter/google/gemini-3.1-flash-lite-preview \
  --api-key-env OPENROUTER_API_KEY

# Just tools
uv run python -m seatau.translation.cli \
  --domains retail --lang-id th --components tools

# Dry run
uv run python -m seatau.translation.cli \
  --domains retail --lang-id id --components tools --dry-run
```

See [`translation/README.md`](translation/README.md) for full pipeline details.

### Human review (annotation round-trip)

```bash
# 1. Export reviewer workbook
uv run python -m seatau.annotation export \
  --domains retail telecom --lang-id vi \
  -o data/seatau/annotation/annotation_vi.xlsx --reviewer alice --round-id r1

# 2. Reviewer fills the name.vi.final column in the .xlsx

# 3. Import the reviewed workbook into {lang}_loc/ (production: rejects empty .final)
uv run python -m seatau.annotation import \
  --workbook data/seatau/annotation/annotation_vi.xlsx --lang vi

# Round-trip smoke test: accept machine translation when .final is empty
uv run python -m seatau.annotation import \
  --workbook data/seatau/annotation/annotation_vi.xlsx --lang vi \
  --allow-machine-fallback

# Optional: export + synthetic localization in one shot
uv run python -m seatau.localization export \
  --domains retail telecom --lang-id vi \
  -o data/seatau/annotation/annotation_vi.localized.xlsx \
  --reviewer alice --round-id r1
```

See [`annotation/README.md`](annotation/README.md) for the full workflow.

### Mixed-language tools (EXP #1)

```bash
# Run with a 5-language uniform tool partition
tau2 run --domain airline --lang-id en \
  --lang-components mixed_tools \
  --mixed-tools-config 5lang_uniform_en-th-vi-id-zh
```

See [`mixed_lang_tools/README.md`](mixed_lang_tools/README.md).

## How `--lang-id` flows through the runtime

1. `scripts/run_seatau.sh` resolves the preset → sets `--lang-id`,
   `--lang-components`, optional `--mixed-tools-config`, plus
   `--seatau-experiment` / `--seatau-target-lang` / `--seatau-asset-mode`.
2. `tau2 run` validates `--lang-id` against `src/seatau/languages.json`.
3. `tau2.runner.batch.run_domain` loads tasks; if `tasks` ∈ components,
   loads from `{language_asset_id}/tasks.json`.
4. `tau2.runner.build.build_text_orchestrator` constructs the env and
   calls `tau2.runner.language.apply_language_config(env, config)`, which
   patches tool docstrings and DB output canonicalization (via
   `seatau.translation.runtime_localization`), swaps translated
   `policy.md` / `*.md`, hot-swaps `db.json` / `db.toml`, and returns
   the localized greeting.
5. The evaluator replay path re-applies the same wiring on gold/predicted
   environments via `_build_language_environment_configurer` so DB
   hashes are comparable.

`config.language_asset_id` resolves to `lang_id` for `translated` /
original modes, and to `{lang_id}_loc` for `localized` mode (see
`tau2/data_model/simulation.py`).

## Audit / status

- Translation manifest fingerprints (16 manifests across 3 domains × 5
  langs + mock/vi): all fresh as of 2026-05-10.
- `.stale` filename gating has been removed; staleness is now expressed
  via `translation_manifest.json` SHAs only.
- See `experiments/REPORT.md` for the full audit and redesign plan.

## Operational docs

- [`translation/README.md`](translation/README.md) — machine-translation pipeline
- [`annotation/README.md`](annotation/README.md) — human-review round-trip
- [`mixed_lang_tools/README.md`](mixed_lang_tools/README.md) — EXP #1 partitioning
- [`localization/README.md`](localization/README.md) — synthetic-data helpers
- [`../../experiments/PLAN.md`](../../experiments/PLAN.md) — roadmap and known gaps
- [`../../experiments/REPORT.md`](../../experiments/REPORT.md) — audit + redesign
- [`../../scripts/run_seatau.sh`](../../scripts/run_seatau.sh) — preset fanout wrapper
