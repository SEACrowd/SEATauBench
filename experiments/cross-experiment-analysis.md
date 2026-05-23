# Cross-Experiment Trace Analysis

Date: 2026-05-22

## Scope

This analysis covers the three experiment families defined in
`src/seatau/experiments.yaml`:

- `baseline`: English baseline with original assets and no language components.
- `crosslingual`: English assets with L2 user/agent prompting and greeting.
- `translated`: translated assets, tools, policy, DB, tasks, and L2 prompting.

I excluded `mixed_tools`, `localized`, and `banking_knowledge` from the main
comparison because they are not part of the requested baseline -> crosslingual
-> translated comparison.

## Sources And Outputs

Raw source coverage:

- `data/simulations/1-english-baseline`
- `data/simulations/2-crosslingual`
- translated run folders directly under `data/simulations`
- 169 `results.json` files total
- 38,296 simulations in the corrected explicit-path deterministic pass

Important correction to the earlier report: before this pass,
`src/seatau/analysis/_common.py::resolve_paths()` only descended one directory
level, so passing bare `data/simulations` missed doubly nested English baseline
paths. I used the explicit path list below for the corrected outputs, and then
updated `resolve_paths()` to recurse through nested `results.json` files for
future runs.

```bash
fd 'results\.json$' data/simulations -t f | sort > /tmp/seatau_results_paths.txt
```

Corrected deterministic outputs:

- `experiments/analysis_logs/all_results_action_sequences.csv`
- `experiments/analysis_logs/all_results_failure_modes.csv`
- `experiments/analysis_logs/all_results_user_reliability.csv`
- `experiments/analysis_logs/all_results_user_reliability_details.csv`
- `experiments/analysis_logs/all_results_user_language.csv`
- `experiments/analysis_logs/all_results_agent_language.csv`
- `experiments/analysis_logs/all_results_failure_mode_tables/`
- `experiments/analysis_logs/all_results_report_tables/`
- `experiments/analysis_logs/cross_experiment_deterministic_summary.csv`

Manual exploration outputs:

- `experiments/analysis_logs/cross_experiment_manual_trace_sample_450.csv`
- `experiments/analysis_logs/cross_experiment_manual_hidden_issue_counts.csv`
- `experiments/deep-reading-100-trace-addendum.md`
- `experiments/analysis_logs/deep_reading_100_trace_selection.csv`
- `experiments/analysis_logs/deep_reading_100_turn_by_turn_worksheet.md`
- `experiments/analysis_logs/deep_reading_100_review_cards.md`

Manual sample design: 450 failure-oriented traces, balanced at 50 traces per
experiment/domain cell: baseline, crosslingual, translated x airline, retail,
telecom. For each sampled trace I extracted the user/agent turns, source path,
task/trial, failed action checks, tool sequence, tool errors, first/last
utterance snippets, and a hidden-issue label; I then manually inspected the
sample summaries and representative raw conversations by failure class.

Follow-up deep read: I selected 100 unique traces from the 450-trace sample for
turn-by-turn review, with 11 traces in each experiment/domain cell except
translated telecom with 12. The addendum in
`experiments/deep-reading-100-trace-addendum.md` records the audit files,
coverage, and findings from that pass.

## Aggregate Results

These rates are over all requested runs and agents in the local
`data/simulations` tree, with non-agent infrastructure separated from evaluated
agent failures.

| Experiment   |  Domain | Runs |  Sims | Success | Infra | Agent failure | Top failure modes                                                |
| ------------ | ------: | ---: | ----: | ------: | ----: | ------------: | ---------------------------------------------------------------- |
| baseline     | airline |    5 |   750 |   62.4% |  0.0% |         37.6% | wrong write/state, missing write, communication assertion        |
| baseline     |  retail |    5 | 1,710 |   62.5% |  0.0% |         37.5% | missing write, wrong write/state, premature refusal              |
| baseline     | telecom |    5 | 1,710 |   68.8% |  0.0% |         31.2% | missing device instruction, tool loop, missing write             |
| crosslingual | airline |   24 | 3,200 |   64.0% |  1.2% |         34.8% | wrong write/state, missing write, communication assertion        |
| crosslingual |  retail |   19 | 6,498 |   65.1% |  0.0% |         34.9% | wrong write/state, missing write, premature refusal              |
| crosslingual | telecom |   17 | 5,814 |   64.3% |  0.0% |         35.7% | missing device instruction, tool loop, missing write             |
| translated   | airline |   34 | 3,763 |   38.7% |  4.0% |         57.3% | missing write, dialogue loop, wrong write/state                  |
| translated   |  retail |   35 | 9,421 |   25.9% | 10.8% |         63.3% | missing write, fabricated identifier, tool loop                  |
| translated   | telecom |   12 | 4,614 |   25.1% | 44.8% |         30.0% | fabricated identifier, missing device instruction, missing write |

The main correction to the previous interpretation is that translated runs are
not just a weaker version of the crosslingual pattern. They introduce a distinct
failure regime: placeholder identifiers, repeated lookup errors, no-progress
partial runs, and translated-tool mismatch.

## Manual Findings

The 450-trace manual sample produced these dominant hidden issue labels:

| Hidden issue                                | Count |
| ------------------------------------------- | ----: |
| wrong write arguments or final state        |    82 |
| read context but skipped required write     |    82 |
| communication assertion failure             |    53 |
| premature refusal or policy misread         |    49 |
| telecom user-device instruction gap         |    45 |
| repeated tool error loop                    |    32 |
| placeholder or fabricated identifier loop   |    24 |
| missing required write                      |    23 |
| entity disambiguation or lookup miss        |    22 |
| dialogue loop or no tool progress           |    13 |
| language drift or code switching            |    10 |
| overcompensation for unrequested issue      |     7 |
| translated identifier passed to lookup tool |     6 |

By experiment, baseline and crosslingual failures are dominated by ordinary
task execution errors: skipped writes, wrong writes, policy misreads, and
communication assertions. Translated failures shift toward lookup and control
failures: fabricated identifiers, repeated tool errors, no-progress loops, and
device-instruction gaps.

## Evidence From Trace Reading

Each row below is grounded in the raw `results.json` plus the sampled trace CSV.

| Finding                                                                                               | Source trace                                                                                                                                                                                                                                                                                                       | Evidence                                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Baseline already fails complex multi-step airline writes.                                             | `data/simulations/1-english-baseline/20260506_204315_airline_llm_agent_Qwen3-235B-A22B-Instruct-2507-FP8_user_simulator_Qwen3-235B-A22B-Instruct-2507-FP8/20260506_204315_airline_llm_agent_Qwen3-235B-A22B-Instruct-2507-FP8_user_simulator_Qwen3-235B-A22B-Instruct-2507-FP8/results.json`, task `17`, trial `1` | The agent reads several reservations for a name/cabin/bag change but refuses the requested update after deciding the passenger name cannot be changed. The evaluator expected `update_reservation_flights` and `update_reservation_passengers`; both writes were missing. |
| Baseline airline has hidden overcompensation.                                                         | same Qwen baseline run, task `2`, trial `0`                                                                                                                                                                                                                                                                        | The user starts by trying to book SF -> NY and later complains about a delayed prior reservation. The agent issues a travel certificate even though the task says compensation should not be offered unless the user asks for it.                                         |
| Crosslingual often preserves aggregate success but adds entity grounding errors.                      | `data/simulations/2-crosslingual/20260508_194059_retail_llm_agent_Qwen3-235B-A22B-Instruct-2507-FP8_user_simulator_Qwen3-235B-A22B-Instruct-2507-FP8_crosslingual_thai/results.json`, task `92`, trial `1`                                                                                                         | The agent first calls `find_user_id_by_name_zip` with Thai-script first/last names, receives `User not found`, then recovers with romanized names but returns the wrong order item. This is a translated-identifier lookup failure plus wrong write target.               |
| Crosslingual retail lookup also fails when the agent drops part of a name.                            | `data/simulations/2-crosslingual/20260509_014748_retail_llm_agent_Qwen3-235B-A22B-Instruct-2507-FP8_user_simulator_Qwen3-235B-A22B-Instruct-2507-FP8_crosslingual_chinese/results.json`, task `67`, trial `2`                                                                                                      | The user asks about a recent order. The agent repeatedly searches with `first_name=Noah`, blank `last_name`, and several zips, then answers with an order total after failed expected name+zip lookups.                                                                   |
| Telecom is a separate axis of difficulty, not just a language problem.                                | `data/simulations/1-english-baseline/20260422_204705_telecom_llm_agent_gpt-5-mini_user_simulator_qwen3-235b-a22b-2507/20260422_204705_telecom_llm_agent_gpt-5-mini_user_simulator_qwen3-235b-a22b-2507/results.json`, task `[service_issue]airplane_mode_on                                                        | unseat_sim_card`, trial `2`                                                                                                                                                                                                                                               | The agent identifies the customer and transfers to a human, but the evaluator expected user-device actions `toggle_airplane_mode` and `reseat_sim_card`. This same missing-device-instruction family is the top telecom failure in baseline and crosslingual. |
| Translated retail introduces fabricated placeholder lookup loops.                                     | `data/simulations/2026-05-20-02-36-51_translated_retail_trial-3_id_kimi-k2.5_Qwen3-235B-A22B-Instruct-2507-FP8/results.json`, task `52`, trial `0`                                                                                                                                                                 | The user asks to exchange a delivered digital camera. The agent repeatedly calls `find_user_id_by_email({"email": "user@example.com"})`, gets `User not found`, and makes no task progress.                                                                               |
| Translated telecom has severe identifier hallucination when the user does not provide an account key. | `data/simulations/2026-05-18-21-51-53_translated_telecom_trial-3_id_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8/results.json`, service issue task, trial `0`                                                                                                                                                      | The agent tries `get_customer_by_phone` with `not_provided`, empty strings, `unknown`, `PENDING_USER_PROVIDE`, and similar placeholders instead of asking the user for a usable identifier.                                                                               |
| Translated airline has repeated tool-error loops on impossible or fabricated entities.                | `data/simulations/2026-05-19-15-14-21_translated_airline_trial-3_tl_kimi-k2.5_Qwen3-235B-A22B-Instruct-2507-FP8/results.json`, task `45`, trial `2`                                                                                                                                                                | The agent repeatedly queries flight `HAT789` on the same date and gets repeated `Flight HAT789 not found` errors instead of changing strategy or asking for clarification.                                                                                                |
| Some translated runs should not be counted as clean benchmark failures.                               | `data/simulations/2026-05-21-06-35-19_translated_telecom_trial-3_tl_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8/results.json` and `data/simulations/2026-05-21-11-53-32_translated_telecom_trial-3_vi_gpt-5-mini_Qwen3-235B-A22B-Instruct-2507-FP8/results.json`                                                  | Deterministic action analysis marks 342/342 `no_actions` for both runs, while failure-mode analysis shows 100% or near-100% fabricated identifier / tool-error behavior. These are likely bad or partial runs, not clean model quality estimates.                         |

## Language Notes

Language adherence alone does not explain the low pass rates.

- English baseline language is mostly clean, but still has 31-38% agent failure
  by domain.
- Corrected crosslingual language analysis must infer expected language from
  folder suffixes such as `_crosslingual_vietnamese`, because the extracted
  crosslingual `results.json` files do not populate `info.lang_id` or
  `info.seatau_info`. Raw `all_results_*_language.csv` therefore treats many
  crosslingual rows as expenslation pipcted English and is misleading without correction.
- Translated runs usually have the expected target language in metadata, and
  many translated traces are linguistically fluent, yet still fail from missing
  writes, placeholder identifiers, wrong tool arguments, and tool loops.

Existing corrected language summaries from the earlier pass remain useful for
baseline/crosslingual:

- `experiments/analysis_logs/baseline_crosslingual_user_language_corrected_summary.csv`
- `experiments/analysis_logs/baseline_crosslingual_agent_language_corrected_summary.csv`

## Interpretation

The strongest finding is that `pass_hat_k` is low for two different reasons:

1. In baseline and crosslingual, many failures are ordinary task completion
   failures. The agent often reads enough state but skips the required write,
   writes the wrong entity or payment method, transfers too early, or gives a
   final answer that violates an NL assertion.
2. In translated runs, the benchmark surface itself becomes more brittle. The
   agent more often fabricates identifiers, passes translated or placeholder
   values into lookup tools, loops on failed tools, or reaches no-action states.

Crosslingual prompting does not materially reduce aggregate success across all
agents in the local traces: baseline and crosslingual are both around 62-69%
success by domain. Full translation is much worse in these local runs: 38.7%
airline, 25.9% retail, and 25.1% telecom success, with telecom heavily confounded
by non-agent infrastructure and no-action traces.

## Recommendations

- Use `experiments/deep-reading-100-trace-addendum.md` as the turn-by-turn
  manual companion to the deterministic tables when interpreting `pass_hat_k`.
- Treat translated telecom TL/VI and other no-action dominated runs as
  `NEEDS_CHECK` rather than completed benchmark evidence.
- Add a deterministic guardrail for placeholder identifiers before scoring:
  `user@example.com`, empty phone numbers, `not_provided`, `unknown`, and similar
  lookup arguments should be flagged as invalid agent behavior.
- Add a crosslingual lookup audit: count non-ASCII names passed to English lookup
  APIs and whether the agent recovers with romanized names.
- For telecom, separate account/device instruction failures from ordinary DB
  write failures. Missing user-device actions are a repeated domain-specific
  failure in baseline, crosslingual, and translated traces.
- Keep using manual trace review in addition to deterministic scripts. The
  scripts catch action mismatch, but manual reading exposed hidden causes such
  as unrequested compensation, repeated fabricated identifiers, and premature
  escalation after adequate reads.
