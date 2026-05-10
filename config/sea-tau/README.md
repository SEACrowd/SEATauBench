# SEA-TAU Experiment Config

This directory contains the source-of-truth configuration for SEA-TAU experiment presets.

## Files

| Path | Purpose |
| --- | --- |
| `experiments.yaml` | Experiment definitions, aliases, language components, and mixed-tools flags. |
| `mixed_tools/*.json` | Tool-language partition configs used by `mixed_tools` presets. |

Supported SEA-TAU domains are `airline`, `retail`, and `telecom`. The `mock`
domain remains available for core tau2 tests, but SEA-TAU wrappers skip it.

## Experiment language matrix

| Experiment | User conversation | Agent conversation | Tool language | Context (db/tasks/policy) | Asset mode |
| --- | --- | --- | --- | --- | --- |
| `baseline` | English | English | English | English | `original` |
| `mixed_tools` | English | English | Mixed (English + selected L2s) | English | `original` |
| `crosslingual` | L2 | L2 | English | English | `original` |
| `translated` | L2 | L2 | L2 | L2 | `translated` (`{lang_id}`) |
| `localized` | L2 | L2 | L2 | L2 | `localized` (`{lang_id}_loc`) |

## Notes

1. `mixed_tools` presets use only the `mixed_tools` component and keep conversation/greeting English.
2. `--mixed-tools-config` is only valid when `mixed_tools` is enabled.
3. Localized artifacts live in optional `{lang_id}_loc` directories. A
   `localized` run requires the relevant files there and does not fall back to
   `{lang_id}` or English assets.
4. When using `scripts/run_seatau.sh` without `--lang-id`, experiments fan out across non-English registry languages.

## Evaluation Metrics

SEA-TAU keeps the upstream tau2 task-success metrics intact. Task reward is still
computed from the task's `reward_basis`: DB state, environment assertions, action
checks, communication checks, and optional NL assertions.

SEA-TAU also records `language_correctness` in `reward_info.info`. The expected
assistant language is English for `baseline` and `mixed_tools`, and the target L2
for `crosslingual`, `translated`, and `localized`. The score is the proportion of
assistant text turns detected in the expected language by fastText LID.

The language model defaults to `data/models/lid.176.bin`; override with
`TAU2_FASTTEXT_LID_MODEL_PATH` if needed. This metric is recorded as metadata by
default. It affects final reward only when a task explicitly includes
`LANGUAGE_CORRECTNESS` in `reward_basis` or when using
`EvaluationType.LANGUAGE_CORRECTNESS`.

For command-level behavior and examples, see [`scripts/run_seatau.sh`](../../scripts/run_seatau.sh).
