# All Results Analysis

This analysis is built directly from every confident `simulation_source/results.json` in `experiments/experiments_all.csv`; it is not limited to the sampled deep-reading set.

## Outputs

- `failure_mode/all_trial_outcomes.csv`: one row per simulation trial with scalable first-pass labels. Source for the `specific_failure_mode_share` figure, which also writes `failure_mode/specific_failure_rates.csv` and `failure_mode/specific_failure_rates_top.md`.
- `all_task_language_summary.csv`: one row per task/language/experiment.
- `experiment_language_summary.csv`: run-level user/agent language correctness, non-target proportions, and drift turns.
- `language_drift_by_group.csv`: drift by scenario x domain x language x agent x role.
- `language_passhat_ranks.csv`: `experiments_all` plus pass_hat ranks by comparable language group.
- `metric_correlations_by_language.csv`: Pearson correlation/R-squared between
  language correctness and pass_hat/rho over experiment-summary rows
  (`scenario x domain x language x model`), with additional rows stratified by
  `summary_level` (`overall`, `scenario`, `domain`, and `scenario_domain`).
- `turn_language_evidence.csv`: per-turn language detections for audit.

## Counts

- Trial rows: 45636.
- Task/model rows: 3614.
- Cross-scenario rows with reward gap >= 0.5: 83.
- Model-specific task rows: 150.
- Generally difficult task rows: 232.

## Overall Failure Labels

successful_control:26528|wrong_write_action:8533|wrong_write_arguments_or_state:5475|wrong_read_arguments:1719|db_mismatch:1276|loop_or_recovery_failure:1016|missing_required_read:522|premature_final_or_incomplete_resolution:486

## Top Cross-Scenario Degradations

| domain | task_id | scenario | mean_task_reward | reward_gap_from_best_scenario | dominant_failure_labels |
|---|---|---|---|---|---|
| retail | 113 | 4-translated | 0.083333 | 0.916667 | wrong_write_arguments_or_state:34\|loop_or_recovery_failure:7\|successful_control:4\|wrong... |
| retail | 88 | 4-translated | 0.0 | 0.877193 | wrong_write_arguments_or_state:37\|wrong_write_action:8\|loop_or_recovery_failure:3 |
| retail | 78 | 4-translated | 0.020833 | 0.85636 | wrong_write_arguments_or_state:25\|wrong_write_action:14\|loop_or_recovery_failure:8\|succ... |
| telecom | [mms_issue]break_app_sms_permission\|data_mode_off[PERSONA:None] | 2-multilingual-tools | 0.074074 | 0.830688 | wrong_write_action:49\|successful_control:4\|wrong_write_arguments_or_state:1 |
| telecom | [mms_issue]bad_network_preference\|bad_wifi_calling\|break_app_sms_permission\|data_mode_o... | 2-multilingual-tools | 0.018519 | 0.814814 | wrong_write_action:39\|wrong_write_arguments_or_state:14\|successful_control:1 |
| retail | 90 | 4-translated | 0.0 | 0.807018 | wrong_write_arguments_or_state:34\|wrong_write_action:10\|loop_or_recovery_failure:4 |
| telecom | [mms_issue]bad_network_preference\|bad_wifi_calling\|break_app_sms_permission\|data_mode_o... | 2-multilingual-tools | 0.0 | 0.777778 | wrong_write_action:51\|wrong_write_arguments_or_state:3 |
| telecom | [mms_issue]airplane_mode_on\|bad_network_preference\|break_apn_mms_setting\|break_app_both... | 2-multilingual-tools | 0.240741 | 0.759259 | wrong_write_action:31\|successful_control:13\|wrong_write_arguments_or_state:10 |
| telecom | [mms_issue]break_apn_mms_setting\|data_mode_off\|data_usage_exceeded\|user_abroad_roaming_... | 4-translated | 0.261905 | 0.738095 | wrong_write_action:18\|successful_control:11\|wrong_write_arguments_or_state:8\|loop_or_re... |
| telecom | [mms_issue]airplane_mode_on\|bad_network_preference\|bad_wifi_calling\|break_apn_mms_setti... | 2-multilingual-tools | 0.166667 | 0.722222 | wrong_write_action:30\|wrong_write_arguments_or_state:14\|successful_control:9\|loop_or_re... |
| retail | 30 | 4-translated | 0.0625 | 0.715278 | wrong_read_arguments:15\|wrong_write_arguments_or_state:13\|loop_or_recovery_failure:7\|mi... |
| telecom | [mms_issue]break_apn_mms_setting\|data_mode_off\|data_usage_exceeded\|user_abroad_roaming_... | 2-multilingual-tools | 0.287037 | 0.712963 | wrong_write_action:21\|wrong_write_arguments_or_state:16\|successful_control:15\|db_mismat... |

## Lowest Language Pass@3 Buckets

| scenario | domain | language_scenario | mean_pass_hat_3 | mean_user_language_correctness | mean_agent_language_correctness |
|---|---|---|---|---|---|
| 4-translated | retail | thai | 0.123 | 0.994633 | 0.998847 |
| 4-translated | retail | filipino | 0.213333 | 0.940689 | 0.959162 |
| 4-translated | retail | indonesian | 0.24125 | 0.971051 | 0.967551 |
| 4-translated | retail | vietnamese | 0.25 | 0.988261 | 0.998976 |
| 4-translated | telecom | vietnamese | 0.2545 | 0.999346 | 0.912376 |
| 2-multilingual-tools | telecom | tool_mix_2 | 0.285 | 0.999428 | 0.991763 |
| 2-multilingual-tools | telecom | vietnamese | 0.285 | 0.999221 | 0.990982 |
| 2-multilingual-tools | telecom | tool_mix_5 | 0.2895 | 0.999721 | 0.992067 |
| 4-translated | telecom | thai | 0.289667 | 0.998842 | 0.93567 |
| 4-translated | retail | chinese | 0.294333 | 0.983573 | 0.990937 |
| 2-multilingual-tools | telecom | chinese | 0.298 | 0.999375 | 0.989599 |
| 2-multilingual-tools | telecom | tool_mix_4 | 0.298 | 0.99968 | 0.992653 |

## Language Drift Groups To Inspect

| scenario | domain | language_scenario | agent_family | role | mean_language_correctness | non_target_lang_proportion | mean_drift_turn |
|---|---|---|---|---|---|---|---|
| 3-crosslingual | retail | filipino | qwen3.6-35b-a3b | agent | 0.483936 | en_0.516 | 0.0 |
| 3-crosslingual | airline | filipino | qwen3.6-35b-a3b | agent | 0.521333 | en_0.479 | 0.0 |
| 3-crosslingual | airline | chinese | gpt-5-mini | agent | 0.596649 | en_0.402\|ja_0.001 | 0.0 |
| 4-translated | telecom | chinese | qwen3-235b | agent | 0.61609 | en_0.373\|ko_0.011 | 10.0 |
| 3-crosslingual | airline | filipino | gpt-5-mini | agent | 0.654172 | en_0.345\|es_0.001 | 0.0 |
| 3-crosslingual | airline | indonesian | gpt-5-mini | agent | 0.65586 | en_0.343\|lv_0.001 | 0.0 |
| 3-crosslingual | retail | filipino | kimi-k2.5 | agent | 0.685443 | en_0.314\|sco_0.000 | 0.0 |
| 3-crosslingual | airline | thai | gpt-5-mini | agent | 0.690981 | en_0.309 | 0.0 |
| 3-crosslingual | airline | filipino | kimi-k2.5 | agent | 0.699358 | en_0.301 | 0.0 |
| 4-translated | telecom | filipino | qwen3-235b | agent | 0.702271 | en_0.290\|ko_0.008\|si_0.000 | 28.0 |
| 3-crosslingual | airline | chinese | qwen3.6-35b-a3b | agent | 0.702467 | en_0.298 | 0.0 |
| 3-crosslingual | airline | vietnamese | gpt-5-mini | agent | 0.702564 | en_0.297 | 0.0 |

## Overall Language Correlations

These correlations are computed over experiment-summary rows: each observation is
one `scenario x domain x language x model` aggregate. The table below shows the
`summary_level=overall` slice; the CSV also includes scenario-, domain-, and
scenario-domain-stratified correlations. This is distinct from the
`metric_correlation_matrix` figure, which correlates language metric columns over
domain-model mean rows.

| language_metric | outcome_metric | n | pearson_r | r_squared |
|---|---|---|---|---|
| user_language_correctness | pass_hat_1 | 166 | -0.063058 | 0.003976 |
| user_language_correctness | pass_hat_2 | 166 | -0.045354 | 0.002057 |
| user_language_correctness | pass_hat_3 | 166 | -0.035292 | 0.001246 |
| user_language_correctness | rho_3 | 166 | -0.070607 | 0.004985 |
| agent_language_correctness | pass_hat_1 | 166 | -0.083627 | 0.006993 |
| agent_language_correctness | pass_hat_2 | 166 | -0.092271 | 0.008514 |
| agent_language_correctness | pass_hat_3 | 166 | -0.095841 | 0.009185 |
| agent_language_correctness | rho_3 | 166 | -0.058021 | 0.003366 |
