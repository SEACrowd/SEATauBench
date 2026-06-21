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

### 5. Refactor metrics

- Move metric functions from `src/seatau/generate_scenario_summary.py` to be public functions in `src/seatau/metrics/performance.py`, and then update paths.
- Post-hoc compute user_language_correctness and agent_language_correctness with fastText language detection. Abstract that language detection logic from `src/tau2/evaluator/language_correctness.py` to `src/seatau/metrics/language_use.py`, and then use that common logic in both `src/seatau/metrics/language_use.py` and `src/tau2/evaluator/language_correctness.py` after refactoring.

### 6. Collect constants related to SEATau across scripts

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

### 8. Refactor analysis and plot utils

- Plot code is under `src/seatau/plot/` and plots are saved in `figs`. Analysis code is under `src/seatau/analysis/` and analysis data are saved in `data/analyses/`. Define them in `src/seatau/constants.py` and reuse the paths.
- Refactor common plot code to `src/seatau/plot/plot_utils.py`, such as some from `src/seatau/plot/*_common.py`
- Refactor common data code to `src/seatau/plot/data_utils.py`. Also maybe this module should be under `src/seatau/analysis/` instead.
- Regenerate all non-temp figures from `src/seatau/plot/`

### 9. Generate annotations for humans to validate translations from `data/tau2/domains/{domain}/{lang_id}/`

### 10. Rewrite README

- Change to describe SEATauBench
- Reproducibility
  - `uv run plot list` to see all available plots
  - Manual:
    1. Download the zip into `data/simulations`
    2. Generate summary metrics across scenarios with `src/seatau/generate_scenario_summary.py`
    3.
- Run experiments
  - To run current or more models: add OPENROUTER_API_KEY -> 
  - To add more languages: add to `languages.json` -> generate translation pipeline -> 

### 11. Cross-scenario analysis

-
