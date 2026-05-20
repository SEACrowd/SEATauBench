# Failure Mode Analysis for Translated SEA-Tau Runs

Date: 2026-05-20

This note summarizes trajectory-level failure modes for suspiciously low translated experiment runs, with emphasis on tool-call and language-related errors. It complements the per-run live notes and the analysis template in `experiments/YYYYMMDD-experiment-and-analysis-template.md`.

## Artifacts

- `src/seatau/analysis/failure_modes.py`: reusable agent failure-mode classifier.
- `src/seatau/analysis/user_reliability.py`: reusable user-simulator reliability classifier for `experiments/errors.csv`.
- `experiments/failure_modes.csv`: 9,098 per-simulation rows from 34 tracker-backed runs with available `results.json`.
- `experiments/failure_modes_low_metric.csv`: 5,419 per-simulation rows from 16 low-metric runs found through `experiments/experiments.csv`.
- `experiments/failure_modes_done.csv`: 6,780 per-simulation rows from 26 tracker rows marked `DONE`.
- `experiments/failure_modes_done_low_metric.csv`: 4,254 per-simulation rows from `DONE` rows with any `pass_hat_* < 30`.
- `experiments/errors.csv`: consolidated user-simulator reliability summary by domain/language/agent.
- `experiments/errors_done.csv`: DONE-only user-simulator reliability summary by domain/language/agent.
- `experiments/failure_mode_tables/low_metric/`: regenerated tables by domain, language, agent, and combinations for low-metric runs.
- `experiments/failure_mode_tables/all_tracked/`: regenerated tables by domain, language, agent, and combinations for all tracker-backed runs.
- `experiments/failure_mode_tables/done/`: regenerated tables for `progress=DONE`.
- `experiments/failure_mode_tables/done_low_metric/`: regenerated tables for `progress=DONE` and low-pass metrics.

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

- Holdout scope: 4,338 low-metric simulations after excluding manual sample run-task pairs.
- Holdout agent-failure rows: 2,597.
- Unique held-out run-task pairs: 1,446.
- Stratified validation examples: 207 rows, up to three examples per `(domain, language, agent, primary_failure_mode)`.
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

Scope: 26 rows in `experiments/experiments.csv` with `progress=DONE`. All 26 had a local `simulation_source/results.json`.

Coverage limitation: DONE currently covers all five languages, but telecom has only one DONE run (`telecom/id/azure/gpt-5-mini`). DONE-only telecom findings should not be generalized to Thai, Tagalog, Vietnamese, or Chinese until those runs are DONE.

### DONE Script Results

`experiments/failure_modes_done.csv` has 6,780 simulations:

- Success: 2,648 simulations, 39.1%.
- Non-agent infrastructure: 61 simulations, 0.9%.
- Agent failures: 4,071 simulations, 60.0%.

Primary DONE agent-failure modes:

| Primary failure mode | Count | Share of agent failures |
|---|---:|---:|
| `missing_required_write` | 1,518 | 37.3% |
| `tool_error_loop` | 661 | 16.2% |
| `credential_or_identifier_hallucination` | 612 | 15.0% |
| `wrong_write_arguments_or_state` | 510 | 12.5% |
| `premature_refusal_or_policy_misread` | 343 | 8.4% |
| `non_action_assertion_failure` | 123 | 3.0% |
| `dialogue_or_action_loop` | 93 | 2.3% |
| `missing_user_device_instruction` | 91 | 2.2% |
| `translated_identifier_lookup_failure` | 71 | 1.7% |
| `language_drift` | 18 | 0.4% |

DONE by domain:

| Domain | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| airline | 1,650 | 57.0% | 0.7% | 42.3% | `missing_required_write` 306, `wrong_write_arguments_or_state` 147, `premature_refusal_or_policy_misread` 77 |
| retail | 4,788 | 32.1% | 1.0% | 66.9% | `missing_required_write` 1,195, `tool_error_loop` 612, `credential_or_identifier_hallucination` 562 |
| telecom | 342 | 49.7% | 0.0% | 50.3% | `missing_user_device_instruction` 91, `credential_or_identifier_hallucination` 50, `missing_required_write` 17 |

DONE by language:

| Language | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| id | 2,010 | 39.2% | 0.0% | 60.8% | `missing_required_write` 430, `tool_error_loop` 301, `credential_or_identifier_hallucination` 154 |
| th | 984 | 41.3% | 0.0% | 58.7% | `missing_required_write` 231, `premature_refusal_or_policy_misread` 113, `wrong_write_arguments_or_state` 83 |
| tl | 1,476 | 26.5% | 0.8% | 72.7% | `missing_required_write` 533, `credential_or_identifier_hallucination` 233, `tool_error_loop` 112 |
| vi | 1,326 | 42.0% | 3.7% | 54.3% | `missing_required_write` 200, `credential_or_identifier_hallucination` 139, `tool_error_loop` 136 |
| zh | 984 | 51.5% | 0.0% | 48.5% | `missing_required_write` 124, `wrong_write_arguments_or_state` 101, `credential_or_identifier_hallucination` 84 |

DONE by agent:

| Agent | Simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| `Qwen3-235B-A22B-Instruct-2507-FP8` | 342 | 1.8% | 0.0% | 98.2% | `tool_error_loop` 186, `missing_required_write` 94, `credential_or_identifier_hallucination` 38 |
| `azure/gpt-5-mini` | 2,802 | 52.5% | 0.0% | 47.5% | `missing_required_write` 376, `wrong_write_arguments_or_state` 345, `premature_refusal_or_policy_misread` 198 |
| `azure/kimi-k2.5` | 1,518 | 24.8% | 2.1% | 73.1% | `missing_required_write` 711, `credential_or_identifier_hallucination` 88, `tool_error_loop` 88 |
| `openrouter/qwen/qwen3.6-35b-a3b` | 2,118 | 37.4% | 1.4% | 61.2% | `credential_or_identifier_hallucination` 436, `missing_required_write` 337, `tool_error_loop` 255 |

DONE user-simulator reliability (`experiments/errors_done.csv`):

- Critical user-simulator errors: 70 simulations.
- Benign user-simulator errors: 378 simulations.
- Total user reliability errors: 448 simulations.
- Highest issue rates: airline/tl/gpt-5-mini 22.0%, retail/tl/gpt-5-mini 19.0%, retail/id/gpt-5-mini 15.5%, retail/tl/kimi-k2.5 13.7%, airline/id/gpt-5-mini 12.7%.

### DONE Manual Exploration

Manual inspection sampled 120 DONE trajectories after script rerun:

| Domain | Sampled trajectories | Languages represented | Notes |
|---|---:|---|---|
| airline | 20 | `id`, `th`, `tl`, plus qwen/gpt/kimi where available | Focused on low-pass agent failures, excluding non-agent infrastructure where possible. |
| retail | 50 | `id`, `th`, `tl`, `vi`, `zh` | Stratified across the dominant failure modes and all DONE agents. |
| telecom | 50 | `id` only | Only DONE telecom run is Indonesian gpt-5-mini. |

Manual findings:

- Airline failures are mostly policy/action-boundary mistakes rather than lookup failures. Common patterns were premature transfer on feasible itinerary changes, writing a partial itinerary/baggage update but missing one required write, and using valid-looking but wrong flight/payment arguments. In Tagalog Kimi runs, raw tool-call markup and translated cabin strings such as `klase ekonomiya` appeared in tool arguments or assistant messages; these failures are classified as language drift or write-argument failures depending on whether the wrong state reached a tool.
- Retail failures are dominated by auth and write completion. The worst DONE case is the user-LLM-as-agent retail/id run: it repeatedly calls lookup tools with placeholders (`user@example.com`, `John Doe`, `12345`) and then stalls in `too_many_errors`. For gpt-5-mini and Kimi, many traces authenticate correctly and read the order/product state, but stop after summarizing options or transfer instead of calling `exchange_delivered_order_items`, `modify_pending_order_items`, `cancel_pending_order`, or equivalent final write. Wrong-write examples include invalid cancellation reasons, wrong item IDs, multiple exchanges split incorrectly, or calling exchange on non-delivered orders.
- Telecom DONE failures are mainly action-boundary failures. The agent often performs user-device actions as tools (`toggle_airplane_mode`, `set_network_mode_preference`, `reboot_device`, `grant_app_permission`) instead of instructing the user, so reward checks mark `requestor=user` actions missing. A second cluster fabricates phone identifiers when the user does not provide a canonical number (`UNPROVIDED`, empty string, `+33`, `please_provide_your_phone_number`) and loops on `get_customer_by_phone`. Some traces eventually gather enough state but transfer after troubleshooting instead of completing backend writes such as `refuel_data`, `enable_roaming`, `resume_line`, or billing/payment flow.
- User simulator reliability in DONE runs is not the main blocker. Most user-sim issues are benign language-drift artifacts: short confirmations, IDs, payment tokens, email addresses, or JSON-like slot dumps. The task-critical reliability failures are `###OUT-OF-SCOPE###`, concentrated in airline/Tagalog and a smaller set of retail/Chinese/Thai scenarios.
- Cross-language pattern in DONE rows: Tagalog has the highest DONE agent-failure rate (72.7%) and high user-language drift; Indonesian has many failures because it includes the difficult telecom DONE run and the user-LLM-as-agent retail/id run; Chinese has the strongest DONE success rate (51.5%) among languages currently represented.

## Aggregate Results

Primary counts on `failure_modes_low_metric.csv`, excluding `success` and `non_agent_infrastructure`:

| Primary failure mode | Count | Share of agent failures |
|---|---:|---:|
| `missing_required_write` | 1,055 | 29.9% |
| `credential_or_identifier_hallucination` | 857 | 24.3% |
| `tool_error_loop` | 811 | 23.0% |
| `wrong_write_arguments_or_state` | 219 | 6.2% |
| `premature_refusal_or_policy_misread` | 195 | 5.5% |
| `missing_user_device_instruction` | 172 | 4.9% |
| `translated_identifier_lookup_failure` | 102 | 2.9% |
| `dialogue_or_action_loop` | 46 | 1.3% |
| `non_action_assertion_failure` | 34 | 1.0% |
| `language_drift` | 18 | 0.5% |

Secondary flags across all 5,419 low-metric rows:

| Secondary flag | Count | Share of all rows |
|---|---:|---:|
| `tool_errors` | 2,445 | 45.1% |
| `refusal_or_policy_language` | 1,396 | 25.8% |
| `missing_user_device_instruction` | 1,270 | 23.4% |
| `write_check_failed` | 1,241 | 22.9% |
| `assistant_multi_tool_call` | 1,094 | 20.2% |
| `placeholder_identifier` | 1,044 | 19.3% |
| `placeholder_lookup` | 971 | 17.9% |
| `repeated_tool_error_x10` | 945 | 17.4% |
| `read_check_failed` | 516 | 9.5% |
| `language_drift` | 400 | 7.4% |

The all-tracked aggregate, using all 34 available tracker-backed runs, shows a less extreme but consistent picture: among 5,073 agent-failure rows, the leading categories are `missing_required_write` (29.9%), `tool_error_loop` (22.4%), `credential_or_identifier_hallucination` (17.0%), and `wrong_write_arguments_or_state` (10.9%).

## User Simulator Reliability

`experiments/errors.csv` now consolidates user-simulator reliability by domain/language/agent and is generated by `analyze-user-reliability`, not `analyze-failure-modes`. Manual reliability exploration sampled 30 trajectories across airline, retail, and telecom, covering all five languages (`id`, `th`, `tl`, `vi`, `zh`); validation then sampled 90 unseen per-simulation rows across severity, domain, language, and agent.

- Critical user error: `###OUT-OF-SCOPE###`, because this is an irrecoverable simulator exit that can preclude task completion.
- Benign user error: language drift, including mild drift (`0.8 <= score < 1.0`), substantial slot/JSON-like drift, and short identifier or detector artifacts.
- `###TRANSFER###` and `###STOP###` are reported but not counted as user errors because they are normally terminal markers caused by agent transfer or task completion.

Current totals across 34 rows:

- Critical user errors: 79 simulations.
- Benign user errors: 403 simulations.
- Total user reliability errors: 482 simulations.

Highest user reliability issue rates:

| Domain | Language | Agent | Total user error rate | User language drift | Out-of-scope | Transfer markers |
|---|---|---|---:|---|---:|---:|
| airline | tl | `azure/gpt-5-mini` | 22.0% | 27/150 sims; 36/526 turns | 8 | 85 |
| retail | tl | `azure/gpt-5-mini` | 19.0% | 64/342 sims; 83/1786 turns | 4 | 70 |
| retail | id | `azure/gpt-5-mini` | 15.5% | 53/342 sims; 60/1557 turns | 0 | 99 |
| retail | tl | `azure/kimi-k2.5` | 13.7% | 47/342 sims; 47/602 turns | 0 | 83 |
| airline | id | `azure/gpt-5-mini` | 12.7% | 17/150 sims; 22/492 turns | 3 | 84 |

Interpretation: the user simulator is broadly usable, but Tagalog and Indonesian runs have enough user-language drift to track explicitly. Most drift is not task-critical after validation; it is usually short confirmations, IDs/emails/payment tokens, JSON-like slot dumps, or detector confusion on related languages. Transfer markers are frequent, but mostly reflect agent behavior rather than independent user-simulator unreliability.

## Updateable Tables

The table files in `experiments/failure_mode_tables/low_metric/` answer the main slicing questions directly.

### By domain

| Domain | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| airline | 150 | 20.7% | 0.7% | 78.7% | `missing_required_write` 79 |
| retail | 3,559 | 28.6% | 11.6% | 59.8% | `missing_required_write` 944, `credential_or_identifier_hallucination` 335, `tool_error_loop` 257 |
| telecom | 1,710 | 9.9% | 15.0% | 75.0% | `tool_error_loop` 550, `credential_or_identifier_hallucination` 522, `missing_user_device_instruction` 172 |

CSV: `experiments/failure_mode_tables/low_metric/failure_modes_by_domain.csv`

### By language

| Language | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| id | 1,368 | 29.0% | 0.4% | 70.6% | `tool_error_loop` 369, `missing_required_write` 258, `missing_user_device_instruction` 134 |
| th | 1,368 | 22.8% | 20.9% | 56.3% | `missing_required_write` 237, `credential_or_identifier_hallucination` 124, `translated_identifier_lookup_failure` 101 |
| tl | 973 | 21.6% | 0.2% | 78.2% | `missing_required_write` 427, `credential_or_identifier_hallucination` 127, `tool_error_loop` 75 |
| vi | 1,026 | 16.8% | 36.7% | 46.5% | `credential_or_identifier_hallucination` 283, `missing_required_write` 69 |
| zh | 684 | 18.9% | 0.1% | 81.0% | `tool_error_loop` 234, `credential_or_identifier_hallucination` 204 |

CSV: `experiments/failure_mode_tables/low_metric/failure_modes_by_language.csv`

### By agent

| Agent LLM | Total simulations | Success rate | Infrastructure rate | Agent failure rate | Dominant agent modes |
|---|---:|---:|---:|---:|---|
| `azure/gpt-5-mini` | 1,368 | 32.7% | 17.8% | 49.5% | `missing_required_write` 141, `missing_user_device_instruction` 119, `wrong_write_arguments_or_state` 102 |
| `azure/kimi-k2.5` | 1,176 | 17.4% | 0.1% | 82.5% | `missing_required_write` 646, `credential_or_identifier_hallucination` 88, `tool_error_loop` 74 |
| `openrouter/moonshotai/kimi-k2.5` | 342 | 50.3% | 9.4% | 40.4% | `missing_required_write` 64, `wrong_write_arguments_or_state` 26 |
| `openrouter/qwen/qwen3.6-35b-a3b` | 2,533 | 15.6% | 15.6% | 68.8% | `tool_error_loop` 659, `credential_or_identifier_hallucination` 653, `missing_required_write` 204 |

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

Telecom failures are dominated by lookup/tool loops.

Among 1,283 telecom agent failures in the low-metric set:

- `tool_error_loop`: 550, 42.9%.
- `credential_or_identifier_hallucination`: 522, 40.7%.
- `missing_user_device_instruction`: 172, 13.4%.

Main pattern: the agent often starts by fabricating a phone number or using a placeholder number before the user provides account identifiers. In Vietnamese and Chinese Qwen telecom runs, this commonly becomes ten repeated `get_customer_by_phone` failures and `too_many_errors`.

Concrete examples from held-out validation:

- Vietnamese telecom: repeated `get_customer_by_phone({"phone_number": "0912345678"})` or `0123456789`.
- Chinese telecom: repeated `get_customer_by_phone({"phone_number": "1234567890"})`.
- Indonesian telecom gpt-5-mini: often identifies the customer correctly but fails to complete the required user-side phone actions or assistant-side account writes such as roaming enablement or data refuel.

Interpretation: telecom exposes two coupled weaknesses. First, identity resolution is brittle when the opening user message does not supply canonical credentials. Second, the translated telecom policy requires separating assistant tools from user-device actions, and agents frequently blur that boundary.

### Retail

Retail failures are more mixed and more task-composition-heavy.

Among 1,721 retail agent failures in the low-metric set:

- `missing_required_write`: 662, 39.9%.
- `credential_or_identifier_hallucination`: 263, 15.3%.
- `tool_error_loop`: 227, 13.2%.
- `wrong_write_arguments_or_state`: 214, 12.4%.
- `premature_refusal_or_policy_misread`: 181, 10.5%.
- `translated_identifier_lookup_failure`: 101, 5.9%.

Main patterns:

- The agent retrieves user/order/product details but stops before return, exchange, cancel, or payment-splitting writes.
- The agent chooses wrong item IDs or wrong order IDs in multi-order tasks.
- Thai name lookup is a clear language/tool boundary failure: agents pass Thai-script names such as `เมย์ เดวิส` into `find_user_id_by_name_zip`, then either fail or retry with approximations.
- Placeholder identity loops occur when the user lacks email/order details and the agent uses `user@example.com`, empty strings, or guessed identifiers instead of asking targeted follow-up questions.

Interpretation: retail is not only a language problem. The strongest retail failure mode is multi-step execution: agents often gather enough context but fail to commit correct state-changing actions.

### Airline

Airline has only one low-metric run in the current consolidated low-metric set, so this slice should be treated as provisional.

Among 118 airline agent failures in the low-metric set:

- `missing_required_write`: 79, 66.9%.
- `dialogue_or_action_loop`: 20, 16.9%.
- `language_drift`: 11, 9.3%.
- `tool_error_loop`: 4, 3.4%.

Main patterns:

- Agent retrieves user/reservation details but does not complete the required booking, cancellation, baggage, passenger, or flight update.
- Agent sometimes refuses or transfers after reading a reservation even when a search/update path is expected.
- Some Thai airline tasks hit dialogue/action loops after partially correct reservation reads.

Interpretation: airline failures are mostly planning/policy failures after successful reads, not raw language failures.

## Language Results

Agent-failure rows by language in the low-metric set:

| Language | Agent failures | Dominant modes |
|---|---:|---|
| id | 966 | `tool_error_loop` 38.2%, `missing_required_write` 26.7%, `missing_user_device_instruction` 13.9% |
| th | 770 | `missing_required_write` 30.8%, `credential_or_identifier_hallucination` 16.1%, `translated_identifier_lookup_failure` 13.1% |
| tl | 356 | `missing_required_write` 40.7%, `wrong_write_arguments_or_state` 16.0%, `credential_or_identifier_hallucination` 15.4% |
| vi | 477 | `credential_or_identifier_hallucination` 59.3%, `missing_required_write` 14.5%, `tool_error_loop` 13.6% |
| zh | 554 | `tool_error_loop` 42.2%, `credential_or_identifier_hallucination` 36.8% |

Language drift is measurable but usually secondary rather than primary. It appears as a secondary flag in 227 of 5,001 low-metric rows (4.5%). The stronger language-linked failure is not ordinary response-language drift; it is tool/schema language mismatch, especially translated names or localized field values fed into canonical DB tools.

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
