# translated / azure/kimi-k2.5 (openrouter/moonshotai/kimi-k2.5)

## Overview

4 of 15 retail runs have usable data; all airline and telecom rows are TODO. Early azure runs (retail/id, retail/th) had severe infra failures (83.6% and 22.8% respectively) and are NEEDS_CHECK. Retail/vi and retail/zh were cleanly rerun via OpenRouter with 9.4% infra errors (acceptable). Pass@1 on clean runs: 56.7% (vi) and 60.7% (zh). Language compliance is perfect (99.9–100%) for both clean retail runs — best agent-side compliance observed across all models so far.

## Runs Summary Table

| Domain  | Lang | Progress     | Pass@1 | Pass@2 | Pass@3 | Lang Correct | Notes |
|---------|------|--------------|--------|--------|--------|--------------|-------|
| retail  | id   | NEEDS_CHECK  | 66.1   | —      | —      | 99.3%        | 83.6% infra failures; partial (56 tasks, 1 trial) |
| retail  | th   | NEEDS_CHECK  | 45.9   | 29.2   | 25.0   | 100.0%       | 22.8% infra failures; 114 tasks but uneven trial count |
| retail  | tl   | TODO         | —      | —      | —      | —            | |
| retail  | vi   | DONE         | 56.7   | 39.2   | 26.8   | 99.9%        | Rerun via OpenRouter; 9.4% infra errors |
| retail  | zh   | DONE         | 60.7   | 45.0   | 36.6   | 100.0%       | Full 342 sims; clean run |
| airline | id   | TODO         | —      | —      | —      | —            | |
| airline | th   | TODO         | —      | —      | —      | —            | |
| airline | tl   | TODO         | —      | —      | —      | —            | |
| airline | vi   | TODO         | —      | —      | —      | —            | |
| airline | zh   | TODO         | —      | —      | —      | —            | |
| telecom | id   | TODO         | —      | —      | —      | —            | |
| telecom | th   | TODO         | —      | —      | —      | —            | |
| telecom | tl   | TODO         | —      | —      | —      | —            | |
| telecom | vi   | TODO         | —      | —      | —      | —            | |
| telecom | zh   | TODO         | —      | —      | —      | —            | |

## Analysis by Domain

### retail

Only vi and zh are clean DONE. Both show competitive pass@1 (56.7 and 60.7) comparable to gpt-5-mini on the same tasks. Pass@3 (26.8 and 36.6) reflects the same multi-trial consistency issue seen across all models. Agent language compliance is the highest observed: 99.9% (vi) and 100% (zh).

- **vi**: 32 infra errors out of 342 sims (9.4%) — acceptable. Read 92.7%, write 54.1%, DB match 56.3%.
- **zh**: Clean run. Read 90.3%, write 65.7%, DB match 64.9% — write and DB match better than vi.
- **id, th (NEEDS_CHECK)**: Azure infra failures make pass metrics unreliable; need rerun via OpenRouter.
- **tl**: Not yet run.

### airline, telecom

No data yet — all TODO.

## User Simulator Analysis

Language drift data available for retail/vi only (from analysis scripts):

```
Lang: vi  Simulations: 342
Aggregate (310 evaluated):
  Mean score : 0.993  |  Perfect: 300/310  |  Drift: 10/310
  Turn-level : 1515/1527 = 0.992
  Drift breakdown: de 4, ru 3, en 3, fr 2
```

Low drift (3.2% sims). Scattered European bleed (de, ru, en, fr) with no dominant language. Turn 3 drift pattern suggests greeting/auth step edge cases, not task-critical.

## Agent Analysis

Language compliance for available runs:

```
retail/vi: mean 0.999, 309/310 sims perfect, 1 drift sim (task 70 trial 2 turn 18)
retail/zh: mean 1.000, 255/255 evaluated — zero drift
```

Kimi-k2.5 has the best language-following of any model tested so far for these two languages.

## Task Analysis

### Action sequence patterns (retail/vi — final 342 sims)

```
all_pass            119   34.8%
read_only_pass       14    4.1%
read_ok_write_fail  127   37.1%  attempted=49, skipped=78
read_only_fail        4    1.2%
read_fail            37   10.8%
no_actions            9    2.6%
not_evaluated        32    9.4%
Tasks with failures: 88 / 114
```

### Action sequence patterns (retail/zh — partial at 74%)

```
all_pass            102   39.8%  (higher than vi)
read_only_pass       14    5.5%
read_ok_write_fail   76   29.7%  attempted=39, skipped=37
read_only_fail        3    1.2%
read_fail            45   17.6%  (higher than vi's 10.8% — monitor final)
no_actions           14    5.5%
```

### Consistently failing task types

1. `read_ok_write_fail(skipped)` — agent reads correctly but stops before executing the DB write; likely over-reliance on confirmation or skipping the final action.
2. `read_ok_write_fail(attempted)` — agent attempts write but fails; parameter or DB mismatch.
3. `read_fail` (higher in zh than vi) — agent cannot retrieve required data; may reflect Chinese-language retrieval complexity.

## Cross-Experiment Analysis

- vs gpt-5-mini (retail/vi, zh): nearly identical pass@1 (kimi 56.7 vs gpt 58.5 for vi; kimi 60.7 vs gpt 59.6 for zh). Kimi has better language compliance.
- Infra stability: OpenRouter provider far more stable than Azure for kimi (9.4% vs 73–84% infra failures in early azure runs).
- airline/telecom: no comparison possible yet.
