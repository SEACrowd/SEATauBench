# Failure Mode Analysis for Translated SEA-Tau Runs

Date: 2026-05-20

This note summarizes trajectory-level failure modes for suspiciously low translated experiment runs, with emphasis on tool-call and language-related errors. It complements the per-run live notes and the analysis template in `experiments/YYYYMMDD-experiment-and-analysis-template.md`.

## Artifacts

- `src/seatau/analysis/failure_modes.py`: reusable agent failure-mode classifier.
- `src/seatau/analysis/user_reliability.py`: reusable user-simulator reliability classifier for `experiments/errors.csv`.
- `experiments/failure_modes.csv`: 8,058 per-simulation rows from 31 tracker-backed runs with available `results.json`.
- `experiments/failure_modes_low_metric.csv`: 4,848 per-simulation rows from low-metric runs found through `experiments/experiments.csv`.
- `experiments/failure_modes_done.csv`: 7,272 per-simulation rows from 28 tracker rows marked `DONE`.
- `experiments/failure_modes_done_low_metric.csv`: 4,404 per-simulation rows from `DONE` rows with any `pass_hat_* < 30`.
- `experiments/errors.csv`: consolidated user-simulator reliability summary by domain/language/agent.
- `experiments/errors_done.csv`: DONE-only user-simulator reliability summary by domain/language/agent.
- `experiments/failure_mode_tables/low_metric/`: regenerated tables by domain, language, agent, and combinations for low-metric runs.
- `experiments/failure_mode_tables/all_tracked/`: regenerated tables by domain, language, agent, and combinations for all tracker-backed runs.
- `experiments/failure_mode_tables/done/`: regenerated tables for `progress=DONE`.
- `experiments/failure_mode_tables/done_low_metric/`: regenerated tables for `progress=DONE` and low-pass metrics.
- `experiments/failure_mode_tables/report/`: report-facing CSVs with task-denominator rates used in the main findings below.

## Classifier

Run:

```bash
uv run analyze-failure-modes data/simulations/<run_dir> --output experiments/failure_modes.csv
```

Regenerate the updateable tables from the tracker:

```bash
# All runs with available simulation_source/results.json
uv run analyze-failure-modes \
  --experiments-csv experiments/experiments.csv \
  --output experiments/failure_modes.csv \
  --summary-dir experiments/failure_mode_tables/all_tracked

# Suspicious low-pass runs only
uv run analyze-failure-modes \
  --experiments-csv experiments/experiments.csv \
  --max-pass-hat 30 \
  --output experiments/failure_modes_low_metric.csv \
  --summary-dir experiments/failure_mode_tables/low_metric

# DONE runs only
uv run analyze-failure-modes \
  --experiments-csv experiments/experiments.csv \
  --progress DONE \
  --output experiments/failure_modes_done.csv \
  --summary-dir experiments/failure_mode_tables/done

# DONE low-pass runs only
uv run analyze-failure-modes \
  --experiments-csv experiments/experiments.csv \
  --progress DONE \
  --max-pass-hat 30 \
  --output experiments/failure_modes_done_low_metric.csv \
  --summary-dir experiments/failure_mode_tables/done_low_metric

# User-simulator reliability / experiments/errors.csv
uv run analyze-user-reliability \
  --experiments-csv experiments/experiments.csv \
  --failure-modes-csv experiments/failure_modes.csv \
  --output experiments/errors.csv

# DONE user-simulator reliability
uv run analyze-user-reliability \
  --experiments-csv experiments/experiments.csv \
  --progress DONE \
  --failure-modes-csv experiments/failure_modes_done.csv \
  --output experiments/errors_done.csv

# Report-facing CSV tables used by this markdown
uv run analyze-report-tables \
  --failure-modes-csv experiments/failure_modes.csv \
  --failure-summary-dir experiments/failure_mode_tables/all_tracked \
  --user-errors-csv experiments/errors.csv \
  --output-dir experiments/failure_mode_tables/report
```

The summary directory contains:

- `failure_modes_by_domain.csv`
- `failure_modes_by_language.csv`
- `failure_modes_by_agent.csv`
- `failure_modes_by_domain_language.csv`
- `failure_modes_by_domain_agent.csv`
- `failure_modes_by_language_agent.csv`
- `failure_modes_by_domain_language_agent.csv`
- `failure_modes_by_run.csv`
- `failure_modes_by_group_long.csv`

Primary categories are mutually exclusive:

- `credential_or_identifier_hallucination`: repeated failing lookup using fake or placeholder credentials such as `user@example.com`, `1234567890`, `0123456789`, `0912345678`, empty values, or equivalent.
- `tool_error_loop`: same tool and same arguments repeatedly fail, but not due to a classified placeholder lookup.
- `translated_identifier_lookup_failure`: translated/non-ASCII identifier values are passed into DB lookup tools that expect canonical identifiers.
- `missing_required_write`: expected write action is absent after reads or conversation.
- `wrong_write_arguments_or_state`: write tool is called, but with wrong arguments or in an invalid state.
- `missing_user_device_instruction`: telecom user-side diagnostic/fix action is required but not executed/instructed.
- `premature_refusal_or_policy_misread`: agent retrieves relevant information but refuses or transfers when the task appears feasible.
- `wrong_read_arguments`: read tool is called, but arguments do not match the expected read.
- `non_action_assertion_failure`: action checks pass or are absent, but non-action assertions fail.
- `dialogue_or_action_loop`: `too_many_errors` without a repeated same-tool error signature.
- `non_agent_infrastructure`: infrastructure/provider termination or missing reward.
- `success`: reward is 1.0.

Secondary flags are non-exclusive and capture cross-cutting signals: `tool_errors`, `assistant_multi_tool_call`, `language_drift`, `refusal_or_policy_language`, `translated_identifier_lookup_failure`, `placeholder_lookup`, `missing_user_device_instruction`, and read/write check failures.

## Manual Exploration

Manual inspection covered 220 representative agent-failure tasks across five runs:

| Domain | Language | Run | Sampled tasks |
|---|---:|---|---:|
| airline | tl | `2026-05-18-19-16-28_translated_airline_trial-3_tl_qwen3.6-35b-a3b_Qwen3-235B-A22B-Instruct-2507-FP8` | 20 |
| retail | th | `2026-05-18-05-04-57_translated_retail_trial-3_th_qwen3.6-35b-a3b_Qwen3-235B-A22B-Instruct-2507-FP8` | 50 |
| retail | zh | `2026-05-18-12-11-13_translated_retail_trial-3_zh_qwen3.6-35b-a3b_Qwen3-235B-A22B-Instruct-2507-FP8` | 50 |
| telecom | id | `2026-05-18-21-51-53_translated_telecom_trial-3_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8` | 50 |
| telecom | vi | `2026-05-19-00-49-19_translated_telecom_trial-3_vi_qwen3.6-35b-a3b_Qwen3-235B-A22B-Instruct-2507-FP8` | 50 |

The manual sample intentionally excluded non-agent infrastructure failures when possible and sampled additional tasks when provider/infra errors obscured behavior.

## Validation

Validation used tasks not in the manual sample:

- Holdout scope: 3,672 low-metric simulations after excluding manually sampled run directories.
- Holdout agent-failure rows: 2,783.
- Unique held-out run-task pairs: 1,240.
- Stratified validation examples: 192 rows, up to three examples per `(domain, language, agent, primary_failure_mode)`.
- Invariant checks: 0 failures.

Invariant checks included:

- Reward `1.0` must map to `success`.
- `success` must have reward `1.0`.
- `translated_identifier_lookup_failure` primary must include the corresponding secondary flag.
- `missing_user_device_instruction` primary must include the corresponding secondary flag.
- `credential_or_identifier_hallucination` primary must include a placeholder identifier or placeholder lookup flag.

The first held-out pass found one over-broad heuristic: repeated write-tool errors could be mislabeled as credential hallucination if any unrelated placeholder appeared elsewhere in the trace. The classifier was tightened so `credential_or_identifier_hallucination` only fires when the repeated failing call is itself a lookup tool using a placeholder/fake identifier.

## DONE-Only Rerun

Rerun date: 2026-05-20.

Scope: 28 rows in `experiments/experiments.csv` with `progress=DONE`. All 28 had a local `simulation_source/results.json`.

Coverage limitation: DONE currently covers all five languages overall, but telecom has only two DONE runs (`telecom/id/azure/gpt-5-mini` and `telecom/th/azure/gpt-5-mini`). DONE-only telecom findings should not be generalized to Tagalog, Vietnamese, or Chinese telecom until those runs are DONE.

### DONE Script Results

`experiments/failure_modes_done.csv` has 7,272 simulations:

- Success: 2,847 simulations, 39.1%.
- Non-agent infrastructure: 63 simulations, 0.9%.
- Agent failures: 4,362 simulations, 60.0%.

Primary DONE agent-failure modes:

| Primary failure mode | Count | Share of agent failures |
|---|---:|---:|
| `missing_required_write` | 1,354 | 31.0% |
| `credential_or_identifier_hallucination` | 769 | 17.6% |
| `tool_error_loop` | 706 | 16.2% |
| `wrong_write_arguments_or_state` | 544 | 12.5% |
| `premature_refusal_or_policy_misread` | 368 | 8.4% |
| `missing_user_device_instruction` | 234 | 5.4% |
| `non_action_assertion_failure` | 133 | 3.0% |
| `dialogue_or_action_loop` | 131 | 3.0% |
| `translated_identifier_lookup_failure` | 72 | 1.7% |
| `max_steps_or_dialogue_loop` | 25 | 0.6% |
| `language_drift` | 11 | 0.3% |

DONE by domain:

| Domain | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| airline | 1,800 | 52.5% | 0.6% | 46.9% | `missing_required_write` 364, `wrong_write_arguments_or_state` 147, `tool_error_loop` 81 |
| retail | 4,788 | 36.2% | 1.1% | 62.7% | `missing_required_write` 963, `tool_error_loop` 615, `credential_or_identifier_hallucination` 542 |
| telecom | 684 | 24.9% | 0.0% | 75.1% | `missing_user_device_instruction` 234, `credential_or_identifier_hallucination` 227, `missing_required_write` 27 |

DONE by language:

| Language | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| id | 2,010 | 39.2% | 0.0% | 60.8% | `missing_required_write` 430, `tool_error_loop` 301, `credential_or_identifier_hallucination` 154 |
| th | 1,326 | 30.6% | 0.0% | 69.4% | `missing_required_write` 241, `credential_or_identifier_hallucination` 179, `missing_user_device_instruction` 143 |
| tl | 1,134 | 33.4% | 1.1% | 65.5% | `missing_required_write` 261, `credential_or_identifier_hallucination` 213, `tool_error_loop` 91 |
| vi | 1,326 | 42.0% | 3.7% | 54.3% | `missing_required_write` 200, `credential_or_identifier_hallucination` 139, `tool_error_loop` 136 |
| zh | 1,476 | 48.6% | 0.1% | 51.2% | `missing_required_write` 222, `tool_error_loop` 140, `wrong_write_arguments_or_state` 135 |

DONE by agent:

| Agent | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| `Qwen3-235B-A22B-Instruct-2507-FP8` | 342 | 1.8% | 0.0% | 98.2% | `tool_error_loop` 186, `missing_required_write` 94, `credential_or_identifier_hallucination` 38 |
| `azure/gpt-5-mini` | 3,144 | 46.8% | 0.0% | 53.2% | `missing_required_write` 386, `wrong_write_arguments_or_state` 345, `missing_user_device_instruction` 234 |
| `azure/kimi-k2.5` | 1,668 | 34.5% | 2.0% | 63.4% | `missing_required_write` 537, `tool_error_loop` 131, `premature_refusal_or_policy_misread` 101 |
| `openrouter/qwen/qwen3.6-35b-a3b` | 2,118 | 37.4% | 1.4% | 61.2% | `credential_or_identifier_hallucination` 436, `missing_required_write` 337, `tool_error_loop` 255 |

DONE user-simulator reliability (`experiments/errors_done.csv`):

- Critical user-simulator errors: 71 simulations.
- Benign user-simulator errors: 348 simulations.
- Total user reliability errors: 419 simulations.
- Highest issue rates: airline/tl/gpt-5-mini 22.0%, retail/tl/gpt-5-mini 19.0%, retail/id/gpt-5-mini 15.5%, airline/id/gpt-5-mini 12.7%, airline/tl/kimi-k2.5 12.7%.

### DONE Manual Exploration

Manual inspection sampled 120 DONE trajectories from the full DONE set, plus 68 trajectories from the current newly relevant Chinese Kimi sources and 89 user-simulator reliability examples:

| Domain | Sampled trajectories | Languages represented | Notes |
|---|---:|---|---|
| airline | 20 + 28 focused Chinese Kimi | `id`, `th`, `tl`, `zh`, plus qwen/gpt/kimi where available | Focused on low-pass agent failures, excluding non-agent infrastructure where possible. |
| retail | 50 | `id`, `th`, `tl`, `vi`, `zh` | Stratified across the dominant failure modes and all DONE agents. |
| retail Chinese Kimi | 40 focused | `zh` | Added after `retail/zh/azure/kimi-k2.5` appeared in the DONE set. |
| telecom | 50 | `id` | Manual telecom sample remains Indonesian gpt-5-mini; Thai telecom is newly included in script aggregates but was not part of the earlier manual telecom sample. |
| user simulator reliability | 89 | all DONE languages with observed reliability errors | Stratified across critical/benign severity and drift reasons. |

Manual findings:

- Airline failures are mostly tool-loop and policy/action-boundary mistakes. The newly included `airline/zh/azure/kimi-k2.5` run is a severe outlier: only 4/150 successes. Manual traces show repeated `list_all_airports`, `calculate`, `get_flight_status`, and `transfer_to_human_agents` calls, often until `max_steps`, `too_many_errors`, or timeout. It also repeatedly passes Chinese instruction placeholders such as `请提供您的用户ID` into `get_user_details`, producing translated identifier lookup failures.
- Airline non-Kimi failures still show the earlier pattern: premature transfer on feasible itinerary changes, partial itinerary/baggage/passenger writes, and wrong flight/payment arguments. In Tagalog Kimi, raw tool-call markup and translated cabin strings such as `klase ekonomiya` appear in tool arguments or assistant messages; these are classified as language drift or write-argument failures depending on whether the wrong state reaches a tool.
- Retail failures are dominated by auth and write completion. The worst DONE case remains the user-LLM-as-agent retail/id run: it repeatedly calls lookup tools with placeholders (`user@example.com`, `John Doe`, `12345`) and then stalls in `too_many_errors`. For gpt-5-mini and Kimi, many traces authenticate correctly and read the order/product state, but stop after summarizing options or transfer instead of calling `exchange_delivered_order_items`, `modify_pending_order_items`, `cancel_pending_order`, or equivalent final write.
- The newly included `retail/zh/azure/kimi-k2.5` run is materially better than the airline Chinese Kimi run: 207/342 successes. Its failures are mainly final-write omissions after correct reads, wrong write arguments, and policy/refusal issues. Examples include presenting a correct return/exchange confirmation and then stopping without `return_delivered_order_items` or `exchange_delivered_order_items`, translating cancellation reasons into Chinese (`不再需要`) before retrying English `no longer needed`, and modifying only item options while omitting a required address change.
- Telecom DONE failures are mainly action-boundary failures. The agent often performs user-device actions as tools (`toggle_airplane_mode`, `set_network_mode_preference`, `reboot_device`, `grant_app_permission`) instead of instructing the user, so reward checks mark `requestor=user` actions missing. A second cluster fabricates phone identifiers when the user does not provide a canonical number (`UNPROVIDED`, empty string, `+33`, `please_provide_your_phone_number`) and loops on `get_customer_by_phone`. Some traces eventually gather enough state but transfer after troubleshooting instead of completing backend writes such as `refuel_data`, `enable_roaming`, `resume_line`, or billing/payment flow.
- User simulator reliability in DONE runs is not the main blocker. Most user-sim issues are benign language-drift artifacts: short confirmations, IDs, payment tokens, email addresses, JSON-like slot dumps, or detected-language confusion on nearby languages. The task-critical reliability failures are `###OUT-OF-SCOPE###`, concentrated in airline scenarios and a smaller set of retail scenarios.
- Cross-language pattern in DONE rows changed after the tracker update: Thai now has the highest DONE agent-failure rate (69.4%) after the full telecom/th gpt-5-mini run was included, Tagalog remains high (65.5%), and Indonesian remains difficult because it includes telecom/id and the user-LLM-as-agent retail/id run.

## Main Findings: Error Rates Over Analyzed Tasks

Denominator convention: unless a column explicitly says "share of agent failures", percentages below are calculated as `count / total_simulations` for that slice. This makes domain, language, and agent comparisons comparable even when success rates differ. These tables are generated by `uv run analyze-report-tables`; the CSV sources are in `experiments/failure_mode_tables/report/`, with the wider full-slice tables in `experiments/failure_mode_tables/all_tracked/`.

Across all 8,058 analyzed translated simulations, the agent failed in 5,027 tasks (62.4%), succeeded in 2,925 tasks (36.3%), and hit non-agent infrastructure/provider failures in 106 tasks (1.3%).

### Aggregate Translated Experiment

CSV: `experiments/failure_mode_tables/report/agent_failure_modes_aggregate.csv`

| Primary failure mode | Count | Rate over all analyzed tasks | Share of agent failures |
|---|---:|---:|---:|
| `missing_required_write` | 1,469 | 18.2% | 29.2% |
| `credential_or_identifier_hallucination` | 1,167 | 14.5% | 23.2% |
| `tool_error_loop` | 749 | 9.3% | 14.9% |
| `wrong_write_arguments_or_state` | 558 | 6.9% | 11.1% |
| `premature_refusal_or_policy_misread` | 385 | 4.8% | 7.7% |
| `missing_user_device_instruction` | 234 | 2.9% | 4.7% |
| `dialogue_or_action_loop` | 169 | 2.1% | 3.4% |
| `non_action_assertion_failure` | 137 | 1.7% | 2.7% |
| `translated_identifier_lookup_failure` | 105 | 1.3% | 2.1% |
| `max_steps_or_dialogue_loop` | 25 | 0.3% | 0.5% |
| `wrong_read_arguments` | 13 | 0.2% | 0.3% |
| `language_drift` | 11 | 0.1% | 0.2% |
| `unclassified_failure` | 5 | 0.1% | 0.1% |

### By Domain

CSV: `experiments/failure_mode_tables/report/agent_failure_rates_by_domain.csv`

| Domain | Tasks analyzed | Success | Infra/non-agent | Agent errors | Top agent modes, rate over tasks |
|---|---:|---:|---:|---:|---|
| airline | 1,902 | 946 (49.7%) | 11 (0.6%) | 945 (49.7%) | `missing_write` 420 (22.1%), `wrong_write` 147 (7.7%), `dialogue_loop` 116 (6.1%) |
| retail | 5,130 | 1,809 (35.3%) | 95 (1.9%) | 3,226 (62.9%) | `missing_write` 1,022 (19.9%), `tool_loop` 653 (12.7%), `cred_halluc` 598 (11.7%) |
| telecom | 1,026 | 170 (16.6%) | 0 (0.0%) | 856 (83.4%) | `cred_halluc` 569 (55.5%), `missing_user_device` 234 (22.8%), `missing_write` 27 (2.6%) |

### By Language

CSV: `experiments/failure_mode_tables/report/agent_failure_rates_by_language.csv`

| Language | Tasks analyzed | Success | Infra/non-agent | Agent errors | Top agent modes, rate over tasks |
|---|---:|---:|---:|---:|---|
| id | 2,010 | 787 (39.2%) | 0 (0.0%) | 1,223 (60.8%) | `missing_write` 430 (21.4%), `tool_loop` 301 (15.0%), `cred_halluc` 154 (7.7%) |
| th | 1,770 | 484 (27.3%) | 43 (2.4%) | 1,243 (70.2%) | `missing_write` 356 (20.1%), `cred_halluc` 235 (13.3%), `missing_user_device` 143 (8.1%) |
| tl | 1,476 | 379 (25.7%) | 12 (0.8%) | 1,085 (73.5%) | `cred_halluc` 555 (37.6%), `missing_write` 261 (17.7%), `tool_loop` 91 (6.2%) |
| vi | 1,326 | 557 (42.0%) | 49 (3.7%) | 720 (54.3%) | `missing_write` 200 (15.1%), `cred_halluc` 139 (10.5%), `tool_loop` 136 (10.3%) |
| zh | 1,476 | 718 (48.6%) | 2 (0.1%) | 756 (51.2%) | `missing_write` 222 (15.0%), `tool_loop` 140 (9.5%), `wrong_write` 135 (9.1%) |

### By Agent

CSV: `experiments/failure_mode_tables/report/agent_failure_rates_by_agent.csv`

| Agent | Tasks analyzed | Success | Infra/non-agent | Agent errors | Top agent modes, rate over tasks |
|---|---:|---:|---:|---:|---|
| `Qwen3-235B-A22B-Instruct-2507-FP8` | 342 | 6 (1.8%) | 0 (0.0%) | 336 (98.2%) | `tool_loop` 186 (54.4%), `missing_write` 94 (27.5%), `cred_halluc` 38 (11.1%) |
| `azure/gpt-5-mini` | 3,486 | 1,472 (42.2%) | 0 (0.0%) | 2,014 (57.8%) | `cred_halluc` 569 (16.3%), `missing_write` 386 (11.1%), `wrong_write` 345 (9.9%) |
| `azure/kimi-k2.5` | 1,770 | 577 (32.6%) | 34 (1.9%) | 1,159 (65.5%) | `missing_write` 593 (33.5%), `tool_loop` 136 (7.7%), `dialogue_loop` 114 (6.4%) |
| `openrouter/qwen/qwen3.6-35b-a3b` | 2,460 | 870 (35.4%) | 72 (2.9%) | 1,518 (61.7%) | `cred_halluc` 492 (20.0%), `missing_write` 396 (16.1%), `tool_loop` 293 (11.9%) |

### By Domain × Language

CSV: `experiments/failure_mode_tables/report/agent_failure_rates_by_domain_language.csv`

| Domain / language | Tasks analyzed | Success | Infra/non-agent | Agent errors | Top agent modes, rate over tasks |
|---|---:|---:|---:|---:|---|
| airline / id | 300 | 199 (66.3%) | 0 (0.0%) | 101 (33.7%) | `missing_write` 37 (12.3%), `wrong_write` 33 (11.0%), `policy_refusal` 21 (7.0%) |
| airline / th | 402 | 172 (42.8%) | 0 (0.0%) | 230 (57.2%) | `missing_write` 112 (27.9%), `dialogue_loop` 47 (11.7%), `wrong_write` 24 (6.0%) |
| airline / tl | 450 | 212 (47.1%) | 6 (1.3%) | 232 (51.6%) | `missing_write` 138 (30.7%), `wrong_write` 23 (5.1%), `dialogue_loop` 20 (4.4%) |
| airline / vi | 300 | 185 (61.7%) | 5 (1.7%) | 110 (36.7%) | `wrong_write` 36 (12.0%), `missing_write` 33 (11.0%), `policy_refusal` 23 (7.7%) |
| airline / zh | 450 | 178 (39.6%) | 0 (0.0%) | 272 (60.4%) | `missing_write` 100 (22.2%), `tool_loop` 64 (14.2%), `dialogue_loop` 49 (10.9%) |
| retail / id | 1,368 | 418 (30.6%) | 0 (0.0%) | 950 (69.4%) | `missing_write` 376 (27.5%), `tool_loop` 293 (21.4%), `cred_halluc` 104 (7.6%) |
| retail / th | 1,026 | 312 (30.4%) | 43 (4.2%) | 671 (65.4%) | `missing_write` 234 (22.8%), `policy_refusal` 118 (11.5%), `translated_lookup` 101 (9.8%) |
| retail / tl | 684 | 167 (24.4%) | 6 (0.9%) | 511 (74.7%) | `cred_halluc` 213 (31.1%), `missing_write` 123 (18.0%), `tool_loop` 82 (12.0%) |
| retail / vi | 1,026 | 372 (36.3%) | 44 (4.3%) | 610 (59.5%) | `missing_write` 167 (16.3%), `cred_halluc` 139 (13.5%), `tool_loop` 136 (13.3%) |
| retail / zh | 1,026 | 540 (52.6%) | 2 (0.2%) | 484 (47.2%) | `missing_write` 122 (11.9%), `wrong_write` 104 (10.1%), `cred_halluc` 84 (8.2%) |
| telecom / id | 342 | 170 (49.7%) | 0 (0.0%) | 172 (50.3%) | `missing_user_device` 91 (26.6%), `cred_halluc` 50 (14.6%), `missing_write` 17 (5.0%) |
| telecom / th | 342 | 0 (0.0%) | 0 (0.0%) | 342 (100.0%) | `cred_halluc` 177 (51.8%), `missing_user_device` 143 (41.8%), `missing_write` 10 (2.9%) |
| telecom / tl | 342 | 0 (0.0%) | 0 (0.0%) | 342 (100.0%) | `cred_halluc` 342 (100.0%) |

### By Domain × Language × Agent

The full domain × language × agent table is `experiments/failure_mode_tables/report/agent_failure_rates_by_domain_language_agent.csv`. The compact highest-error table below is generated as `experiments/failure_mode_tables/report/agent_failure_highest_domain_language_agent.csv`.

| Domain / language / agent | Tasks analyzed | Agent errors | Top agent modes, rate over tasks |
|---|---:|---:|---|
| telecom / th / `azure/gpt-5-mini` | 342 | 342 (100.0%) | `cred_halluc` 177 (51.8%), `missing_user_device` 143 (41.8%), `missing_write` 10 (2.9%) |
| telecom / tl / `azure/gpt-5-mini` | 342 | 342 (100.0%) | `cred_halluc` 342 (100.0%) |
| airline / th / `azure/kimi-k2.5` | 102 | 101 (99.0%) | `missing_write` 56 (54.9%), `dialogue_loop` 38 (37.3%), `tool_loop` 5 (4.9%) |
| retail / id / `Qwen3-235B-A22B-Instruct-2507-FP8` | 342 | 336 (98.2%) | `tool_loop` 186 (54.4%), `missing_write` 94 (27.5%), `cred_halluc` 38 (11.1%) |
| retail / tl / `openrouter/qwen/qwen3.6-35b-a3b` | 342 | 336 (98.2%) | `cred_halluc` 213 (62.3%), `missing_write` 57 (16.7%), `tool_loop` 49 (14.3%) |
| airline / zh / `azure/kimi-k2.5` | 150 | 146 (97.3%) | `missing_write` 58 (38.7%), `dialogue_loop` 44 (29.3%), `tool_loop` 40 (26.7%) |
| retail / vi / `openrouter/qwen/qwen3.6-35b-a3b` | 342 | 330 (96.5%) | `cred_halluc` 139 (40.6%), `tool_loop` 106 (31.0%), `missing_write` 67 (19.6%) |

The low-metric diagnostic cuts remain in `experiments/failure_mode_tables/low_metric/`.

## User Simulator Reliability

`experiments/errors.csv` now consolidates user-simulator reliability by domain/language/agent and is generated by `analyze-user-reliability`, not `analyze-failure-modes`. Manual reliability exploration sampled 30 trajectories across airline, retail, and telecom, covering all five languages (`id`, `th`, `tl`, `vi`, `zh`); validation then sampled 90 unseen per-simulation rows across severity, domain, language, and agent.

- Critical user error: `###OUT-OF-SCOPE###`, because this is an irrecoverable simulator exit that can preclude task completion.
- Benign user error: language drift, including mild drift (`0.8 <= score < 1.0`), substantial slot/JSON-like drift, and short identifier or detector artifacts.
- `###TRANSFER###` and `###STOP###` are reported but not counted as user errors because they are normally terminal markers caused by agent transfer or task completion.

Current totals across 31 domain/language/agent rows and 8,058 analyzed simulations:

- Critical user errors: 79 simulations, 1.0% of analyzed tasks.
- Benign user errors: 354 simulations, 4.4% of analyzed tasks.
- Total user reliability errors: 433 simulations, 5.4% of analyzed tasks.

User simulator reliability by domain:

CSV: `experiments/failure_mode_tables/report/user_reliability_by_domain.csv`

| Domain | Tasks | Critical | Benign | Total user errors | User language drift sims | Out-of-scope |
|---|---:|---:|---:|---:|---:|---:|
| airline | 1,902 | 56 (2.9%) | 83 (4.4%) | 139 (7.3%) | 86 (4.5%) | 56 (2.9%) |
| retail | 5,130 | 23 (0.4%) | 248 (4.8%) | 271 (5.3%) | 252 (4.9%) | 23 (0.4%) |
| telecom | 1,026 | 0 (0.0%) | 23 (2.2%) | 23 (2.2%) | 23 (2.2%) | 0 (0.0%) |

User simulator reliability by language:

CSV: `experiments/failure_mode_tables/report/user_reliability_by_language.csv`

| Language | Tasks | Critical | Benign | Total user errors | User language drift sims | Out-of-scope |
|---|---:|---:|---:|---:|---:|---:|
| id | 2,010 | 10 (0.5%) | 136 (6.8%) | 146 (7.3%) | 137 (6.8%) | 10 (0.5%) |
| th | 1,770 | 27 (1.5%) | 20 (1.1%) | 47 (2.7%) | 20 (1.1%) | 27 (1.5%) |
| tl | 1,476 | 27 (1.8%) | 108 (7.3%) | 135 (9.1%) | 113 (7.7%) | 27 (1.8%) |
| vi | 1,326 | 7 (0.5%) | 29 (2.2%) | 36 (2.7%) | 29 (2.2%) | 7 (0.5%) |
| zh | 1,476 | 8 (0.5%) | 61 (4.1%) | 69 (4.7%) | 62 (4.2%) | 8 (0.5%) |

Highest domain/language user-simulator reliability issue rates:

Full CSV: `experiments/failure_mode_tables/report/user_reliability_by_domain_language.csv`

| Domain / language | Tasks | Critical | Benign | Total user errors | User language drift sims | Out-of-scope |
|---|---:|---:|---:|---:|---:|---:|
| airline / tl | 450 | 23 (5.1%) | 47 (10.4%) | 70 (15.6%) | 49 (10.9%) | 23 (5.1%) |
| airline / id | 300 | 9 (3.0%) | 19 (6.3%) | 28 (9.3%) | 20 (6.7%) | 9 (3.0%) |
| retail / tl | 684 | 4 (0.6%) | 61 (8.9%) | 65 (9.5%) | 64 (9.4%) | 4 (0.6%) |
| retail / id | 1,368 | 1 (0.1%) | 94 (6.9%) | 95 (6.9%) | 94 (6.9%) | 1 (0.1%) |
| telecom / id | 342 | 0 (0.0%) | 23 (6.7%) | 23 (6.7%) | 23 (6.7%) | 0 (0.0%) |

Highest user reliability issue rates:

| Domain | Language | Agent | Total user error rate | User language drift | Out-of-scope | Transfer markers |
|---|---|---|---:|---|---:|---:|
| airline | tl | `azure/gpt-5-mini` | 22.0% | 27/150 sims; 36/526 turns | 8 | 85 |
| retail | tl | `azure/gpt-5-mini` | 19.0% | 64/342 sims; 83/1786 turns | 4 | 70 |
| retail | id | `azure/gpt-5-mini` | 15.5% | 53/342 sims; 60/1557 turns | 0 | 99 |
| airline | id | `azure/gpt-5-mini` | 12.7% | 17/150 sims; 22/492 turns | 3 | 84 |
| airline | tl | `azure/kimi-k2.5` | 12.7% | 14/150 sims; 14/246 turns | 5 | 51 |
| airline | tl | `openrouter/qwen/qwen3.6-35b-a3b` | 12.0% | 8/150 sims; 11/530 turns | 10 | 71 |

Interpretation: the user simulator is broadly usable, but Tagalog and Indonesian runs have enough user-language drift to track explicitly. Most drift is not task-critical after validation; it is usually short confirmations, IDs/emails/payment tokens, JSON-like slot dumps, or detector confusion on related languages. Transfer markers are frequent, but mostly reflect agent behavior rather than independent user-simulator unreliability.

## Updateable Tables

The table files in `experiments/failure_mode_tables/low_metric/` answer the main slicing questions directly.

### By domain

| Domain | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| airline | 402 | 9.0% | 0.0% | 91.0% | `missing_required_write` 194, `dialogue_or_action_loop` 102, `tool_error_loop` 49 |
| retail | 3,762 | 26.9% | 2.5% | 70.6% | `missing_required_write` 875, `credential_or_identifier_hallucination` 598, `tool_error_loop` 560 |
| telecom | 684 | 24.9% | 0.0% | 75.1% | `missing_user_device_instruction` 234, `credential_or_identifier_hallucination` 227, `missing_required_write` 27 |

CSV: `experiments/failure_mode_tables/low_metric/failure_modes_by_domain.csv`

### By language

| Language | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| id | 1,368 | 29.5% | 0.0% | 70.5% | `missing_required_write` 347, `tool_error_loop` 270, `credential_or_identifier_hallucination` 154 |
| th | 1,470 | 21.3% | 2.9% | 75.8% | `missing_required_write` 300, `credential_or_identifier_hallucination` 235, `missing_user_device_instruction` 143 |
| tl | 834 | 23.7% | 0.7% | 75.5% | `credential_or_identifier_hallucination` 213, `missing_required_write` 203, `tool_error_loop` 86 |
| vi | 684 | 25.1% | 6.4% | 68.4% | `credential_or_identifier_hallucination` 139, `missing_required_write` 131, `tool_error_loop` 120 |
| zh | 492 | 27.0% | 0.0% | 73.0% | `missing_required_write` 115, `credential_or_identifier_hallucination` 84, `tool_error_loop` 70 |

CSV: `experiments/failure_mode_tables/low_metric/failure_modes_by_language.csv`

### By agent

| Agent LLM | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| `Qwen3-235B-A22B-Instruct-2507-FP8` | 342 | 1.8% | 0.0% | 98.2% | `tool_error_loop` 186, `missing_required_write` 94, `credential_or_identifier_hallucination` 38 |
| `azure/gpt-5-mini` | 1,368 | 32.7% | 0.0% | 67.3% | `missing_user_device_instruction` 234, `credential_or_identifier_hallucination` 227, `missing_required_write` 148 |
| `azure/kimi-k2.5` | 1,428 | 25.9% | 2.2% | 71.8% | `missing_required_write` 553, `dialogue_or_action_loop` 114, `tool_error_loop` 112 |
| `openrouter/qwen/qwen3.6-35b-a3b` | 1,710 | 23.1% | 3.6% | 73.3% | `credential_or_identifier_hallucination` 492, `missing_required_write` 301, `tool_error_loop` 257 |

CSV: `experiments/failure_mode_tables/low_metric/failure_modes_by_agent.csv`

### Combined tables

Use these when a single-axis table hides the interaction:

- Domain × language × agent: `experiments/failure_mode_tables/low_metric/failure_modes_by_domain_language_agent.csv`
- Domain × language: `experiments/failure_mode_tables/low_metric/failure_modes_by_domain_language.csv`
- Domain × agent: `experiments/failure_mode_tables/low_metric/failure_modes_by_domain_agent.csv`
- Language × agent: `experiments/failure_mode_tables/low_metric/failure_modes_by_language_agent.csv`
- Long-form plotting table: `experiments/failure_mode_tables/low_metric/failure_modes_by_group_long.csv`

## Domain Results

### Telecom

Telecom failures are dominated by user-device action-boundary errors and identity lookup failures.

Among 514 telecom agent failures in the low-metric set:

- `missing_user_device_instruction`: 234, 45.5%.
- `credential_or_identifier_hallucination`: 227, 44.2%.
- `missing_required_write`: 27, 5.3%.
- `tool_error_loop`: 10, 1.9%.

Main pattern: the agent often performs phone-side remediation as assistant tools instead of instructing the user, or starts by fabricating a phone number before the user provides account identifiers. In the current low-metric set this is concentrated in Indonesian, Thai, and Tagalog gpt-5-mini telecom runs.

Concrete examples from held-out validation:

- Indonesian telecom gpt-5-mini: often identifies the customer correctly but fails to complete the required user-side phone actions or assistant-side account writes such as roaming enablement or data refuel.
- Thai telecom gpt-5-mini: often cannot ground the customer identity and then falls into missing user-device instructions or credential hallucination, leaving the task unrecoverable.
- Tagalog telecom gpt-5-mini: current tracker-backed run is all credential hallucination in the classifier, dominated by placeholder lookup loops.

Interpretation: telecom exposes two coupled weaknesses. First, identity resolution is brittle when the opening user message does not supply canonical credentials. Second, the translated telecom policy requires separating assistant tools from user-device actions, and agents frequently blur that boundary.

### Retail

Retail failures are more mixed and more task-composition-heavy.

Among 2,656 retail agent failures in the low-metric set:

- `missing_required_write`: 875, 32.9%.
- `credential_or_identifier_hallucination`: 598, 22.5%.
- `tool_error_loop`: 560, 21.1%.
- `wrong_write_arguments_or_state`: 217, 8.2%.
- `premature_refusal_or_policy_misread`: 195, 7.3%.
- `translated_identifier_lookup_failure`: 101, 3.8%.

Main patterns:

- The agent retrieves user/order/product details but stops before return, exchange, cancel, or payment-splitting writes.
- The agent chooses wrong item IDs or wrong order IDs in multi-order tasks.
- Thai name lookup is a clear language/tool boundary failure: agents pass Thai-script names such as `เมย์ เดวิส` into `find_user_id_by_name_zip`, then either fail or retry with approximations.
- Placeholder identity loops occur when the user lacks email/order details and the agent uses `user@example.com`, empty strings, or guessed identifiers instead of asking targeted follow-up questions.

Interpretation: retail is not only a language problem. The strongest retail failure mode is multi-step execution: agents often gather enough context but fail to commit correct state-changing actions.

### Airline

Airline has three low-metric runs in the current consolidated low-metric set, all Kimi: Thai, Tagalog, and Chinese. This slice is useful for diagnosing Kimi airline behavior but should not be generalized to all airline agents.

Among 366 airline agent failures in the low-metric set:

- `missing_required_write`: 194, 53.0%.
- `dialogue_or_action_loop`: 102, 27.9%.
- `tool_error_loop`: 49, 13.4%.
- `language_drift`: 11, 3.0%.

Main patterns:

- Agent retrieves user/reservation details but does not complete the required booking, cancellation, baggage, passenger, or flight update.
- Chinese Kimi airline frequently loops over `list_all_airports`, `calculate`, `get_flight_status`, or `transfer_to_human_agents` until `max_steps`, `too_many_errors`, or timeout.
- Some Tagalog airline tasks hit language drift or dialogue/action loops after partially correct reservation reads.

Interpretation: airline failures are mostly planning/policy failures after successful reads, not raw language failures.

## Language Results

Agent-failure rows by language in the low-metric set:

| Language | Agent failures | Dominant modes |
|---|---:|---|
| id | 965 | `missing_required_write` 36.0%, `tool_error_loop` 28.0%, `credential_or_identifier_hallucination` 16.0% |
| th | 1,114 | `missing_required_write` 26.9%, `credential_or_identifier_hallucination` 21.1%, `missing_user_device_instruction` 12.8% |
| tl | 630 | `credential_or_identifier_hallucination` 33.8%, `missing_required_write` 32.2%, `tool_error_loop` 13.7% |
| vi | 468 | `credential_or_identifier_hallucination` 29.7%, `missing_required_write` 28.0%, `tool_error_loop` 25.6% |
| zh | 359 | `missing_required_write` 32.0%, `credential_or_identifier_hallucination` 23.4%, `tool_error_loop` 19.5% |

Language drift is measurable but usually secondary rather than primary. It appears as a secondary flag in 254 of 4,848 low-metric rows (5.2%). The stronger language-linked failure is not ordinary response-language drift; it is tool/schema language mismatch, especially translated names or localized field values fed into canonical DB tools.

## Research Story

The evidence supports three main stories:

1. Tool grounding fails before reasoning in telecom. Agents often cannot establish identity robustly in translated telecom tasks. Once the first lookup fails, many trajectories collapse into repeated lookup calls rather than asking for a usable credential or continuing with user-side diagnostics.
2. Tool/schema translation mismatch is a distinct failure mode. Thai retail shows the clearest instance: natural-language names are translated while DB lookup keys remain romanized/canonical. This is different from generic language drift.
3. Many failures are post-read execution failures. In retail and airline, agents often read the correct records but fail to perform the required write, write to the wrong target, or prematurely refuse. These are agentic planning and policy-application failures more than comprehension failures.

The evidence for broad cultural drift is weaker than the evidence for language-tool boundary failures. Some user personas and localized politeness markers affect dialogue length and follow-up behavior, but the dominant quantified errors are tool grounding, identifier handling, and write execution.

## Caveats

- The classifier is heuristic, not a semantic judge. It should guide inspection and aggregate diagnosis, not replace trajectory review.
- `credential_or_identifier_hallucination` is intentionally conservative after validation: it now requires a repeated failing lookup with placeholder/fake identifiers.
- `non_agent_infrastructure` is common in some suspicious rows. Retail/vi Qwen and telecom/th gpt-5-mini are not reliable evidence about agent behavior because most rows terminate before meaningful task execution.
- `language_drift` uses stored language correctness where available; response-language drift may be undercounted in runs without stored scores.

## Recommended Next Analysis

1. Add task-family tags to the failure CSV: `identity`, `return/exchange`, `booking/update`, `mobile_data`, `mms`, `service_issue`.
2. For telecom, separately quantify first actionable turn: asks for credential, fabricates credential, or begins device diagnostics.
3. For retail, separate read-correct/write-skipped from write-attempted/wrong-target by product/order/item ID.
4. For Thai and Chinese, quantify canonicalization failures: non-ASCII names, translated enum values, localized reason strings, and translated cabin/mode values.
5. Add a small labeled validation file with human labels for 100 examples so future heuristic changes can be regression-tested.

## 2026-05-22 Translation-Pipeline Audit Addendum

This addendum cross-checks the failure analysis against the actual translation
runtime and the translated telecom artifacts. The full implementation note is in
`src/seatau/translation/pipeline-implementation-notes.md`.

Key findings:

- Telecom is structurally different from airline and retail because the agent
  can call 30 user-device tools in solo mode, and all 30 currently return
  English free-form strings.
- In the completed `telecom/id` `azure/gpt-5-mini` run, 2,183 of 8,917 tool
  messages (24.5%) contained English telecom user-tool strings such as
  `Status Bar:`, `Airplane Mode:`, `SIM Card Status:`, or `Speed test failed:`.
- The completed `telecom/th`, `telecom/tl`, and `telecom/vi` `azure/gpt-5-mini`
  runs mostly fail before reaching user-device diagnostics. Their zero English
  user-tool counts are therefore not evidence that the surface is clean.
- Tool error messages bypass response localization when `response.error` is
  true. This matters for telecom: `th`, `tl`, and `vi` are dominated by repeated
  English lookup errors after the agent calls customer lookup tools with empty
  or placeholder phone numbers.
- Schema localized-value collisions were found only in telecom Thai and Chinese:
  `Active` and `active` collapse to one localized form in each language. This is
  likely a secondary evaluation/analysis ambiguity, not the main cause of the
  current zero-pass telecom runs.

Recommendation: treat the existing telecom `azure/gpt-5-mini` runs as pilot
diagnostics, redesign telecom user tools to return structured payloads or stable
message codes, localize structured errors, and then rerun telecom only. Airline
and retail do not need reruns for this issue.
