# Analysis artifacts and plot inputs

`data/analyses/` contains derived tables for the SEA-TAU analysis and plotting
pipeline. The registered plotting commands in `src/seatau/plot/` read these
tables, the canonical experiment index in `data/seatau/experiments.csv`, or
both. They write figures to the repository-level `figs/` directory, not to
`data/analyses/figs/`.

## Data flow

The normal pipeline is:

```text
data/simulations/**/results.json
  -> data/seatau/experiments.csv
  -> data/analyses/**/*.csv
  -> figs/<figure-stem>.{pdf,png}
```

`data/seatau/experiments.csv` is the canonical run index. Each row identifies a
scenario, domain, language, agent model, simulation directory, and summary
metrics. The file uses the column name `language_senario`; keep that spelling
when consuming the CSV.

The canonical scenario and language definitions are:

- `data/seatau/scenarios.yaml`: `english`, `l2_tools`, `l2_interaction`, and
  `l2_domain` are the primary scenarios. `l2_tools_mix` is the auxiliary
  mixed-language tool scenario. The supported domains are `airline`, `retail`,
  and `telecom`.
- `data/seatau/languages.json`: language codes, display names, instruction
  labels, and greetings for English, Thai, Vietnamese, Indonesian, Chinese,
  and Filipino.

The other `data/seatau/` directories are supporting artifacts rather than
direct plot inputs:

- `annotations/` contains the current translation-review workbooks and
  manifests.
- `annotations_legacy/` contains the previous review workbooks.
- `audits/` contains annotation audit outputs.
- `stats/` contains translation-corpus statistics. See
  `data/seatau/stats/README.md` for regeneration instructions.

## Generate the analysis tables

Run these commands from the repository root after the simulation runs are
available. The language analyses and drift diagnostics require the configured
fastText language-identification model.

```bash
# Refresh the canonical run index.
uv run python -m seatau.generate_scenario_summary

# Recompute run-level language metrics from results.json.
uv run python -m seatau.analysis.experiment_language_summary

# Build the performance and correlation tables.
uv run python -m seatau.analysis.perf_by_language
uv run python -m seatau.analysis.en_vs_l2_perf
uv run python -m seatau.analysis.metric_correlations_by_language

# Build the language-drift tables.
uv run python -m seatau.analysis.language_drift_summary
uv run python -m seatau.analysis.language_drift_diagnostics

# Unpack the review export into the tidy error-tag table.
uv run python -m seatau.analysis.error_tag_rates
```

The commands use the canonical paths from `src/paths.py`. Use each module's
`--help` output to provide a different input or output path.

## Analysis artifacts

### Run and performance tables

| Path | Contents | Plot consumers |
|---|---|---|
| `experiment_language_summary.csv` | One row per experiment run with pass rates, `rho_3`, user and agent language correctness, turn totals, non-target language proportions, drift turns, and detected-language proportions. | `language_vs_robustness_corr` |
| `perf_by_language.csv` | Model-by-language estimates for `pass@1` and `rho^3`, with bootstrap intervals over domain-level means. | `perf_by_language` |
| `en_vs_l2_perf.csv` | Domain-by-model English and non-English estimates, confidence intervals, and the number of non-English languages. | `en_vs_l2_perf` |
| `metric_correlations_by_language.csv` | Pearson correlation and R-squared between language-correctness metrics and outcome metrics. Includes `summary_level` values `overall`, `scenario`, `domain`, and `scenario_domain`. | Analysis table only; `metric_correlation_matrix` computes a different correlation table directly from `data/seatau/experiments.csv`. |

`experiment_language_summary.csv` is derived from each referenced
`results.json` and uses fastText detections. A nonempty
`language_detector_warning` column identifies runs whose language metrics need
review.

### Language-drift tables

| Path | Contents | Plot consumers |
|---|---|---|
| `language_drift_summary/agent_language_drift_by_task.csv` | Task-level agent language-drift summary. | `agent_english_share_boxplots`, `agent_english_share_by_model_heatmap` |
| `language_drift_diagnostics/contextual_run_language.csv` | Context-aware, run-level language detections and correctness. | `language_correctness_heatmap`; also refreshes crosslingual correctness for `language_vs_robustness_corr` |
| `language_drift_diagnostics/contextual_turn_position.csv` | Language correctness and drift by turn position. | `language_drift_by_turn_position` |
| `language_drift_diagnostics/contextual_tool_mix_summary.csv` | Language use in mixed-language tool runs. | `tool_mix_agent_language_use` |

`language_drift_summary.py` and `language_drift_diagnostics.py` both read
`data/seatau/experiments.csv` and the referenced simulation `results.json`
files. By default, system and user-simulator failures are excluded from the
diagnostic summaries. Pass `--include-system-errors` when an audit needs those
rows.

### Error-review tables

| Path | Contents | Plot consumers |
|---|---|---|
| `error_tag_rates_raw.csv` | Review-pipeline export with per-cell outcome counts and packed critical/benign counts for each error tag. | Input to `seatau.analysis.error_tag_rates`; no plot reads it directly. |
| `error_tag_rates.csv` | Tidy long-format review data with one row per setting, language, domain, role, category, and severity. | `error_breakdown_by_setting_role`, `avg_error_tags_occ_per_100_turns`, `avg_error_tags_occ_agent` |

`error_tag_rates_raw.csv` is supplied by the review pipeline. The repository
has no command that produces this raw export.

`error_tag_rates.csv` uses two denominators:

- `total_sims` is the denominator for `category=outcome` rows. The
  `critical`, `benign`, and `correct` values are per-simulation outcome
  shares.
- `turns` is the denominator for error-tag rows. The tag figures report
  average error occurrences per 100 turns, not the percentage of turns with an
  error. One turn can contain multiple tagged occurrences.

The tidy table is built from `error_tag_rates_raw.csv` and
`experiment_language_summary.csv`. The review export covers `gpt-5-mini`
agent runs. Mixed `L2 Tool` Mix-2 through Mix-5 rows are excluded because the
run-level summary has no matching turn totals for those language labels.

`error_breakdown.csv` is a superseded table. The plotting code does not read
it; use `error_tag_rates.csv`.

### Failure-mode tables

| Path | Contents | Plot consumers |
|---|---|---|
| `failure_mode/all_trial_outcomes.csv` | One row per simulation trial with behavioral outcome flags and a `primary_label`. | Input to `specific_failure_mode_share` |
| `failure_mode/specific_failure_rates.csv` | Generated failure counts and shares at overall, scenario, scenario-domain, and scenario-domain-model-language levels. | Intermediate table generated by `specific_failure_mode_share` |
| `failure_mode/specific_failure_rates_top.md` | Top 80 detailed failure-rate rows from the generated table. | Human-readable audit output |

The repository has no analysis command that regenerates
`failure_mode/all_trial_outcomes.csv`. Treat it as a supplied input artifact.
The `specific_failure_mode_share` plot filters it to usable behavioral trials
and failed or partial trials, then writes the two derived files above.

`language_drift_by_group.csv` is also present at the top level, but no analysis
or registered plot command writes or reads it. Treat it as a legacy snapshot
rather than a source for new figures.

## Generate figures

The `plot` console command is registered by `src/seatau/plot/cli.py`.
`src/seatau/plot/registry.py` is the source of truth for the figure stems.
Each command writes `figs/<stem>.pdf` and `figs/<stem>.png` by default.

To inspect the registry or regenerate every registered figure:

```bash
uv run plot list
uv run plot all
```

`plot all` runs each unique plot module once. The `language_drift` module
generates four figures, and the `error_tag_rates` module generates two. Any
registry entry backed by one of those modules therefore generates all figures
from that module, even when you name one stem. Use the module-specific command
when you want all outputs from a shared module:

```bash
uv run python -m seatau.plot.language_drift
uv run python -m seatau.plot.error_tag_rates
```

For a standalone figure, run one figure stem with:

```bash
uv run plot <figure-stem>
```

Pass module-specific options after the stem, such as
`--output-dir`, `--formats`, `--csv`, `--analysis-dir`, `--summary-dir`, or
`--diagnostics-dir`. For example:

```bash
uv run plot perf_by_language --formats png
uv run plot language_correctness_heatmap \
  --analysis-dir data/analyses/language_drift_diagnostics
```

`plot all` needs every prerequisite input, including the supplied failure-mode
and error-review artifacts.

### Figure and input map

| Figure stem | Default input | Output |
|---|---|---|
| `language_degradation` | `data/seatau/experiments.csv` | `figs/language_degradation.{pdf,png}` |
| `metric_correlation_matrix` | `data/seatau/experiments.csv` | `figs/metric_correlation_matrix.{pdf,png}` |
| `perf_tool_mix` | `data/seatau/experiments.csv` | `figs/perf_tool_mix.{pdf,png}` |
| `perf_by_language` | `data/analyses/perf_by_language.csv` | `figs/perf_by_language.{pdf,png}` |
| `en_vs_l2_perf` | `data/analyses/en_vs_l2_perf.csv` | `figs/en_vs_l2_perf.{pdf,png}` |
| `error_breakdown_by_setting_role` | `data/analyses/error_tag_rates.csv` outcome rows | `figs/error_breakdown_by_setting_role.{pdf,png}` |
| `avg_error_tags_occ_per_100_turns` | `data/analyses/error_tag_rates.csv` tag rows | `figs/avg_error_tags_occ_per_100_turns.{pdf,png}` |
| `avg_error_tags_occ_agent` | `data/analyses/error_tag_rates.csv` tag rows | `figs/avg_error_tags_occ_agent.{pdf,png}` |
| `specific_failure_mode_share` | `data/analyses/failure_mode/all_trial_outcomes.csv` | `figs/specific_failure_mode_share.{pdf,png}` |
| `language_correctness_heatmap` | `data/analyses/language_drift_diagnostics/contextual_run_language.csv` | `figs/language_correctness_heatmap.{pdf,png}` |
| `agent_english_share_boxplots` | `data/analyses/language_drift_summary/agent_language_drift_by_task.csv` | `figs/agent_english_share_boxplots.{pdf,png}` |
| `agent_english_share_by_model_heatmap` | `data/analyses/language_drift_summary/agent_language_drift_by_task.csv` | `figs/agent_english_share_by_model_heatmap.{pdf,png}` |
| `tool_mix_agent_language_use` | `data/analyses/language_drift_diagnostics/contextual_tool_mix_summary.csv` | `figs/tool_mix_agent_language_use.{pdf,png}` |
| `language_drift_by_turn_position` | `data/analyses/language_drift_diagnostics/contextual_turn_position.csv` | `figs/language_drift_by_turn_position.{pdf,png}` |
| `language_vs_robustness_corr` | `data/analyses/experiment_language_summary.csv`, plus contextual run diagnostics when available | `figs/language_vs_robustness_corr.{pdf,png}` |

The files `figs/domain_viewer.*`, `figs/overview.*`, and `figs/traj.*` are not
registered with the `plot` CLI. `plot list` and `plot all` do not regenerate
them.
