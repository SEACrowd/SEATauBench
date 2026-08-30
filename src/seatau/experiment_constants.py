"""Domain constants shared by the SEA-TauBench analysis and plot layers.

Scenario/language/model labels, ordering, and the ``FILTER_SETTING`` scope
used to select and label experiment rows. Lives outside ``seatau.plot.style``
and ``seatau.analysis.experiment_metrics`` on purpose: both need these
constants, so neither should have to import the other to get them (that
was a circular import). This module depends on neither.
"""

from __future__ import annotations

from seatau.constants import get_language_display_name_by_code
from seatau.experiment_matrix import (
    get_scenario_display_name,
    list_all_scenarios,
    list_supported_domains,
)

LANGUAGE_DISPLAY_NAME_BY_CODE = get_language_display_name_by_code()

METRIC_RENAMES = {
    "pass_hat_1": "pass@1",
    "pass_hat_2": "pass^2",
    "pass_hat_3": "pass^3",
    "rho_hat_3": "rho^3",
}
PRIMARY_METRICS = ("pass@1", "rho^3")
LANGUAGE_ORDER = [
    display_name.lower() for display_name in LANGUAGE_DISPLAY_NAME_BY_CODE.values()
]
LANGUAGE_CODE_BY_KEY = {
    display_name.lower(): code
    for code, display_name in LANGUAGE_DISPLAY_NAME_BY_CODE.items()
}
TOOL_MIX_ORDER = ["tool_mix_2", "tool_mix_3", "tool_mix_4", "tool_mix_5"]

FILTER_SETTING = {
    "scenario": list_all_scenarios(include_auxiliary=True),
    "domain": list_supported_domains(),
    "language_senario": LANGUAGE_ORDER + TOOL_MIX_ORDER,
    "normalized_agent_llm": [
        "gpt-5-mini",
        "qwen-3-235b-it",
        "kimi-k2.5",
    ],
}

SCENARIO_ORDER = list_all_scenarios()
SCENARIO_LABELS = {
    scenario: get_scenario_display_name(scenario)
    for scenario in FILTER_SETTING["scenario"]
}
SCENARIO_ID_BY_NAME = {
    scenario: idx for idx, scenario in enumerate(FILTER_SETTING["scenario"], start=1)
}
SCENARIO_NAME_BY_ID = {value: key for key, value in SCENARIO_ID_BY_NAME.items()}
NON_BASELINE_SCENARIO_ORDER = ["l2_interaction", "l2_tools", "l2_domain"]
LANGUAGE_LABELS = {
    **{language: LANGUAGE_CODE_BY_KEY[language].upper() for language in LANGUAGE_ORDER},
    **{mix: f"Mix {mix.rsplit('_', maxsplit=1)[-1]}" for mix in TOOL_MIX_ORDER},
}
LANGUAGE_DISPLAY_NAMES = {
    **{
        display_name.lower(): display_name
        for display_name in LANGUAGE_DISPLAY_NAME_BY_CODE.values()
    },
    **{mix: f"Tool Mix {mix.rsplit('_', maxsplit=1)[-1]}" for mix in TOOL_MIX_ORDER},
}

MODEL_ORDER = FILTER_SETTING["normalized_agent_llm"]
MODEL_LABELS = {
    "gpt-5-mini": "GPT 5 Mini",
    "kimi-k2.5": "Kimi K2.5",
    "qwen-3-235b-it": "Qwen3 235B IT",
}
