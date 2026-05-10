# SEA-TAU Plan

SEA-TAU evaluates whether conversational customer-service agents degrade from the
English-only tau2 baseline under multilingual Southeast/East Asian language
conditions. The implementation should stay as close to upstream tau2 as possible:
reuse original code paths, keep original benchmark data intact, and add only the
experiment layer needed for multilingual assets, runtime loading, result metadata,
and human localization review.

## Research Questions

Do conversational agent success rates degrade significantly from the English-only
tau2 baseline across the SEA-TAU experiment settings?

How does degradation vary by:

- target language: Indonesian, Thai, Vietnamese, Filipino, and Chinese
- agent model: `openrouter/openai/gpt-4.1-mini` and
  `openrouter/qwen/qwen3-235b-a22b-2507`
- user simulator model: `openrouter/qwen/qwen3-235b-a22b-2507`
- adaptation strategy: baseline, mixed tools, crosslingual, translated, localized

Supported SEA-TAU domains are:

- `airline`
- `retail`
- `telecom`

The `mock` domain is not translated and is not a supported SEA-TAU domain. It can
remain useful for core tau2 smoke tests, but SEA-TAU scripts should not fan out to
it.

## Experiment Matrix

| Experiment     | User conversation | Agent conversation | Tools                                           | Context (`db/tasks/policy`) | Asset root                                  |
| -------------- | ----------------- | ------------------ | ----------------------------------------------- | --------------------------- | ------------------------------------------- |
| `baseline`     | English           | English            | English                                         | English                     | original tau2 data                          |
| `mixed_tools`  | English           | English            | multilingual mix, e.g. 5 English + 5 Thai tools | English                     | original context + translated tool docs     |
| `crosslingual` | L2                | L2                 | English                                         | English                     | original tau2 data                          |
| `translated`   | L2                | L2                 | L2                                              | L2                          | `data/tau2/domains/{domain}/{lang_id}/`     |
| `localized`    | L2                | L2                 | L2                                              | L2                          | `data/tau2/domains/{domain}/{lang_id}_loc/` |

Important decisions:

- `mixed_tools` uses English conversation, English greeting, English policy, English
  DB, and English tasks. Only tool descriptions are multilingual.
- Translated artifacts live under `{lang_id}` and should work without localized
  artifacts.
- Localized artifacts live under `{lang_id}_loc`; this folder is optional and must
  not affect the translated `{lang_id}` folder.
- `{lang_id}_loc` does not require an entry in `config/languages.json`.
- A localized experiment should explicitly load `{lang_id}_loc`; if it is missing,
  the run should fail or skip clearly instead of silently falling back to machine
  translation.

## High-Level Goals

- Maintain a unified codebase that can run upstream tau2 evaluations and the extra
  SEA-TAU experiments.
- Reuse original tau2 code paths wherever possible; change shared code only when
  required for multilingual component loading, metadata, or validation.
- Keep original tau2 data intact for correct English-baseline comparison.
- Load language-aware components on demand through CLI options and SEA-TAU presets.
- Distinguish translated and localized experiments in asset loading, run metadata,
  and documentation.
- Save results under `data/simulations/` in a reviewable structure.
- Export translated components for human annotation and import reviewed localized
  artifacts back into the runtime format.
- Add localization utilities for realistic names, addresses, and prose while
  preserving canonical IDs, tool names, schemas, enum values, and evaluator
  compatibility.

## Result Output Requirements

Default run folders should use:

```text
YYYY-MM-DD-HH-MM-SS_{domain}_{language}_{agent-llm}_{user-llm}
```

`results.json` should include enough metadata to review and reproduce SEA-TAU
runs:

- experiment name
- target language
- effective run language
- asset mode: `original`, `translated`, or `localized`
- artifact root actually loaded
- `lang_components`
- `mixed_tools_config`, when applicable
- realized mixed-tools partition summary, when applicable
- model names and model args
- task set, task split, task IDs, and number of tasks
- relevant SEA-TAU config files or manifest hashes
- translation/localization manifest paths, when applicable

## Current Codebase Progress

Already present or in progress:

- `config/languages.json` defines language metadata used by `--lang-id`.
- `config/sea-tau/experiments.yaml` defines SEA-TAU presets and aliases.
- `config/sea-tau/mixed_tools/*.json` stores mixed tool-language partition configs.
- `scripts/run_seatau.sh` runs preset fanout and manages `--lang-components`.
- `tau2 run` accepts `--lang-id`, `--lang-components`, and
  `--mixed-tools-config`.
- Runtime language wiring supports user prompt, agent prompt, greeting, tools,
  mixed tools, policy, DB, schema localization, and translated task loading.
- `src/translation/` contains the selective translation pipeline.
- `src/utils/export_annotation_sheet.py` exports annotation workbooks, but the
  annotation/localization workflow still needs to be made current.
- Default run naming and SEA-TAU metadata fields have been started.
- SEA-TAU presets now declare supported domains and asset modes.
- `localized` runs resolve assets from `{lang_id}_loc` and fail clearly when
  required localized artifacts are missing.
- SEA-TAU wrapper dry-runs surface `asset_mode` and skip unsupported domains,
  including `mock`.
- Environment replay evaluation now applies the same language runtime wiring as
  the run, so localized tool payloads can be canonicalized before DB comparison.
- Language correctness is available as an explicit evaluator reward and is also
  recorded in `reward_info.info` for standard evaluations.

Known gaps:

- Finish annotation import from edited `.xlsx` or `.csv` files into `{lang_id}_loc`.
- Add or update docs so `config/sea-tau/README.md` is the experiment matrix source
  of truth and `src/translation/README.md` owns translation/localization workflow
  details.
- Revisit any direct edits to original tau2 data and move them to SEA-TAU overlays
  unless they are true baseline correctness fixes.

## Implementation Plan

[x] Reconcile SEA-TAU docs and config so `mixed_tools` is consistently defined as
English conversation with multilingual tool descriptions.

[x] Define supported SEA-TAU domains centrally as `airline`, `retail`, and
`telecom`; exclude `mock` from translation and preset fanout.

[x] Add runtime asset-mode handling: `original`, `translated`, and `localized`.
Translated mode loads `{lang_id}`; localized mode loads `{lang_id}_loc`.

[x] Make localized asset loading optional for the codebase but strict for the
`localized` experiment.

[/] Preserve original tau2 domain data; move or revert direct changes unless they
are required baseline fixes.

[ ] Expand `results.json` metadata with SEA-TAU experiment settings, asset mode,
artifact root, language components, mixed-tools config, and partition summary.

[x] Add language correctness evaluation as a new reward in
`src/tau2/evaluator/evaluator.py`: iterate over trajectories, run language ID on
all assistant turns with `fastText`, and record the proportion of turns in the
expected language in `reward_info.info`.

[ ] Finish annotation export/import: export English + `{lang_id}` review sheets

[ ] Being able to import reviewed final values into `{lang_id}_loc`.

[ ] Add localization utilities for realistic names, addresses, and localized prose
while preserving evaluator-compatible canonical fields.

[ ] Consolidate documentation across `README.md`, `config/README.md`,
`config/sea-tau/README.md`, `src/translation/README.md`, and annotation docs.

[ ] Add tests for preset resolution, no-`mock` SEA-TAU fanout, `{lang_id}` vs
`{lang_id}_loc` loading, metadata persistence, annotation round-trip, and original
data preservation.

[ ] Run focused tests during development and `make test` before committing.
