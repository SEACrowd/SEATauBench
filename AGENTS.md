# SEA-Tau Experiments

Our big goals is to run all domains, all languages, for `translated` experiment.

1. Determine the next steps: Check `experiments/experiments.csv` (60 rows: 3 domains x 4 models x 5 languages) for experiment tracking, and also `data/simulations/` for partial experiments. Prioritize resuming partial experiments. But if it has too many errors, skip and restart cleaner.
2. Set up relevant script by following the guide below. Take note of the saved folder.
3. Monitor the progress every 15-20 minutes, autonomoulsy fix any errors that arise. Particularly, make sure `localhost:8000` is alive, has job, to run the default user-llm. Do NOT count `litellm.ContentPolicyViolationError` (Azure content filter) as error, continue.
   - If the port fails and you cannot resurrect it quickly, start `scripts/lanta_vllm_watchdog.sh` from the repo root and leave it running as the fallback keeper. It polls the model API, reopens the SSH tunnel, and resubmits the SLURM job if needed.
4. Update the canonical aggregate live note `experiments/translated_{agent_llm}.md` (e.g. `translated_kimi-k2.5.md`, `translated_gpt-5-mini.md`) with details for completed domains & languages. These files already exist for all 4 agent LLMs — update them in place. Do this by exploring output trajectories in the saved folder (`results.json`) or reading live log traces. **Run the analysis scripts (see below) and paste their output into the relevant sections.** For cross-model failure patterns, update `experiments/failure-mode-analysis.md`.

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

## Error & Debugging

1. Find the corresponding experiment and simulation_source in `experiments/experiments.csv` or `experiments/experiments_all.csv`
2. Find `data/simulations/<simulation_source>` or `logs/<simulation_source>`
