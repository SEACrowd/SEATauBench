# SEA-Tau Experiments

Our big goals is to run all domains, all languages, for `translated` experiment.

1. Determine the next steps: Check `experiments/experiments.csv` (60 rows: 3 domains x 4 models x 5 languages) for experiment tracking, and also `data/simulations/` for partial experiments. Prioritize resuming partial experiments. But if it has too many errors, skip and restart cleaner.
2. Set up relevant script by following the guide below. Take note of the saved folder.
3. Monitor the progress every 15-20 minutes, autonomoulsy fix any errors that arise. Particularly, make sure `localhost:8000` is alive, has job, to run the default user-llm. Do NOT count `litellm.ContentPolicyViolationError` (Azure content filter) as error, continue.
   - If the port fails and you cannot resurrect it quickly, start `scripts/lanta_vllm_watchdog.sh` from the repo root and leave it running as the fallback keeper. It polls the model API, reopens the SSH tunnel, and resubmits the SLURM job if needed.
4. Find the live note `experiments/YYYYMMDD_{experiment}_{agent-llm}.md` and incrementally fill in the details for all domains & all languages in there. You do this by EITHER exploring output trajectories inside saved folder (usually `results.json`) OR reading live log traces. You must answer the guiding questions. If the file doesn't exist yet, copy the template `YYYYMMDD-experiment-and-analysis-template.md` to create a new file. **Run the analysis scripts (see below) and paste their output into the relevant sections.**
5. After obtaining all relevant output trajectories, write high-level metrics to `experiments/experiments.csv`. The columns needed are `progress,progress_notes,experiment,domain,language_or_scenario,agent_llm,simulation_source,pass_hat_1,pass_hat_2,pass_hat_3,read_action_count,read_acount_total,read_action_percent,write_action_count,write_acount_total,write_action_percent,db_match,language_correctness,total_simulations,total_tasks
`. `progress` column should be one of: TODO, DONE, PARTIAL, IN_PROGRESS, NEEDS_CHECK
6. After a sweep run, again, determine the next steps based on `experiments.csv` progress. Verify that your log analysis is detailed, truthy, and helpful.

## Set up

- Experiment preset: `translated`
- Languages: `id`, `th`, `tl`, `vi`, `zh`. Prioritize finishing a domain with all languages before moving to another domain.
- Agent LLM: `azure/gpt-5-mini` -> `azure/kimi-k2.5` -> `openrouter/qwen/qwen3.6-35b-a3b` -> user-llm default
- User LLM: default Qwen3-235B-A22B-Instruct-2507-FP8 from `src/tau2/config.py`
- User LLM API base: `http://127.0.0.1:8000/v1`
- Fallback port keeper: `scripts/lanta_vllm_watchdog.sh`
- Domain: retail -> airline -> telecom
- All tasks (we don't pass `--num-tasks`)
- Trials requested: `3`
- Concurrency:
  - For `azure/kimi-k2.5`, start at `--max-concurrency 5`; if it stays clean, you can push toward `6` before backing off on retries, otherwise gradually decrease to `--max-concurrency 2`.
  - For `azure/gpt-5-mini`, start at `--max-concurrency 35`; if it stays clean, you can push toward `40` before backing off on retries, otherwise gradually decrease to `--max-concurrency 30`.
  - OpenRouter `qwen/qwen3.6-35b-a3b` can run with higher concurrency, typically `--max-concurrency 40` and possibly higher if the run stays clean.
  - You should run one Azure & one OpenRouter model in parallel to make the benchmark run faster
  - When user and agent LLM are the same (Qwen3-235B-A22B-Instruct-2507-FP8), concurrency and limits might suffer. Progress monitoring, server fix, and `scripts/lanta_vllm_watchdog.sh` will be important here.

Use the dedicated sweep helpers when possible:

- Azure: `scripts/run_azure_translated_sweep.py`
- OpenRouter: `scripts/run_openrouter_translated_sweep.py`
- OpenRouter Kimi: `run_kimi_translated_sweep.py`

Main script:

```bash
uv run seatau \
  --experiment translated \
  --domain {retail,airline,telecom} \
  --agent-llm azure/gpt-5-mini \
  --num-trials 3 \
  --max-concurrency 10 \
  --save-to {YYYY-MM-DD-HH-MM-SS_experiment_domain_trial-num-trial_lang-or-scenario_agent-llm}
```

Optional:

- `--lang-id {id,th,tl,vi,zh}` (languages from `src/seatau/languages.json`). Or leave this option empty.
- `--auto-resume` resume from the existing checkpoint
- Use `--resume-partials` when resuming `PARTIAL` or `IN_PROGRESS` rows in place.

Required keys depend on the task:

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — for LLM-based agents and user simulators
- `ELEVENLABS_API_KEY` — voice synthesis
- `DEEPGRAM_API_KEY` — voice transcription
Saved folder example:

`2026-05-16-00-05-49_translated_airline_trial-3_zh_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8`

### Rate limit details

| Avg Kimi tokens/request | Max theoretical RPM before TPM exhaustion |  Safe RPM |
| ----------------------: | ----------------------------------------: | --------: |
|                     500 |                        100 RPM, RPM-bound | 60–75 RPM |
|                   1,000 |                         100 RPM, balanced | 60–75 RPM |
|                   2,000 |                         50 RPM, TPM-bound | 30–40 RPM |
|                   5,000 |                         20 RPM, TPM-bound | 12–15 RPM |
|                  10,000 |                         10 RPM, TPM-bound |   6–8 RPM |

## Progress & next steps

`experiments/experiments.csv` is the single source of truth for all 60 planned runs (5 languages × 3 domains × 4 agent LLMs). Check the `progress` column before starting any run.

**Current status (2026-05-18):** 6 DONE (airline ×5 gpt-5-mini, retail ×1 gpt-5-mini). 4 NEEDS_CHECK (telecom/id gpt-5-mini, retail/id+th+vi kimi-k2.5 — all have significant infra failures, see `progress_notes`). 50 TODO remaining.

**Next action:** Run `TODO` and `NEEDS_CHECK` rows in the order retail → telecom, one language at a time. After each run completes, update the matching CSV row: set `progress=DONE`, fill all metric columns, set `simulation_source`.

IMPORTANT: Only experiments with num_trials=3, all tasks, and minimal errors count as DONE.

## Analysis Scripts

Use these after a run finishes (or at any checkpoint) to fill the **Log & Trace Analysis** sections of the live note. All three accept one or more `results.json` paths or run directories, and an optional `--output <path.csv>` to save per-simulation rows.

```bash
# Action sequence patterns — read/write failure breakdown, write attempted vs. skipped
uv run analyze-action-sequences data/simulations/<run_dir>/results.json

# User simulator language drift (requires uv run for fastText)
uv run analyze-user-language data/simulations/<run_dir>/results.json

# Agent language correctness — uses stored metric when present; add --recalculate to recompute
uv run analyze-agent-language data/simulations/<run_dir>/results.json
```

Results go to `data/simulations/`. Use `tau2 view` to browse them.

Multiple runs at once (e.g. all retail runs):

## Architecture

```
src/tau2/
├── agent/           # Agent implementations (half-duplex and full-duplex)
├── api_service/     # FastAPI-based API service
├── config.py        # Central configuration (single source of truth for defaults)
├── cli.py           # CLI entry point (tau2 command)
├── data_model/      # Pydantic data models (messages, trajectories, etc.)
├── domains/         # Domain definitions (airline, mock, retail, telecom, banking_knowledge)
├── environment/     # Environment, DB, server, toolkit base classes
├── evaluator/       # Task evaluation logic
├── gym/             # Gymnasium-compatible RL interface
├── knowledge/       # Knowledge retrieval pipeline (embedders, retrievers, postprocessors, sandbox)
├── metrics/         # Metrics computation
├── orchestrator/    # Simulation orchestrators (half-duplex, full-duplex)
├── registry.py      # Global registry for agents, domains, tasks, users
├── runner/          # Simulation runner (batch execution, checkpointing, build helpers)
├── scripts/         # CLI command implementations
├── user/            # User simulator implementations
├── utils/           # Shared utilities
└── voice/           # Voice synthesis, transcription, audio-native providers
    └── audio_native/  # Real-time voice providers (openai, gemini, nova, xai, deepgram, qwen, livekit)
```

Other top-level directories:

- `data/` — Domain data (JSON, TOML, policies), simulation outputs
- `tests/` — All tests (pytest)
- `scripts/` — Standalone utility scripts
- `src/experiments/` — Research/experimental code (self-contained)
- `docs/` — User-facing documentation

## Key Patterns

### Registry System

All agents, domains, tasks, and user simulators are registered in `src/tau2/registry.py`. To add a new component, register it there:

```python
registry.register_agent_factory(create_my_agent, "my_agent")
registry.register_domain(get_environment, "my_domain")
registry.register_tasks(get_tasks, "my_domain", get_task_splits=get_tasks_split)
```

### Agent Architecture

Two base classes, determined by communication mode:

| Mode                     | Base class        | Key method                | Used by                        |
| ------------------------ | ----------------- | ------------------------- | ------------------------------ |
| Half-duplex (turn-based) | `HalfDuplexAgent` | `generate_next_message()` | `LLMAgent`                     |
| Full-duplex (streaming)  | `FullDuplexAgent` | `get_next_chunk()`        | `DiscreteTimeAudioNativeAgent` |

Both share the constructor signature: `__init__(self, tools: list[Tool], domain_policy: str)`.
For LLM-based agents, mix in `LLMConfigMixin` to add `llm` and `llm_args` parameters.

### Domain Structure

Each domain (`src/tau2/domains/<name>/`) contains:

- `data_model.py` — DB subclass with domain data models
- `tools.py` — `ToolKitBase` subclass with domain tools
- `environment.py` — `get_environment()`, `get_tasks()`, `get_tasks_split()`
- `user_tools.py` (optional) — user-facing tools
- `utils.py` — data paths and helpers

Domain data lives in `data/tau2/domains/<name>/` (tasks.json, policy.md, db.json/toml, etc.).

**Note:** The `banking_knowledge` domain extends the standard pattern with additional files (`retrieval.py`, `retrieval_mixins.py`, `retrieval_toolkits.py`, `db_query.py`), dynamic tools and policy that vary by `--retrieval-config`, and a separate `knowledge/` retrieval pipeline module. Its data directory also includes `documents/`, `prompts/`, and `tasks/` subdirectories. See `src/tau2/knowledge/README.md` for details.

### Orchestrators

- `Orchestrator` — half-duplex, turn-based, synchronous tool execution
- `FullDuplexOrchestrator` — full-duplex, tick-based, simultaneous agent/user activity

## Testing

Tests are split into tiers matching the optional dependency groups. Each tier has its own Make target and required install extras:
Multiple runs at once (e.g. all retail runs):

```bash
uv run analyze-action-sequences data/simulations/2026-05-*retail*/results.json
```

Test layout mirrors source:

- `tests/test_domains/` — per-domain tool and user-tool tests (except `test_banking_knowledge/` which requires the `knowledge` extra)
- `tests/test_streaming/` — streaming/full-duplex tests (requires `voice` extra)
- `tests/test_voice/` — audio-native provider tests (requires `voice` extra; individual providers gated by `{PROVIDER}_TEST_ENABLED=1`)
- `tests/test_gym/` — gymnasium RL interface tests (requires `gym` extra)
Paste output into the live note:

| Script                     | Live note section                                                |
| -------------------------- | ---------------------------------------------------------------- |
| `analyze-action-sequences` | Task Analysis → pattern counts + failing task list               |
| `analyze-user-language`    | User Simulator Analysis → Language drift                         |
| `analyze-agent-language`   | Agent Analysis → Language drift (for runs without stored metric) |

## Update `errors.csv` results

Ruff rules: `E4`, `E7`, `E9`, `F`, `I` (with `E501` and `F541` ignored).

## Commit Conventions

```
feat: add memory system to agent base class
fix: resolve environment tool timeout issues
docs: update domain contribution guidelines
test: add integration tests for retail domain
```

## Things to Watch Out For

- **`.env` file**: Never commit this. Contains API keys. Use `.env.example` as reference.
- **`data/` directory**: Contains domain data that the framework depends on. Be careful modifying JSON/TOML data files.
- **`config.py`**: Single source of truth for default configuration values. Import constants from here rather than defining local duplicates.
- **`registry.py`**: All new agents, domains, and user simulators must be registered here to be usable via CLI.
- **Audio native providers**: Each has its own WebSocket protocol and event format. Always verify against provider documentation. See `.cursor/rules/audio-native-provider.md` for the full implementation guide.
- **Task splits**: The `base` split is the default for evaluation. The `train`/`test` splits are for RL experiments.
- **Pre-commit hook**: Runs `make check-all` (ruff lint + format). Fix any issues before committing.
- **Notebooks**: Excluded from ruff (`*.ipynb` in pyproject.toml exclude).
- **`banking_knowledge` domain**: Uses `--retrieval-config` to specify how the agent accesses the knowledge base. If omitted, defaults to `bm25` (offline, no API keys needed). Offline configs: `no_knowledge`, `full_kb`, `golden_retrieval`, `bm25`, `bm25_grep`, `grep_only`. `openai_embeddings*` configs require `OPENAI_API_KEY`. `qwen_embeddings*` configs require `OPENROUTER_API_KEY` (included in `.env.example`). `*_reranker` configs additionally require `OPENAI_API_KEY` for the LLM reranker. `terminal_use*` configs require `sandbox-runtime` (`npm install -g @anthropic-ai/sandbox-runtime@0.0.23`). Embedding cache lives in `data/.embeddings_cache` (gitignored). See `src/tau2/knowledge/README.md` for full details.

# SEA-Tau Experiments

Our big goals is to run all domains, all languages, for `translated` experiment.

1. Run the script & save to a folder
2. Monitor the progress every 10 minutes, autonomoulsy fix any errors that arise.
3. After all relevant output trajectories are obtained, write to `experiments/YYYY-MM-DD-{experiment}-{domain}-{languages or all}-{other details}.md` the following:

- Command used, including setup like user-llm, agent-llm, domain, number of tasks, number of trials
- High-level metrics, by domain & language & agent-llm. Relevant metrics must be included are pass^1, pass^2, pass^3, Read Actions, Write Actions, DB Match, total simulations, language correctness. IMPORTANT: group by domain & language & agent-llm.
- Autonomously
After all runs in TODOS are complated, Aggregate analyses across live notes markdown files to `experiments/errors.csv`. You can expand that file as needed.
