# 1. SEA-Tau Experiments

Our big goals is to run all domains, all languages, for `translated` experiment.

1. Determine the next steps: Check `experiments/experiments_trans.csv` (61 rows: 1 header, 3 domains x 4 models x 5 languages) for experiment tracking, and also `data/simulations/` for partial experiments. Prioritize resuming partial experiments. But if it has too many infrastructure errors, skip and restart cleaner.
2. Set up relevant script by following the guide below. Take note of the saved folder.
3. Monitor the progress every 15-20 minutes, autonomoulsy fix any errors that arise. Particularly, make sure `localhost:8000` is alive, has job, to run the default user-llm. Do NOT count `litellm.ContentPolicyViolationError` (Azure content filter) as error, continue.
   - If the port fails and you cannot resurrect it quickly, start `scripts/lanta_vllm_watchdog.sh` from the repo root and leave it running as the fallback keeper. It polls the model API, reopens the SSH tunnel, and resubmits the SLURM job if needed.

4. After obtaining all relevant output trajectories, write high-level metrics to `experiments/experiments.csv`. The columns needed are `progress,progress_notes,experiment,domain,language_or_scenario,agent_llm,simulation_source,pass_hat_1,pass_hat_2,pass_hat_3,read_action_count,read_acount_total,read_action_percent,write_action_count,write_acount_total,write_action_percent,db_match,language_correctness,total_simulations,total_tasks
`. `progress` column should be one of: TODO, DONE, PARTIAL, IN_PROGRESS, NEEDS_CHECK

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

## Write

`experiments/experiments_trans.csv` is the single source of truth for all 60 planned runs (5 languages × 3 domains × 4 agent LLMs). Check the `progress` column before starting any run.

IMPORTANT: Only experiments with num_trials=3, all tasks, and minimal errors count as DONE.

# 2. Translation Error Analysis

# 3. Trajectory Analysis

All of these following analysis scenarios should exclude tasks where
`termination_reason` is `infrastructure_error`. Also exclude insufficient
credits, connection failures, API errors, and user simulator errors from
behavioral analysis; those count as infrastructure/system errors, not task or
model failures.

## Deep Reading

Use `experiments/experiments_all.csv` as the index of analysis runs, but only
sample from rows with a confident `simulation_source`. Skip unidentified rows
for now. The analysis scope is all four scenarios:

- `1-english-only`
- `2-multilingual-tools`
- `3-crosslingual`
- `4-translated`

Sample 20 tasks per `(scenario, domain, agent_llm)`, distributed across
languages where applicable. Task selection should use distinct `task_id` values
across languages as much as possible, so the read set tests broad task coverage
rather than repeatedly reading the same task in each language.

Sampling should be failure-heavy but include controls:

- 70% failed, partial, or non-perfect tasks
- 30% successful control tasks

For each selected task, read all 3 trials when available. If a task has fewer
usable trials after exclusions, prioritize failed trials. Deep reading must
inspect user turns, agent turns, messages, reasoning if present, and tool calls.

`results.json` files can be too verbose for direct reading. Keep deep-reading
utility scripts under `experiments/deep_reading_new/` unless there is a strong
reason to put reusable project tooling elsewhere. The
condensed format should preserve the parts needed for audit:

- scenario, domain, language, agent model, task_id, trial
- reward and termination reason
- user messages
- assistant messages
- tool calls and tool results
- reward/action/db/language metadata when present

For outputs, write a Markdown memo first because the user will read that first.
The claims in the memo must be grounded in an appendable/auditable structured
artifact, such as CSV or JSONL, that Codex can later extend or correct.

Create a new failure taxonomy from the current trajectories. Existing artifacts
under `experiments/deep_reading/` may be referenced for inspiration, but do not
anchor the new taxonomy to stale labels because some old errors have already
been fixed.

Language should be treated as one possible failure cause, but likely not the
dominant explanation given high language metrics. Still track:

- whether language failure caused task failure
- language drift
- non-target-language mixing and which language appears
- extent of linguistic misunderstanding
- the conversation turn where linguistic drift or misunderstanding starts

Group and tell the analysis story by whichever dimensions are most explanatory:
domain, agent model, task difficulty, task length, task pattern, language, and
scenario. Prefer concrete transcript evidence over broad claims.

Before starting the reading pass, follow the operational checklist in
`experiments/deep_reading_new/deep_reading_todo.md`. It turns the task-analysis and
language-analysis questions below into concrete preprocessing, sampling,
trajectory-condensation, labeling, and output steps.

## Task Analysis

1. In a single (scenario, domain, agent_llm), what tasks consistently fail across 3 trials? Find out their common patterns
2. Aggregate insights from Question 1. Does the pattern hold if average out agent_llm? In other words, are tasks generally difficult for these near-frontier models, or are SOME task failures just model specific?
3. For each unique `task_id`, track task performance across all scenarios where
   confident sources exist. Which kinds of tasks fail in later multilingual or
   translated scenarios but succeed in earlier/comparable scenarios? What caused
   the performance degradation?

## Language Analysis

### Questions

- For each experiment, calculate the language correctness in user and agent turns (`user_language_correctness`, `agent_language_correctness`)
- Detect the language being used outside target language (L2), provide language code and proportion. Consider using the format `lang_proportion`, like `en_0.12`.
- Quantify the language drift by experiment: From which turn does the user and agent typically start to drift (`user_drift_turn`, `agent_drift_turn`)? Is it due to translated context proble (e.g., still contains English), genuine agentic failure, or glitch?
- In the same domain, rank `pass_hat_*` metrics by language in non-decreasing order (create `pass_hat_1_rank`, `pass_hat_2_rank`, `pass_hat_3_rank`). Does the agent perform worse in lower-resource language? How worse across number of trials?
- Does the above pattern hold across domains?

### Language Analysis Steps

1. Duplicate `experiments/experiments_all.csv`. Add extra columns for (`user_language_correctness`, `agent_language_correctness`), then fill them by calculate the language for user and agent turns

```bash
# User simulator language drift (requires uv run for fastText)
uv run analyze-user-language data/simulations/<run_dir>/results.json

# Agent language correctness — uses stored metric when present; add --recalculate to recompute
uv run analyze-agent-language data/simulations/<run_dir>/results.json
```

2. In the same domain, rank `pass_hat_*` metrics by language in non-decreasing order (create `pass_hat_1_rank`, `pass_hat_2_rank`, `pass_hat_3_rank`). Does the agent perform worse in lower-resource language? How worse across number of trials?
3. Quantify the language drift by scenario x domain x language x user/agent

4. How much of agent language correctness informs pass^3 and rho^3, for all experiments? Calculate correlation or R-squared.
