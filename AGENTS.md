# AGENTS.md

> Instructions for AI coding agents working on the τ-bench codebase.

## Project Overview

τ-bench is a simulation framework for evaluating conversational customer service agents. It supports text and voice interactions in half-duplex (turn-based) and full-duplex (simultaneous/streaming) communication modes. Domains include `mock`, `airline`, `retail`, `telecom`, and `banking_knowledge`.

## Setup

```bash
uv sync                        # core only (airline, retail, telecom, mock)
uv sync --extra voice          # + voice/audio-native features
uv sync --extra knowledge      # + banking_knowledge domain (retrieval pipeline)
uv sync --extra gym            # + gymnasium RL interface
uv sync --extra dev            # + pytest, ruff, pre-commit (required for committing)
uv sync --extra experiments    # + plotting libs for src/experiments/
uv sync --all-extras           # everything
uv run tau2 check-data         # verify installation
```

**Note:** `langfuse` and `redis` are not declared dependencies but may be needed if you enable `USE_LANGFUSE=True` or `LLM_CACHE_ENABLED=True` with `redis` cache type in `config.py`. Install them manually if needed (`uv pip install langfuse redis`).

Environment variables: copy `.env.example` to `.env` and set API keys. Uses [LiteLLM](https://github.com/BerriAI/litellm) for LLM provider abstraction.

Required keys depend on the task:

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — for LLM-based agents and user simulators
- `ELEVENLABS_API_KEY` — voice synthesis
- `DEEPGRAM_API_KEY` — voice transcription

## Common Commands

| Command               | What it does                                                    | Required install                        |
| --------------------- | --------------------------------------------------------------- | --------------------------------------- |
| `make test`           | Run core tests (skips voice, streaming, gym, banking_knowledge) | `uv sync --extra dev`                   |
| `make test-voice`     | Run voice + streaming tests                                     | `uv sync --extra voice --extra dev`     |
| `make test-knowledge` | Run banking_knowledge tests                                     | `uv sync --extra knowledge --extra dev` |
| `make test-gym`       | Run gymnasium tests                                             | `uv sync --extra gym --extra dev`       |
| `make test-all`       | Run all tests                                                   | `uv sync --all-extras`                  |
| `make lint`           | Lint with ruff                                                  | `uv sync --extra dev`                   |
| `make format`         | Format with ruff                                                | `uv sync --extra dev`                   |
| `make lint-fix`       | Lint and auto-fix                                               | `uv sync --extra dev`                   |
| `make check-all`      | Run lint + format (same as pre-commit hook)                     | `uv sync --extra dev`                   |
| `make clean`          | Remove venv, caches, build artifacts                            | —                                       |
| `make env-cli`        | Interactive environment CLI for testing domain tools            | —                                       |

`make test` is the safe default -- it works with just `uv sync --extra dev` and does not require voice, knowledge, or gym packages. Always run `make check-all` before committing. A pre-commit hook enforces this.

## Running Evaluations

```bash
# Text half-duplex (standard)
tau2 run --domain airline --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-trials 1 --num-tasks 5

# Voice full-duplex (audio native)
tau2 run --domain retail --audio-native --num-tasks 1 --verbose-logs

# Knowledge domain (requires --retrieval-config)
tau2 run --domain banking_knowledge --retrieval-config qwen_embeddings --agent-llm gpt-4.1 --user-llm gpt-4.1 --num-tasks 5
```

Results go to `data/simulations/`. Use `tau2 view` to browse them.

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

```bash
# Core tests — works with just `uv sync --extra dev`
make test

# Voice + streaming tests — requires `uv sync --extra voice --extra dev`
make test-voice

# Banking knowledge tests — requires `uv sync --extra knowledge --extra dev`
make test-knowledge

# Gymnasium tests — requires `uv sync --extra gym --extra dev`
make test-gym

# All tests — requires `uv sync --all-extras`
make test-all

# Domain-specific (core domains work with `make test`)
pytest tests/test_domains/test_<domain_name>

# Specific test file
pytest tests/test_agent.py

# Skip full-duplex integration tests (require live APIs)
pytest -m "not full_duplex_integration"
```

Test layout mirrors source:

- `tests/test_domains/` — per-domain tool and user-tool tests (except `test_banking_knowledge/` which requires the `knowledge` extra)
- `tests/test_streaming/` — streaming/full-duplex tests (requires `voice` extra)
- `tests/test_voice/` — audio-native provider tests (requires `voice` extra; individual providers gated by `{PROVIDER}_TEST_ENABLED=1`)
- `tests/test_gym/` — gymnasium RL interface tests (requires `gym` extra)

## Code Style

- **Formatter/linter**: Ruff (configured in `pyproject.toml`)
- **Line length**: 88 characters
- **Python**: >=3.12, <3.14
- **Type hints**: Encouraged, especially for public APIs
- **Docstrings**: Required for public APIs and complex functions
- **Import sorting**: Handled by ruff
- **Models**: Use Pydantic `BaseModel` for data classes

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
