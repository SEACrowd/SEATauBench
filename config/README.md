# Configuration Reference

Central location for runtime and experiment configuration files.

## Files and directories

| Path | Purpose |
| --- | --- |
| `languages.json` | Language registry used by `--lang-id` and multilingual runtime behavior. |
| `sea-tau/experiments.yaml` | SEA-TAU experiment presets, aliases, and language components. |
| `sea-tau/mixed_tools/*.json` | Mixed-language tool partition configs for SEA-TAU Experiment 1. |

## Specialized docs

- SEA-TAU preset behavior and experiment matrix: [`config/sea-tau/README.md`](sea-tau/README.md)
- Translation pipeline and multilingual artifacts: [`src/translation/README.md`](../src/translation/README.md)
