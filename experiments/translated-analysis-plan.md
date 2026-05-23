# Translated SEA-Tau Analysis Plan

Date: 2026-05-22

## Goal

Build a more comprehensive and targeted analysis of agentic failure modes in non-English SEA-Tau settings, especially for the `translated` experiment where tasks, policy, tools, DB artifacts, prompts, and runtime language behavior are all localized.

The main research risk is conflating three different causes:

- true agentic multilingual failures
- translation/runtime-localization defects
- user-simulator or infrastructure artifacts

The plan below keeps the existing deterministic analysis as the quantitative backbone, then adds targeted LLM review and translation-aware attribution where it most affects the research claim.

## Current Evidence Base

Existing artifacts already provide a strong baseline:

- `experiments/experiments.csv`: tracker source of truth for run progress and high-level metrics.
- `experiments/failure_modes.csv`: per-simulation deterministic failure labels.
- `experiments/errors.csv`: user-simulator reliability summary.
- `experiments/failure_mode_tables/report/`: report-facing aggregate tables.
- `experiments/failure-mode-analysis.md`: current translated failure-mode writeup and manual validation.
- `experiments/2026-05-22-baseline-crosslingual-cross-experiment-analysis.md`: baseline/crosslingual/translated contrast.

Important current findings:

- Across analyzed translated simulations, agent failures dominate user-simulator reliability errors.
- Largest failure modes are `missing_required_write`, `credential_or_identifier_hallucination`, `tool_error_loop`, and `wrong_write_arguments_or_state`.
- Telecom and retail have the strongest failure signals.
- Thai and Tagalog currently have high aggregate agent-failure rates.
- Cross-experiment comparison suggests translated retail failures are not explained by language prompting alone; translated assets or runtime localization may be contributing.

## Priority 0: Refresh Canonical Inputs

Impact: Very high. Feasibility: High. Do this before drawing new claims.

TODO:

- Regenerate `experiments/failure_modes.csv` from the latest tracker-backed `DONE` and available runs.
- Regenerate `experiments/errors.csv`.
- Regenerate `experiments/failure_mode_tables/report/*`.
- Reconcile stale markdown notes with `experiments/experiments.csv`.
- Mark which prose notes are archival versus current if not immediately regenerated.

Rationale:

Some per-model markdown notes are stale relative to `experiments.csv`. Any claim about language, domain, or model performance should cite the generated CSVs or freshly regenerated notes, not older prose summaries.

Suggested commands:

```bash
uv run analyze-failure-modes \
  --experiments-csv experiments/experiments.csv \
  --output experiments/failure_modes.csv \
  --summary-dir experiments/failure_mode_tables/all_tracked

uv run analyze-user-reliability \
  --experiments-csv experiments/experiments.csv \
  --failure-modes-csv experiments/failure_modes.csv \
  --output experiments/errors.csv

uv run analyze-report-tables \
  --failure-modes-csv experiments/failure_modes.csv \
  --failure-summary-dir experiments/failure_mode_tables/all_tracked \
  --user-errors-csv experiments/errors.csv \
  --output-dir experiments/failure_mode_tables/report
```

## Priority 1: Add Translation-Aware Attribution

Impact: Very high. Feasibility: Medium. This most directly improves the research claim.

TODO:

- Add secondary attribution labels to the analysis output without replacing the existing mutually exclusive primary failure modes.
- Start with deterministic or mostly deterministic labels:
  - `final_write_omitted_after_correct_read`
  - `localized_enum_or_value_used_in_tool_arg`
  - `canonical_identifier_placeholder_used`
  - `localized_identifier_or_slot_used_for_lookup`
  - `device_action_treated_as_agent_tool`
  - `confirmation_loop_or_overcautious_stop`
  - `benign_language_detector_artifact`
  - `simulator_out_of_scope`
- Add higher-uncertainty labels only when supported by LLM review or manual audit:
  - `asset_translation_suspect`
  - `schema_label_confusion`
  - `policy_translation_misread`
  - `tool_description_misread`

Rationale:

The current primary modes are useful but not enough for causal attribution. For example, `missing_required_write` can mean overcautious policy behavior, failure to understand localized confirmation requirements, tool-schema confusion, or plain task-execution weakness. Secondary labels preserve the existing metrics while making non-English failure claims sharper.

Suggested implementation:

- Extend `src/seatau/analysis/failure_modes.py` secondary flags first.
- Emit semicolon-separated `translation_attribution_flags`.
- Keep the current `primary_failure_mode` stable until the new labels are validated.

## Priority 2: Build A Review Bridge For LLM Judge Outputs

Impact: High. Feasibility: Medium. Use for explanation, not canonical scoring.

TODO:

- Create `src/seatau/analysis/review_bridge.py`.
- Ingest reviewed outputs from `src/tau2/scripts/review_conversation.py`, especially `results_reviewed.json`.
- Join review data to deterministic rows by `(run, task_id, trial)`.
- Output a per-simulation CSV with:
  - deterministic primary and secondary modes
  - reward, termination reason, read/write failure counts
  - user-simulator reliability flags
  - agent/user language scores
  - LLM judge `agent_error`, `user_error`, severity, tags
  - short judge reasoning and correct behavior
  - attribution label: `agent_behavior`, `translation_asset`, `runtime_localization`, `simulator`, `infra`, or `ambiguous`

Rationale:

`review_conversation.py` is too expensive and judge-dependent to become the benchmark metric. Its value is semantic explanation and adjudication for ambiguous deterministic buckets.

Targeted review samples:

- `crosslingual_success -> translated_failure` task transitions.
- `non_action_assertion_failure`.
- `translated_identifier_lookup_failure`.
- high-count `credential_or_identifier_hallucination` slices.
- `missing_required_write` where reads passed.
- telecom `missing_user_device_instruction`.
- reward failures with near-perfect language correctness.
- matched successes for the same task/language/model.

## Priority 3: Static Translation Asset Audit

Impact: High. Feasibility: Medium. Essential before blaming agents for translated-retail failures.

TODO:

- Check `translation_manifest.json` presence and staleness for every analyzed translated run.
- Run DB structure parity checks for translated DB files.
- Audit protected-token leakage in translated `tasks.json`, `db.json`, `db.toml`, and policies.
- Audit translated schema artifacts:
  - value-set coverage
  - enum/localized label consistency
  - ambiguous localized labels mapping to multiple canonicals
- Audit tool docstrings for argument semantics changes.
- Produce an `experiments/translation_asset_audit.csv` keyed by `(domain, lang, asset_file, issue_type)`.

Rationale:

The `translated` preset includes translated policy, tasks, tools, DB, and runtime schema localization. A failure in translated retail may be an agent failure, but it may also be an artifact or localization issue. The research claim needs to separate these.

Suggested issue labels:

- `manifest_missing`
- `manifest_stale`
- `db_structure_mismatch`
- `protected_token_translated`
- `canonical_literal_translated`
- `localized_label_ambiguous`
- `schema_value_missing`
- `tool_doc_argument_semantics_changed`
- `policy_translation_ambiguous`
- `task_translation_ambiguous`

## Priority 4: Cross-Experiment Task Transition Tables

Impact: High. Feasibility: Medium to high, because the comparison note already has derived outputs.

TODO:

- Make task-transition tables a first-class generated artifact.
- For each `(domain, task_id, lang, agent)` compare:
  - baseline success rate
  - crosslingual success rate
  - translated success rate
  - localized success rate when available
- Classify transitions:
  - `baseline_fail_crosslingual_success`
  - `baseline_success_crosslingual_fail`
  - `crosslingual_success_translated_fail`
  - `crosslingual_fail_translated_success`
  - `always_fail`
  - `always_success`
  - `unstable`

Rationale:

The strongest evidence about non-English context effects is contrastive. If a task succeeds in crosslingual but fails in translated, the problem is more likely translated assets/runtime localization than ordinary L2 conversation. If it fails in baseline too, the failure is less likely to be specifically multilingual.

Highest-priority transition:

`crosslingual_success_translated_fail`

This is the most important bucket for auditing translated artifact harm.

## Priority 5: Focused Manual And LLM Review Slices

Impact: Medium to high. Feasibility: High if kept small.

TODO:

- Sample 20-30 traces per high-impact slice rather than broad random samples.
- Prioritize:
  - retail translated failures where crosslingual succeeded
  - telecom gpt-5-mini zero-pass runs
  - airline Kimi Thai/Chinese outliers
  - Tagalog and Thai high-failure slices
  - `missing_required_write` after correct reads
  - `credential_or_identifier_hallucination` loops
- For each sampled trace, record:
  - deterministic failure mode
  - whether user simulator contaminated the task
  - whether translated asset text appears suspicious
  - whether the agent had enough information to act
  - whether the failure is reproducible across trials

Rationale:

Manual review should now be used to validate specific causal claims, not just discover broad categories. The existing manual exploration already established the main buckets.

## Priority 6: Refresh Per-Model Live Notes

Impact: Medium. Feasibility: High.

TODO:

- Update:
  - `experiments/translated_gpt-5-mini.md`
  - `experiments/translated_kimi-k2.5.md`
  - `experiments/translated_qwen3.6-35b-a3b.md`
  - `experiments/translated_user-llm.md`
- Use regenerated CSV outputs, not stale run summaries.
- Add a short freshness footer:
  - tracker row count
  - last regenerated date
  - analysis CSV source

Rationale:

The live notes are useful for narrative, but currently some are stale relative to the tracker. They should either be updated or clearly marked as historical.

## Priority 7: Claim-Oriented Reporting

Impact: Medium. Feasibility: High after priorities 0-4.

TODO:

- Write a compact claim table:
  - Claim
  - Evidence
  - Confounders
  - Required next check
- Suggested claims:
  - Non-English translated failures are mostly task-execution/tool-use failures, not user-simulator language drift.
  - Translated retail introduces additional failure beyond crosslingual prompting.
  - Telecom has a distinct user-device action-boundary failure mode.
  - Thai and Tagalog are currently high-risk languages, but the dominant cause differs by domain and agent.
  - Language correctness alone is insufficient as a success proxy.

Rationale:

This keeps the analysis aligned with paper/report claims and prevents spending effort on low-value tables.

## Defer For Now

Lower impact or lower feasibility:

- Running LLM review over every simulation.
- Replacing deterministic primary modes with LLM-generated taxonomies.
- Creating a fully automatic translation-quality judge before static audits are in place.
- Treating fastText language drift as task-critical without manual or heuristic filtering.
- Generalizing telecom findings to all languages/models before missing and `NEEDS_CHECK` rows are cleaned up.

## Expected Deliverables

Near-term:

- Fresh generated failure and user-reliability tables.
- `translation_attribution_flags` added to failure-mode rows.
- A targeted reviewed-trace CSV joining LLM judge outputs with deterministic analysis.
- Static translation asset audit CSV.
- Updated high-level markdown summary distinguishing agent behavior, translation asset issues, simulator issues, and infra.

Research-facing:

- A contrastive task-transition table showing baseline -> crosslingual -> translated behavior.
- A claim-support matrix with confounders and required validation.
- A small set of trace exemplars for the highest-impact failure patterns.
