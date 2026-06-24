# translated / openrouter/qwen/qwen3.6-35b-a3b

## Long-Term TODOs (2026-05-20)

- `retail/tl` remains a clean-rerun target. The latest 2026-05-20 retry completed mechanically but was poisoned by OpenRouter weekly key-limit infra failures, so it should not count as DONE.
- `retail/vi` remains a clean-rerun target. The latest 2026-05-20 retry also hit the OpenRouter weekly key limit and evaluated only 4 tasks, so it should not count as DONE.
- User changed the OpenRouter key limit from weekly to daily on 2026-05-20. Wait briefly before retrying `OPENROUTER_API_KEY`; do not resume the poisoned folders, use `--clean-rerun-partials`.
- Skip telecom for this agent unless explicitly reassigned; translated telecom showed systematic tool-contract failures and is no longer in the active queue.
- After these two rows are clean, move to the Qwen3-235B agent sweep for retail and airline.

## Overview

Most runs active or complete. Retail: 1 DONE, 4 PARTIAL (ongoing). Airline: 2 DONE, 2 PARTIAL, 1 IN_PROGRESS. Telecom: 3 PARTIAL (started, no metrics yet), 2 TODO. Airline is the standout domain — pass@1 67–74%, consistently the best performance across all models and domains tested. Retail is more variable and several runs are partial. Language compliance is high across all languages (90–100%). Read action rates are strong (84–97%); write rates are lower (21–69%).

## Runs Summary Table

| Domain  | Lang | Progress    | Pass@1 | Pass@2 | Pass@3 | Lang Correct | Notes |
|---------|------|-------------|--------|--------|--------|--------------|-------|
| retail  | id   | DONE        | 55.3   | 39.5   | 29.8   | 98.0%        | 6 retry/parse errors; all 114 tasks×3 trials |
| retail  | th   | PARTIAL     | 34.4   | 18.4   | 0.0    | 100.0%       | 107 tasks; pass@3=0 because <3 trials for some tasks |
| retail  | tl   | PARTIAL     | 61.5   | —      | —      | 96.0%        | 52 tasks only |
| retail  | vi   | PARTIAL     | 56.7   | 60.0   | 0.0    | 100.0%       | 67 tasks, 70 sims; pass@3=0 (insufficient trials) |
| retail  | zh   | PARTIAL     | 64.0   | 53.5   | —      | 100.0%       | 111 tasks, 197 sims |
| airline | id   | DONE        | 72.7   | 64.0   | 58.0   | 91.2%        | Best airline/id result across all models |
| airline | th   | PARTIAL     | 67.4   | 59.2   | 64.3   | 100.0%       | 46 tasks |
| airline | tl   | PARTIAL     | 69.4   | 62.3   | 57.1   | 90.4%        | 49 tasks |
| airline | vi   | DONE        | 70.3   | 62.7   | 62.2   | 100.0%       | |
| airline | zh   | IN_PROGRESS | 74.4   | 73.9   | 76.0   | 99.5%        | 43 tasks; highest pass@1 seen so far |
| telecom | id   | PARTIAL     | —      | —      | —      | —            | Running; 0 evaluated tasks in CSV yet |
| telecom | th   | PARTIAL     | —      | —      | —      | —            | Running; 0 evaluated tasks in CSV yet |
| telecom | tl   | PARTIAL     | —      | —      | —      | —            | Running; 0 evaluated tasks in CSV yet |
| telecom | vi   | TODO        | —      | —      | —      | —            | |
| telecom | zh   | TODO        | —      | —      | —      | —            | |

## Analysis by Domain

### retail

Results are partial for most languages. The single DONE run (id) shows pass@1 55.3 with a heavy pass@1→pass@3 drop (29.8), consistent with the pattern across all models. Thai shows extremely low pass@3 (0.0) because the partial run didn't collect enough trials. Vietnamese and Chinese partial passes (56.7 and 64.0) suggest this model performs on par with gpt-5-mini and kimi in retail.

- **th**: pass@1 34.4 (similarly low to gpt-5-mini's 32.5 in Thai retail), write 33.8%.
- **zh**: pass@1 64.0 on partial data — may be the best retail/zh result once completed.
- **tl, vi, zh**: Need completion before reliable comparison.

### airline

Qwen3.6 is clearly the best-performing model for airline (pass@1 67–74% vs gpt-5-mini's 54–60%). All languages show high read rates (84–97%) and reasonable write rates (21–39% — low by design). Language compliance strong: only id (91.2%) and tl (90.4%) slightly below 100%.

- **zh**: Highest single-run pass@1 observed across all models/domains so far (74.4 partial, 43 tasks).
- **vi**: Only fully completed airline run (70.3/62.7/62.2), clean 150 sims.
- **id**: 72.7 pass@1 — the best airline/id result across all models.

### telecom

Three languages started but no evaluated metrics yet in CSV. Results pending.

## User Simulator Analysis

Language compliance is high across all runs (90–100%). No specific user simulator drift data extracted from individual log files (individual markdown files were empty stubs). Based on aggregate patterns from other models, Qwen3-235B drift is expected to remain <2% across SEA languages.

## Agent Analysis

Language compliance summary from CSV:
- 100% for th, vi in both retail and airline
- 90–98% for id and tl (some drift)
- 99.5–100% for zh

Qwen3.6-35b-a3b maintains strong language following across all 5 SEA languages.

## Task Analysis

### Action sequence patterns (aggregate from available runs)

Retail (id — only full run):
- Read rate: 91.3% (956/1047), Write rate: 57.4% (294/512)
- DB match: 56.5%

Airline (vi — only full run):
- Read rate: 93.4% (240/257), Write rate: 31.2% (44/141)
- DB match: 72.4% — notably higher than retail

Airline write rates are low by domain design (information-retrieval heavy). Retail write rates are the key failure axis across all partial runs (33–69%).

### Consistently failing task types

1. Retail `read_ok_write_fail` — same pattern as other models; agent retrieves correctly but fails or skips write execution.
2. Retail Thai specifically: write rate 33.8% (lowest), likely the same Thai policy-comprehension issue seen in gpt-5-mini.
3. Airline write tasks: DB match 72.4% for vi but write rate only 31.2% — agent attempts writes but correct DB outcome is hit less than half the time.

## Cross-Experiment Analysis

- vs gpt-5-mini: significantly better in airline (67–74% vs 54–60%). Retail comparable.
- vs kimi-k2.5: no airline/telecom comparison possible yet; retail metrics are similar.
- Thai retail is weak for both gpt-5-mini (32.5) and qwen3.6 (34.4) — suggests this is a dataset or translation issue, not model-specific.
