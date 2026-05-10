# SEA-TAU Translated/Localized Runtime — Audit & Redesign

Scope: how `tau2 run` actually serves translated artefacts to the agent and user
across the SEA-TAU experiment matrix, with focus on EXP #3 `translated`. Maps
the current code paths, surfaces correctness gaps, and proposes a tighter
design that keeps changes inside `experiments/` + a thin tau2 hook.

References:
- Wrapper: `scripts/run_seatau.sh`
- Preset config: `config/sea-tau/experiments.yaml`
- Plan: `experiments/PLAN.md`
- Runtime wiring: `src/tau2/runner/language.py`, `src/tau2/runner/build.py`,
  `src/tau2/runner/batch.py`
- Schema/value localization: `src/translation/runtime_localization.py`
- Run config / metadata: `src/tau2/data_model/simulation.py`,
  `src/tau2/runner/helpers.py`
- Replay-time wiring: `src/tau2/evaluator/evaluator.py`,
  `src/tau2/evaluator/evaluator_env.py`

## 1. End-to-end runtime path

```
scripts/run_seatau.sh
  ↓ resolves preset → sets --lang-id / --lang-components / --mixed-tools-config
  ↓ adds --seatau-experiment / --seatau-target-lang / --seatau-asset-mode
tau2 run                                                  (src/tau2/cli.py)
  ↓ TextRunConfig (validates lang_id against config/languages.json)
runner.batch.run_domain                                   (src/tau2/runner/batch.py)
  ├─ get_missing_translation_component_warnings(...)      → warn (translated)
  │                                                          / raise (localized)
  ├─ get_tasks(...)
  └─ if "tasks" ∈ effective_lang_components:
        load translated tasks.json from {language_asset_id}/
runner.build.build_text_orchestrator                      (src/tau2/runner/build.py)
  └─ apply_language_config(env, config)                   (src/tau2/runner/language.py)
        ├─ schema runtime localization (tools / db output canonicalization)
        ├─ mixed-tools partition (EXP #1)
        ├─ tool docstring patch (EXP #3 / #4 — non-mixed)
        ├─ translated policy.md swap   (string-replace into existing policy)
        ├─ agent_system suffix         (config/languages.json)
        ├─ db.json/db.toml hot-swap    (env.tools.db = db_class.load(...))
        └─ greeting (returned, used by orchestrator as the canned first turn)
runner.simulation.run_simulation
  └─ evaluator.evaluate_simulation (replay rebuilds env + applies same
                                     environment_configurer for parity)
```

Two language signals propagate down two channels:

- `lang_id` — registry key, drives runtime *behaviour* (greeting, user/agent
  system instructions, language-correctness scoring).
- `language_asset_id` — directory name on disk that the loader reads from.

For `translated` they're equal. For `localized` the property returns
`{lang_id}_loc`. That is the entire reason `language_asset_id` exists — see §3.

## 2. Translation-correctness audit (EXP #3 `translated`)

### What is actually present on disk

Surveyed `data/tau2/domains/{airline,retail,telecom}/{id,th,vi,zh,tl}/`:

| Domain   | tools.json | user_tools.json | data_model.json | policy.md | db.json | tasks.json |
| -------- | ---------- | --------------- | --------------- | --------- | ------- | ---------- |
| airline  | yes (all 5) | n/a            | yes (all 5)     | **stale** | **stale** | **stale** |
| retail   | yes (all 5) | n/a            | yes (all 5)     | **stale** | **stale** | **stale** |
| telecom  | yes (all 5) | yes (all 5)    | yes / user yes  | **stale** | **stale** | **stale** |

The translation pipeline (or someone) renamed the stale outputs to
`{name}.stale` — they no longer match the loader's filename checks
(`policy.md`, `db.json`, `tasks.json`). Manifests still exist but only cover
the up-to-date assets.

### What that means for a `translated` run today

`apply_language_config` in `src/tau2/runner/language.py` and
`run_domain` in `src/tau2/runner/batch.py:875–940` use `Path.exists()` gates on
exact filenames. Because the only present filenames are
`tools.json` and `data_model.json`:

- `tools` component → patched with translated docstrings (correct).
- `db` component → `db.json/db.toml` not found → DB stays English silently.
- `policy` component → `*.md` glob excludes `policy.md.stale` → policy stays
  English; translated policy never reaches the model.
- `tasks` component → `tasks.json` not found in `{lang_id}/` → falls back to
  English `data/tau2/domains/{domain}/tasks.json`.
- `agent_system` / `user_system` / `greeting` come from
  `config/languages.json`, which is fully populated → these *do* fire.
- Schema runtime localization (`apply_schema_runtime_localization`) fires if
  `data_model.json` exists, so localized enum/value canonicalization on tool
  outputs is active even though the underlying DB is English.

Net: today's `translated` is operationally "crosslingual + translated tool
descriptions + canonicalizing localizer for a DB that is still English".
The `get_missing_translation_component_warnings` helper does emit warnings,
but `run_domain` only fails-hard for `effective_seatau_asset_mode == "localized"`
(batch.py:884–895). EXP #3 logs warnings and proceeds — easy to miss.

### Confidence of the asset that *is* loaded

- `tools.json` for retail/th: manifest fingerprint matches current
  `src/tau2/domains/retail/tools.py` (sha `34f4fe97…`). Same for retail/vi.
  Tool descriptions are not stale.
- `policy.md` source for retail vi was sha
  `4e05452556f45d7985b75c74faf42421e49dcc308374dd70890879ef7094a525` at
  translation time; current `data/tau2/domains/retail/policy.md` should be
  re-hashed before re-running the translation. (Not done — file rename to
  `.stale` short-circuits this.)
- The string-replace policy patch is order-sensitive: if the source policy
  shows up verbatim inside `environment.policy`, `policy.replace(...)` swaps
  it. Otherwise the loader special-cases `policy.md` → full replacement. This
  is fragile when `policy.md` files in source domains contain templating or
  frontmatter that policy-builders post-process before runtime.

## 3. Design questions answered

### `seatau_asset_mode` and `effective_seatau_asset_mode` — needed?

`seatau_asset_mode` is the user-facing toggle that selects the artefact root.
Three values: `original`, `translated`, `localized`. Only `localized` triggers
strict-fail behaviour. `effective_seatau_asset_mode` exists because the wrapper
and the CLI both pass an *implicit* signal (the experiment name and the set of
enabled `lang_components`) that should imply a mode if `--seatau-asset-mode`
is not set. The current rule
(`src/tau2/data_model/simulation.py:600–611`) is:

1. explicit `seatau_asset_mode` wins;
2. else if `seatau_experiment == "localized"` → `localized`;
3. else if any of `{tools, policy, db, tasks}` ∈ effective components →
   `translated`;
4. else → `original`.

This is needed today because the wrapper (`run_seatau.sh:464`) does pass
`--seatau-asset-mode` from `experiments.yaml`'s `asset_mode` field, but the
fallback rules let `tau2 run` work correctly when called *without* the wrapper
(e.g. in tests, in `evaluate_trajectories.py`). It is also load-bearing for
the env replay path inside the evaluator: replay code only knows
`seatau_asset_mode`, not the preset name, so the explicit field is what gets
forwarded into `_build_language_environment_configurer`.

Recommendation: keep the field, simplify the inference rule to *only* look at
`seatau_experiment`. The component-set heuristic is too implicit and can flip
modes for users who hand-craft `--lang-components`.

### `environment_configurer` — needed?

Yes, for one specific reason: replay equivalence.
`EnvironmentEvaluator.calculate_reward` (and its full-duplex twin) constructs
two *fresh* environments — `predicted_environment` and `gold_environment` —
and replays the trajectory + golden actions on them. Without the configurer,
those replay envs use English tools, English DB, and the canonicalization
layer on the predicted env is missing, so:

- enum normalization (e.g. mapping localized status `"selesai" → "completed"`
  in `runtime_localization._normalize_literal_value`) doesn't run on replay,
  so a tool call captured during the live run with localized arg literals
  raises against the gold schema.
- DB hashes diverge: the live env mutated a localized DB; the gold env
  mutates an English DB → `db_match=False` for everyone.

The configurer (`src/tau2/evaluator/evaluator.py:409–437`) reconstructs a
minimal `TextRunConfig` and calls `apply_language_config(env, config)` again on
both envs. This is correct but coupled. Cleaner: hoist the language wiring out
of `runner/language.py` into a small `LanguageRuntime` object that can be
applied to any environment without rebuilding a `TextRunConfig` shell. Then
both `build_text_orchestrator` and the evaluator hook take that object.

### `config.language_asset_id` vs `config.lang_id`

`lang_id` is the registry key (drives prompts). `language_asset_id` is the
directory name. They diverge only for `localized`, where the loader reads
`{lang_id}_loc`. Defensive code paths use `config.language_asset_id or
config.lang_id` (e.g. `runner/language.py:63`, `runner/batch.py:878,916`) —
that fallback is dead code today: `language_asset_id` already returns
`lang_id` when not localized, and `None` only when `lang_id is None`. Drop the
`or` chain and read `language_asset_id` once. The two-name duality is needed,
but the `... or ...` defensive form is not.

### Translated vs Localized — what's actually different at runtime?

| Aspect                         | translated (`{lang_id}/`)                  | localized (`{lang_id}_loc/`)                          |
| ------------------------------ | ------------------------------------------ | ----------------------------------------------------- |
| Asset root                     | machine-translation outputs                | human-reviewed overlay                                |
| Missing assets                 | warn + silent English fallback             | hard-fail in `run_domain`                              |
| Schema canonicalization        | runs (uses `data_model.json`)              | runs (uses `data_model.json` from `{lang_id}_loc/`)   |
| Greeting / system instructions | `config/languages.json`                    | `config/languages.json` (same)                        |
| Replay parity                  | configurer reapplies same wiring           | configurer reapplies same wiring with `_loc` root     |
| Source-fingerprint check       | manifest stale-warning                     | manifest stale-warning                                |

Localized is *not* an extension of translated (they don't stack). A localized
folder is expected to be self-contained — every component the experiment
declares must be present.

## 4. Concrete gaps

1. `translated` is non-strict. Today the *only* difference between
   "translated" and "crosslingual" for retail/airline is tool docstrings +
   localized schema enums, because policy/db/tasks live as `*.stale` files.
   Either re-translate (fixing fingerprints) and rename back to canonical
   names, or make `translated` strict the same way `localized` is.

2. `*.stale` rename is invisible to the loader and to manifests. Stale assets
   should be expressed by an updated source fingerprint (already supported by
   `get_stale_translation_warnings`), not by renaming files out of view. The
   rename masks the staleness — there is no warning because the loader sees
   nothing.

3. Silent English fallback for declared components. Inside
   `apply_language_config`, the policy/db/tools branches all use
   `if not path.exists(): continue` without logging. Combined with #1, an
   experiment can declare `lang_components: [..., policy, db, tasks]` and end
   up running with English context, with nothing in `results.json` indicating
   it.

4. `results.json.seatau_info.artifact_root` is correct but weak — it points
   at the directory, not at the *files actually loaded*. After the strict
   change, this needs an `artifact_files` map: `{component → path | "english"}`.

5. Translation manifest covers tools and (sometimes) policy/db/tasks. There
   is no manifest entry for the schema localizer (`data_model.json`), so
   stale-warnings don't fire on schema drift, even though the localizer is
   the most fragile part (enum value drift silently breaks canonicalization).

6. The wrapper hardcodes the language matrix in shell (`run_seatau.sh:292–310`)
   *and* in `seatau_logging.py`'s `build_seatau_run_settings`, *and* in the
   yaml. Three sources of truth → drift.

7. SEA-TAU code is sprinkled across the repo with no single entry point and
   no clean scope separation from non-SEA-TAU experiments:
   - top-level `experiments/` — currently just `PLAN.md` (+ this `REPORT.md`).
     No code, no Dockerfile, no result aggregator.
   - `src/experiments/` — polyglot umbrella, holds both SEA-TAU
     `mixed_lang_tools/` *and* unrelated tau2/tau3 work (`hyperparam/`,
     `tau_voice/`, `agentify_tau_bench/` which is its own uv project).
     `runner/language.py:88` resolves `from experiments.mixed_lang_tools`
     here, mixing scopes.
   - `scripts/run_seatau.sh` — shell wrapper.
   - `config/sea-tau/{experiments.yaml,mixed_tools/,README.md}` — preset
     config and matrix docs.
   - `src/tau2/scripts/seatau_logging.py` — SEA-TAU metadata logger living
     under tau2-core.
   - `src/utils/{export_annotation_sheet,db_excel_*}.py` — localization
     workflow buried in generic utils.
   - `src/localization/` — empty placeholder.
   Six locations, three of which mix SEA-TAU with unrelated code.

## 5. Proposed redesign

Keep changes minimal in tau2 core; centralize SEA-TAU code under
`experiments/`.

### 5.1 Tighten the contract

- Make `translated` strict: in `run_domain`, treat the missing-asset list as
  an error whenever `effective_seatau_asset_mode in {"translated", "localized"}`,
  for any component declared in `effective_lang_components`. Today only
  `localized` is strict.
- Replace `*.stale` rename convention with manifest-driven staleness. Rerun
  translation, write fresh files at canonical names; rely on
  `get_stale_translation_warnings` (already wired) to flag drift.
- Add `data_model.json` to manifest source-fingerprint set.
- Add a failing test in `tests/test_translation/` that asserts every
  declared component is loaded from `{lang_id}/` (not English fallback).

### 5.2 Collapse the redundant signals

- Drop `config.language_asset_id or config.lang_id` defensive chains.
  `language_asset_id` is already correct on its own.
- Simplify `effective_seatau_asset_mode` to a pure function of
  `seatau_experiment` (and explicit `seatau_asset_mode` override). Fail loudly
  if `lang_components` and `seatau_experiment` disagree.
- Hoist language wiring into a `LanguageRuntime` dataclass with a single
  `apply(env)` method. `build_*_orchestrator` and
  `_build_language_environment_configurer` both consume it. This removes the
  evaluator's "fake TextRunConfig" trick.

### 5.3 Give SEA-TAU its own top-level Python package; keep `experiments/` for notes only

`experiments/` (top-level) is a research notebook: transient scripts and
markdown — plans, reports, per-run observations, concerns, next steps. It is
**not** a code/config home. Anything durable (presets, mixed-tool configs,
Dockerfiles, integration tests, runner code) moves out.

`src/experiments/` is a polyglot umbrella for tau2/tau3 research projects
(voice, hyperparam sweeps, agentify_tau_bench, mixed_lang_tools). Folding
the entire SEA-TAU runtime under it would mix scopes — voice and hyperparam
are not SEA-TAU. Better: SEA-TAU becomes a peer of `src/tau2/` and
`src/translation/`.

Four roles, four places, no overlap:

| Location              | Role                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------- |
| `experiments/` (top)  | Transient: one-off scripts, plans, reports, per-run notes/concerns/next-steps. No durable config or code. |
| `config/sea-tau/`     | Durable SEA-TAU config (already exists): `experiments.yaml`, `mixed_tools/*.json`, matrix docs. |
| `src/seatau/` (NEW)   | SEA-TAU Python package. Importable as `seatau.*`. Holds runner, preset loader, mixed-lang tools, runtime hook adapter, localization workflow. |
| `src/experiments/`    | Polyglot umbrella for non-SEA-TAU experiments: `hyperparam/`, `tau_voice/`, `agentify_tau_bench/`. `mixed_lang_tools/` moves out to `src/seatau/`. |

#### Final tree — top-level `experiments/`

```
experiments/
  PLAN.md                         # roadmap, status, known gaps
  REPORT.md                       # this file (audit + redesign)
  notes/                          # optional folder if many notes accumulate
    YYYY-MM-DD_<topic>.md         # per-run observations, concerns, next steps
  scripts/                        # transient one-offs: ad-hoc analyses, repro scripts
    YYYY-MM-DD_<purpose>.py       # not a stable surface; promote to src/seatau/ when reused
```

Rule of thumb: if a file in `experiments/` is referenced from anywhere else
in the repo (an import, a CI job, a Dockerfile), it does not belong here.
Promote it to `src/seatau/`, `config/sea-tau/`, `tests/`, or repo-root
`docker/`.

#### Final tree — `config/sea-tau/` (durable config, mostly unchanged)

```
config/sea-tau/
  README.md                       # experiment matrix; source of truth for presets
  experiments.yaml                # preset definitions and aliases (unchanged location)
  mixed_tools/                    # mixed-tool partition configs (unchanged location)
    2lang_uniform_en-th.json
    3lang_uniform_en-th-vi.json
    5lang_uniform_en-th-vi-id-zh.json
```

#### Final tree — `src/seatau/` (NEW)

```
src/seatau/
  __init__.py
  README.md                       # package overview; cross-links to config/sea-tau/README.md
  cli.py                          # `python -m seatau.cli` — replaces scripts/run_seatau.sh shell yaml_eval
  presets.py                      # YAML loader, alias resolver, fanout planner (reads config/sea-tau/)
  runner.py                       # builds & invokes RunConfig; calls tau2 in-process
  runtime.py                      # LanguageRuntime dataclass; consumed by tau2 core hook
  logging.py                      # ← src/tau2/scripts/seatau_logging.py
  results.py                      # post-run aggregator → parquet/CSV across the matrix
  mixed_lang_tools/               # ← src/experiments/mixed_lang_tools/ (SEA-TAU EXP #1)
    __init__.py
    models.py
    partition.py
    README.md
  localization/                   # human-localization workflow (was in src/utils/)
    __init__.py
    export.py                     # was src/utils/export_annotation_sheet.py
    import_reviewed.py            # finishes PLAN.md "import reviewed values into {lang_id}_loc"
    schemas.py
```

#### Final tree — `src/experiments/` (after the move)

```
src/experiments/
  __init__.py
  README.md                       # umbrella for non-SEA-TAU experiments
  hyperparam/                     # unchanged
  tau_voice/                      # unchanged
  agentify_tau_bench/             # unchanged (or hoist to repo-root projects/)
  # mixed_lang_tools/  →  moved to src/seatau/mixed_lang_tools/
```

#### Other repo-root pieces

```
scripts/run_seatau.sh             # becomes a 1-line shim: exec python -m seatau.cli "$@"
docker/                           # NEW (repo-root, not under experiments/)
  Dockerfile                      # uv sync --frozen; bakes data/models/lid.176.bin
  docker-compose.yml              # services parametrized via env: EXP, DOMAIN, LANG
  entrypoint.sh
tests/test_seatau/                # NEW; sibling of existing tests/test_translation/
  test_presets.py                 # alias resolution, supported domains, asset_mode mapping
  test_strict_translated.py       # run_domain fails if a declared component is missing
  test_cli.py                     # smoke: --dry-run for every preset × supported domain
results/                          # gitignored; default --save-to root for runs
```

`scripts/run_seatau.sh` stays where it is so existing instructions don't
break — it just becomes a one-liner. `docker/` and `tests/test_seatau/` are
durable repo-level concerns, not experiment notes.

#### What gets moved / deleted / left in place

| From                                              | To                                                                       |
| ------------------------------------------------- | ------------------------------------------------------------------------ |
| `scripts/run_seatau.sh` (250+ lines of shell)     | same path, becomes 1-line shim → `python -m seatau.cli`                  |
| `config/sea-tau/experiments.yaml`                 | unchanged location; loaded by `seatau.presets`                            |
| `config/sea-tau/mixed_tools/`                     | unchanged location; loaded by `seatau.mixed_lang_tools`                   |
| `config/sea-tau/README.md`                        | unchanged location; remains matrix source of truth                        |
| `src/tau2/scripts/seatau_logging.py`              | `src/seatau/logging.py`                                                  |
| `src/experiments/mixed_lang_tools/`               | `src/seatau/mixed_lang_tools/`                                           |
| `src/utils/export_annotation_sheet.py`            | `src/seatau/localization/export.py`                                      |
| `src/utils/db_excel_*.py`, `db_json_to_excel.py`, `db_excel_merge_translations.py` | `src/seatau/localization/` (annotation pipeline) |
| `src/localization/` (empty)                       | deleted                                                                   |
| `src/experiments/agentify_tau_bench/`             | optionally hoist to repo-root `projects/` (own pyproject + uv.lock; not SEA-TAU) |
| `runner/language.py:88` import                    | `from experiments.mixed_lang_tools import ...` → `from seatau.mixed_lang_tools import ...` |
| `experiments/PLAN.md`, `experiments/REPORT.md`    | unchanged location; new sibling notes go here                             |

#### tau2-core touch (the one allowed change)

A single hook in `tau2.runner.language`:

```python
def apply_language_runtime(env: Environment, runtime: LanguageRuntime) -> str | None: ...
```

`LanguageRuntime` is owned by `seatau.runtime`. Everything
experiment-specific (preset table, fanout, mixed-tools resolver, asset-root
resolution, strict-fail policy, result aggregation, annotation
export/import) lives under `src/seatau/`. The existing
`apply_language_config(env, config)` becomes a thin adapter that constructs a
`LanguageRuntime` from the run config and calls the hook — preserves
backward compatibility with `tau2 run --lang-id ...` invocations that don't
go through SEA-TAU presets.

### 5.4 Containerized, reproducible runs

- Dockerfile in `experiments/docker/`: pinned base image,
  `uv sync --frozen`, no editable installs, mounts `data/` read-only and
  `output/` read-write. Include `data/models/lid.176.bin` download step
  (or bake it in) so language correctness scoring is deterministic.
- `docker-compose.yml` defines one service per `(experiment, domain, lang)`
  triple, parametrized via env vars; `experiments/scripts/run.py` shells out
  to `docker compose run` so local and CI use the same path.
- Pin LLM provider model strings inside `presets.yaml` (`agent_llm_default`,
  `user_llm_default`); record them in `results.json.seatau_info.models`.
- Include `git_commit` (already in `Info`) plus a `data_commit` field that
  hashes the loaded artefacts (manifest digests + DB hash) so re-runs are
  bit-comparable.

### 5.5 Result schema

Extend `SeaTauInfo` with:

- `artifact_files: dict[str, str | None]` — actual path or `None` for English
  fallback (after strict mode this is rarely None; before, it's the audit
  trail).
- `manifest_digest: str` — sha256 of the relevant `translation_manifest.json`.
- `mixed_tools_partition: dict[str, list[str]] | None` — already partly logged
  by the runner, persist it.
- `language_correctness: float` — already in `reward_info.info`, hoist a
  per-run aggregate up.

This unblocks the PLAN.md "Expand results.json metadata" item.

## 6. Minimum-viable change set (one PR)

1. `run_domain` strict-fail for `translated` mode (mirror the existing
   `localized` branch, batch.py:884–895).
2. Stop using `*.stale` filename suffixes; let manifest staleness do the job.
   Re-translate to canonical names, or move hand-edits into `{lang_id}_loc/`.
3. Create `src/seatau/` (sibling of `src/tau2/`, `src/translation/`).
   Replace `scripts/run_seatau.sh` shell-yaml logic with `src/seatau/cli.py`
   (50-ish lines using PyYAML, reading `config/sea-tau/experiments.yaml` in
   place). `scripts/run_seatau.sh` becomes a one-line
   `exec python -m seatau.cli "$@"`. CLI surface unchanged.
4. Move `src/tau2/scripts/seatau_logging.py` → `src/seatau/logging.py`;
   move `src/experiments/mixed_lang_tools/` → `src/seatau/mixed_lang_tools/`;
   update the import at `runner/language.py:88` and the logger call site.
   `config/sea-tau/{experiments.yaml,mixed_tools/}` stay in place.
5. Drop `or config.lang_id` defensive chains; simplify
   `effective_seatau_asset_mode` to depend only on
   `seatau_experiment` + explicit override.
6. Add `docker/Dockerfile` + compose service at repo root that runs one
   `(experiment, domain, lang)` triple via the new CLI.
7. Create `tests/test_seatau/` with strict-translated, preset-resolution,
   and CLI smoke tests.

Items 1 and 5 are bug fixes; 2 is data hygiene; 3–4 and 6–7 are the
structural consolidation. None of them touch tau2 core except item 5 (a
~10-line edit in `data_model/simulation.py`) and the new
`apply_language_runtime` hook described in §5.3.

After all of this, top-level `experiments/` contains exactly what its name
promises: `PLAN.md`, `REPORT.md`, and ad-hoc notes/scripts that don't yet
deserve a permanent home.
