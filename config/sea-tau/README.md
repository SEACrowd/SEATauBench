# SEA-TAU Experiment Config

This directory contains the source-of-truth configuration for SEA-TAU experiment presets.

## Files

| Path | Purpose |
| --- | --- |
| `experiments.yaml` | Experiment definitions, aliases, language components, and mixed-tools flags. |
| `mixed_tools/*.json` | Tool-language partition configs used by `mixed_tools` presets. |

## Experiment language matrix

| Experiment | User conversation | Agent conversation | Tool language | Context (db/tasks/policy) |
| --- | --- | --- | --- | --- |
| `baseline` | English | English | English | English |
| `mixed_tools` | English | English | Mixed (English + selected L2s) | English |
| `crosslingual` | L2 | L2 | English | English |
| `translated` | L2 | L2 | L2 | L2 |
| `localized` | L2 | L2 | L2 | L2 |

## Notes

1. `mixed_tools` presets use only the `mixed_tools` component and keep conversation/greeting English.
2. `--mixed-tools-config` is only valid when `mixed_tools` is enabled.
3. When using `scripts/run_seatau.sh` without `--lang-id`, experiments fan out across non-English registry languages.

For command-level behavior and examples, see [`scripts/run_seatau.sh`](../../scripts/run_seatau.sh).
