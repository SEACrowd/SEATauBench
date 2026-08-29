# SEA-TAU

SEA-TAU adds four multilingual scenarios on top of `tau2`:

- `english`
- `l2_tools`
- `l2_interaction`
- `l2_domain`

Those scenario ids are the canonical names used in code, `experiments.csv`,
and the simulation directory layout.

## Layout

```text
data/seatau/
  scenarios.yaml        # scenario definitions
  languages.json        # supported language registry

src/seatau/
  experiment_matrix.py  # scenario preset lookup helpers
  translation/          # machine translation and runtime localization
  annotation/           # Excel review workflow for translated assets
  l2_tools_mix/         # mixed-tool partition configs
```

## Run a scenario

Use the `tau2` entry point:

```bash
# En Baseline
uv run tau2 run \
  --domain retail \
  --seatau-scenario english \
  --lang-id en \
  --num-tasks 5 \
  --agent-llm azure/gpt-5-mini

# L2 tools
uv run tau2 run \
  --domain retail \
  --seatau-scenario l2_tools \
  --lang-id vi \
  --lang-components tool_mix \
  --tool-mix-config 5lang_uniform_en-th-vi-id-zh \
  --num-tasks 5 \
  --agent-llm azure/gpt-5-mini

# L2 interaction
uv run tau2 run \
  --domain retail \
  --seatau-scenario l2_interaction \
  --lang-id vi \
  --lang-components user_system agent_system greeting \
  --num-tasks 5 \
  --agent-llm azure/gpt-5-mini

# L2 domain
uv run tau2 run \
  --domain retail \
  --seatau-scenario l2_domain \
  --lang-id vi \
  --lang-components user_system agent_system greeting tools policy db tasks \
  --num-tasks 5 \
  --agent-llm azure/gpt-5-mini
```

`--seatau-scenario` selects the scenario preset. `tau2` applies the
scenario-specific asset mode, language components, and mixed-tool rules.

## Regenerate `experiments.csv`

`data/seatau/experiments.csv` is derived from `data/simulations/`:

```bash
uv run python -m seatau.generate_scenario_summary
```

The generator reads each `results.json`, normalizes the agent model, computes
`rho_hat_3`, and writes the compact CSV used by the analysis scripts.

## Supporting docs

- `translation/README.md`
- `annotation/README.md`
- `l2_tools_mix/README.md`
