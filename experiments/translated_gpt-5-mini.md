# translated / azure/gpt-5-mini

## Overview

10 of 15 runs DONE; telecom/id IN_PROGRESS; telecom/th–zh TODO. Airline pass@1 is consistent (54–60.7%). Retail is more variable (32.5–59.6%); Thai is a clear outlier at 32.5%, likely due to translation quality or Thai-specific policy confusion. Language compliance is near-perfect for th/vi/zh (95–100%) but lower for id and tl in some domains. Write action success (37–64%) is the main bottleneck in retail.

## Runs Summary Table

| Domain  | Lang | Progress    | Pass@1 | Pass@2 | Pass@3 | Lang Correct | Notes |
|---------|------|-------------|--------|--------|--------|--------------|-------|
| airline | id   | DONE        | 60.0   | 54.0   | 50.0   | 79.6%        | Lower lang compliance |
| airline | th   | DONE        | 59.3   | 45.3   | 36.0   | 99.4%        | |
| airline | tl   | DONE        | 56.0   | 43.3   | 38.0   | 83.1%        | |
| airline | vi   | DONE        | 54.0   | 40.0   | 32.0   | 99.7%        | |
| airline | zh   | DONE        | 60.7   | 49.3   | 44.0   | 96.5%        | |
| retail  | id   | DONE        | 54.1   | 39.2   | 32.5   | 95.3%        | |
| retail  | th   | DONE        | 32.5   | 17.5   | 12.3   | 99.7%        | Lowest across all gpt-5-mini retail runs |
| retail  | tl   | DONE        | 48.8   | 33.3   | 26.3   | 97.0%        | |
| retail  | vi   | DONE        | 58.5   | 42.7   | 33.3   | 99.8%        | |
| retail  | zh   | DONE        | 59.6   | 45.0   | 36.8   | 97.3%        | |
| telecom | id   | IN_PROGRESS | 61.7   | 56.1   | 53.8   | 99.3%        | Write 80%; read_action_count=0 in CSV (partial metrics) |
| telecom | th   | TODO        | —      | —      | —      | —            | |
| telecom | tl   | TODO        | —      | —      | —      | —            | |
| telecom | vi   | TODO        | —      | —      | —      | —            | |
| telecom | zh   | TODO        | —      | —      | —      | —            | |

## Analysis by Domain

### retail

Pass@1 ranges 32.5–59.6. Thai is a clear outlier (32.5, write 37%) — significantly below all other languages (write 54–64%). Vietnamese and Chinese are the strongest (58–60%). The pass@1→pass@3 drop is large (~20pp across languages), indicating tasks succeed inconsistently rather than reliably.

- **th**: Write action rate 37% vs 54–64% for other langs; likely policy-following breakdown for Thai cancellation/return flow.
- **id**: Language compliance 95.3% — lowest in retail; occasional drift out of Indonesian.
- **vi, zh**: Best retail performance (pass@1 58–60%, write 64%).

### airline

More consistent across languages (pass@1 54–60.7). Write action rates are low (16–27%) by design — airline tasks are information-heavy. Read rates 75–93%. Language compliance varies: id (79.6%) and tl (83.1%) show more drift.

### telecom

Only id is in progress. Early metrics are strong: pass@1 61.7, pass@3 53.8, write 80% — highest write success seen for gpt-5-mini. Four languages still TODO.

## User Simulator Analysis

Language drift is low overall (most runs 95–100%). The Qwen3-235B simulator is reliable across all 5 SEA languages.

- Airline/id and airline/tl show lower compliance (79.6%, 83.1%), possibly simulator edge cases in English.

## Agent Analysis

Language compliance consistently high (95–100%) for th, vi, zh. Weaker for id (79.6–95.3%) and tl (83.1–97%) — gpt-5-mini has marginally more language drift for Indonesian and Filipino.

## Task Analysis

### Action sequence patterns (aggregate)

Retail read rates 75–91%, write rates 37–64%. Dominant retail failure pattern: `read_ok_write_fail` — agent retrieves data correctly but fails to execute or confirm the DB write. Airline write rates uniformly low (16–27%), reflecting the domain's information-retrieval focus.

### Consistently failing task types

- Retail write-action tasks (cancel, return, exchange): agent reads correctly then skips or fails confirmation+write, especially in Thai.
- Multi-step confirmation tasks: large pass@1→pass@3 gap suggests these succeed by chance.

## Cross-Experiment Analysis

- vs qwen3.6-35b-a3b: airline pass@1 (54–60.7%) is notably lower than qwen3.6 (67–74%). Retail is comparable.
- vs kimi-k2.5 (retail only): very similar — kimi retail/vi 56.7 ≈ gpt-5-mini retail/vi 58.5; kimi retail/zh 60.7 ≈ gpt-5-mini retail/zh 59.6.
