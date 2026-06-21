# AGENTS.md

> Operating guide for AI coding agents working on the SEATauBench / `tau2`
> repository.

## Scope

This repo layers SEATauBench on top of the upstream `tau2-bench` framework.

- `src/tau2/` contains the upstream simulation runtime, domains, evaluator,
  runner, CLI, and shared utilities.
- `src/seatau/` contains the SEATauBench layer: scenarios, translation,
  annotation, metrics, analysis, plotting, and benchmark-specific helpers.
- Generated or data-heavy outputs typically live in `data/simulations/`,
  `data/analyses/`, and `figs/`.

If a subdirectory has its own `AGENTS.md`, follow the more specific file for
that area.

## Setup

Use `uv` for dependency management.

```bash
uv sync                        # core runtime
uv sync --extra dev            # linting, tests, formatting
uv sync --extra experiments    # analysis and plotting
uv sync --extra voice          # voice / audio-native features
uv sync --extra knowledge      # banking_knowledge domain
uv sync --extra gym            # gymnasium RL interface
uv sync --all-extras           # everything
uv run tau2 check-data         # verify the installation
```

Copy `.env.example` to `.env` and add the API keys needed for the task. Common
keys include `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
`VERTEXAI_PROJECT`, `VERTEXAI_LOCATION`, `ELEVENLABS_API_KEY`, and
`DEEPGRAM_API_KEY`.

Do not commit secrets, generated datasets, or other large derived artifacts
unless the task explicitly asks for them.

## Common Commands

### Quality checks

```bash
make test
make test-voice
make test-knowledge
make test-gym
make test-all
make lint
make format
make lint-fix
make check-all
```

`make test` is the safest default. Run `make check-all` before committing.

### SEATauBench workflows

```bash
uv run python -m seatau.generate_scenario_summary
uv run plot all
uv run plot list
uv run python -m seatau.translation.cli --help
uv run python -m seatau.annotation export --help
uv run python -m seatau.annotation import --help
```

For experiments, use the `tau2` CLI with the SEATauBench scenario flag and the
appropriate domain and language settings.

## Repository Layout

- `src/tau2/` - upstream benchmark code
- `src/seatau/` - SEATauBench-specific code
- `data/tau2/` - domain assets and localized overlays
- `data/seatau/` - benchmark metadata, experiments, annotations, and analysis
- `data/simulations/` - simulation run outputs
- `figs/` - generated figures
- `tests/` - automated tests
- `README.md` - project overview and end-to-end workflows

## Project Conventions

- Follow the project’s existing configuration sources instead of duplicating
  constants locally.
- Keep scenario definitions, language definitions, and plotting labels aligned
  with the canonical benchmark files in `src/seatau/`.
- Prefer `pathlib.Path`, type annotations, and small single-purpose functions.
- Use Ruff for formatting and linting, and pytest for tests.
- When changing plots or documentation, verify the rendered output rather than
  assuming the source text is enough.

## Key References

- `README.md` for the high-level benchmark overview and workflows
- `src/seatau/scenarios.yaml` for scenario presets
- `src/seatau/languages.json` for supported languages
- `src/tau2/config.py` for runtime defaults and model configuration
- `src/seatau/translation/README.md` for translation workflow details
- `src/seatau/annotation/README.md` for annotation workflow details
