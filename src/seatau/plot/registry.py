"""Registry of SEA-Tau figure outputs and their plot modules."""

from __future__ import annotations

FIGURE_MODULES: dict[str, str] = {
    "en_vs_l2_perf": "seatau.plot.english_vs_non_english",
    "en_vs_l2_perf_bars": "seatau.plot.english_vs_non_english_bars",
    "error_breakdown_by_setting_role": "seatau.plot.error_breakdown",
    "language_correctness_heatmap": "seatau.plot.language_correctness_heatmap",
    "metric_correlation_matrix": "seatau.plot.metric_correlation_matrix",
    "perf_by_language": "seatau.plot.perf_by_language",
    "perf_tool_mix": "seatau.plot.perf_tool_mix",
}

COUPLED_FIGURE_MODULES: dict[str, str] = {
    "agent_english_share_boxplots": "seatau.plot.language_drift",
    "agent_english_share_by_model_heatmap": "seatau.plot.language_drift",
    "tool_mix_agent_language_use": "seatau.plot.language_drift",
    "language_drift_by_turn_position": "seatau.plot.language_drift",
    "language_degradation": "seatau.plot.language_degradation",
    "language_vs_perf": "seatau.plot.language_vs_perf",
    "specific_failure_mode_share": "seatau.plot.specific_failure_mode_share",
}

STATIC_FIGURES = frozenset(
    {
        "domain_viewer",
        "overview",
        "traj",
    }
)
