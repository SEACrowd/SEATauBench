# translated / user-llm (Qwen3-235B-A22B-Instruct-2507-FP8)

## Long-Term TODOs (2026-05-20)

- Run translated `retail` and `airline` for all languages with a Qwen3-235B-class agent after the Qwen3.6 retail reruns are clean.
- Prefer the local user-LLM server as the agent first, using `Qwen3-235B-A22B-Instruct-2507-FP8` for both user and agent LLM. Start at concurrency 4-6 because both sides share the same server.
- If local progress is too slow to finish the retail + airline sweep inside the 6-7 hour target, switch the agent to `openrouter/qwen/qwen3-235b-a22b-2507` while keeping the local user simulator. Increase concurrency only while retry/rate-limit churn stays low.
- If both local and hybrid modes are still too slow, use `openrouter/qwen/qwen3-235b-a22b-2507` for both sides with separate OpenRouter keys (`OPENROUTER_API_KEY_ALGOVERSE` and `OPENROUTER_API_KEY`) to separate limits. Balance cost against throughput.
- Keep telecom out of this queue unless explicitly reassigned.

## Overview

No runs completed yet — all 15 rows are TODO. This is the lowest-priority agent LLM in the sweep order (after gpt-5-mini, kimi-k2.5, and qwen3.6-35b-a3b). Because the user-LLM is also the user simulator, concurrency limits and server stability will be more critical than for other agents.

## Runs Summary Table

| Domain  | Lang | Progress | Pass@1 | Pass@2 | Pass@3 | Lang Correct | Notes |
|---------|------|----------|--------|--------|--------|--------------|-------|
| retail  | id   | TODO     | —      | —      | —      | —            | |
| retail  | th   | TODO     | —      | —      | —      | —            | |
| retail  | tl   | TODO     | —      | —      | —      | —            | |
| retail  | vi   | TODO     | —      | —      | —      | —            | |
| retail  | zh   | TODO     | —      | —      | —      | —            | |
| airline | id   | TODO     | —      | —      | —      | —            | |
| airline | th   | TODO     | —      | —      | —      | —            | |
| airline | tl   | TODO     | —      | —      | —      | —            | |
| airline | vi   | TODO     | —      | —      | —      | —            | |
| airline | zh   | TODO     | —      | —      | —      | —            | |
| telecom | id   | TODO     | —      | —      | —      | —            | |
| telecom | th   | TODO     | —      | —      | —      | —            | |
| telecom | tl   | TODO     | —      | —      | —      | —            | |
| telecom | vi   | TODO     | —      | —      | —      | —            | |
| telecom | zh   | TODO     | —      | —      | —      | —            | |

## Analysis

TBD — fill after runs complete.

## Notes for running

- User and agent LLM are the same model (Qwen3-235B); resource contention may lower throughput.
- Monitor `localhost:8000` closely; use `scripts/lanta_vllm_watchdog.sh` as fallback.
- Start with lower concurrency (4-6) and adjust based on observed error rate and throughput.
- See CLAUDE.md for watchdog and sweep setup details.
