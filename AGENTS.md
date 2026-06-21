# SEATauBench Analysis and Figures

All experiment runs are done and stored in `data/simulations/` with mapping for each simulation ran in `data/seatau/experiments.csv`. Some simulations lack mapping but work with existing known ones for the following tasks

## TODOs

### 1. Scenario names

- Scenario names (code name & display name) across this project:
  - `english` & "En Baseline"
  - `l2_tools` & "L2 Tools"
  - `l2_interaction` & "L2 Interaction"
  - `l2_domain` & "L2 Domain"

The canonical names are used for datasets and code, while the quoted labels are used for figures.

Relevant files and directories to explore:

- `data/simulations/`
- `src/seatau/scenarios.yaml`, `experiment_matrix.py`
- `src/seatau/plot/config.py`

### 2. Remove experiments with `qwen-3.6-35b`

- [x] Back up relevant files & folders first
- [x] Remove rows where `agent_llm` = `qwen-3.6-35b` in `data/seatau/experiments.csv`. Record the `simulation_source` column values of those rows
- [x] Remove the nested folders under `data/simulations/` that match the mentioned `simulation_source` values
- [x] Confirm that the above steps are done correctly.

### 3. Normalize models in `src/utils/normalize_models.py`

- [x] Write code so (1) we extract all llm values (user & agent) observed in `data/simulations/[dir]/results.json` and (2) normalize them to these options only:

- `gpt-5-mini`
- `kimi-k2.5`
- `qwen-3-235b-it`

Make sure the code is minimal, as in we infer some rule first, like `[api]/[model_developer]/[model_name_full]` and then deal with model variant from full model name later. The normalization is NOT in-place, we do NOT edit `results.json`.

The list above is for code. For display model name, we replace hyphens with spaces and capitalize each word.

### 4. Regenerate `experiments.csv`

- [x] Given `data/simulations/`, regenerate `data/seatau/experiments.csv`. This includes:
  - normalizing the agent llm name
  - computing `rho_hat_3`
  - copying values to the remaining columns

### 5. Collect constants related to SEATau across scripts

1. Rename `src/seatau/paths.py` to `src/seatau/constants.py` and fix downstream
2. Move the constants related to SEATau scenarios or languages to `src/seatau/constants.py`. Don't duplicate what's already defined in `src/seatau/scenarios.yaml`

### 7. Unify figure setting in `src/seatau/plot/config.py`

- Should use display model names above
- Should use four scenario names above
- Font: Helvetica Neue, consistent title sizes
- Color scheme:

* sea-red: #ed2939;
* sea-blue: #0042a6;
* sea-yellow: #f9e300;
* sea-white: #ffffff;
* sea-black: #111111;

### 6.

### Generate annotations for humans to validate translations from `data/tau2/domains/{domain}/{lang_id}/`

### Rewrite README

- Change to describe SEATauBench
- Change
