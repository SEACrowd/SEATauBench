# Experiments

This directory contains **experimental code** that is offered as-is and should be
treated as experimental components, not part of the core tau2 benchmark.

> ⚠️ **Important**: The code in this directory is experimental and may not be fully tested or supported. Use at your own discretion.

## When to read this

Read this file to choose the right experiment module. For usage and implementation
details, use the submodule READMEs below.

## Experiment modules

| Module | README | Scope |
| --- | --- | --- |
| Hyperparameter sweeps | [`hyperparam/README.md`](hyperparam/README.md) | Parameterized eval runs and analysis tooling. |
| Mixed-language tools (SEA-TAU EXP #1) | [`mixed_lang_tools/README.md`](mixed_lang_tools/README.md) | Tool-doc language partitioning and config generation. |
| Agentified Tau-Bench | [`agentify_tau_bench/README.md`](agentify_tau_bench/README.md) | A2A benchmark-agent workflow and orchestration. |

SEA-TAU preset semantics and matrix live in
[`config/sea-tau/README.md`](../../config/sea-tau/README.md).

## Directory Structure

Each experiment should be isolated in its own subdirectory with its own README.

## Quick Start

To contribute experimental code:

1. Create a new subdirectory for your experiment
2. Add a comprehensive README.md explaining the purpose and usage
3. Include example scripts and basic tests
4. Follow the development guidelines below 

## Development Guidelines

When working with experimental code:

1. **Backward Compatibility**: Maintain compatibility with core tau2 interfaces when possible
2. **Documentation**: Each experimental component should have its own README
3. **Testing**: Include basic testing scripts and examples
4. **Dependencies**: Manage dependencies carefully to avoid conflicts with core tau2
5. **Isolation**: Keep experimental code self-contained within this directory

## Contributing

Experimental contributions are welcome! Please:

1. Add comprehensive documentation in your subfolder's README
2. Include example usage and test scripts
3. Mark any breaking changes or dependencies clearly
4. Consider the experimental nature - code doesn't need to be production-ready

## Support

Since this is experimental code:

- **No guarantees** of stability or continued support
- **Community-driven** - contributions and improvements welcome
- **Use at your own risk** - test thoroughly before production use
- **Documentation-first** - refer to individual README files for detailed usage

For core tau2 benchmark support, see the main project documentation.
