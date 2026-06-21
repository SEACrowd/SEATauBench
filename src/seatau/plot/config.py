"""Shared configuration constants for SEA-TauBench figure scripts.

Column names match experiments_all.csv exactly.
"""

from seatau.constants import (
    EXPERIMENTS_CSV,
    FIGS_DIR,
    LANGUAGE_DISPLAY_NAME_BY_CODE,
    PROJECT_ROOT,
)
from seatau.experiment_matrix import (
    get_scenario_display_name,
    list_all_scenarios,
    list_supported_domains,
)

REPO_ROOT = PROJECT_ROOT
DEFAULT_CSV_PATH = EXPERIMENTS_CSV
DEFAULT_FIG_DIR = FIGS_DIR

EXPORT_FORMATS = ("pdf", "png")
EXPORT_DPI = 400
SEA_COLORS = {
    "red": "#ed2939",
    "blue": "#0042a6",
    "yellow": "#f9e300",
    "white": "#ffffff",
    "black": "#111111",
}
SEA_COLOR_SEQUENCE = (
    SEA_COLORS["blue"],
    SEA_COLORS["red"],
    SEA_COLORS["yellow"],
)
PLOT_FONT_FAMILY = ("Helvetica Neue", "Avenir Next", "DejaVu Sans")
PLOT_BASE_FONT_SIZE = 8
PLOT_TITLE_SIZE = 10
PLOT_LABEL_SIZE = 9
PLOT_TICK_SIZE = 8
PLOT_LEGEND_SIZE = 8
PLOT_COLUMN_WIDTH = 3.35
PLOT_TWO_COLUMN_WIDTH = 7.0
PLOT_ROW_HEIGHT = 2.5
PLOT_PANEL_SIZE = (2.55, 2.15)
PLOT_FIGSIZE_ONE_COL = (PLOT_COLUMN_WIDTH, 2.45)
PLOT_FIGSIZE_ONE_COL_TALL = (PLOT_COLUMN_WIDTH, 4.15)
PLOT_FIGSIZE_ONE_COL_SHORT = (PLOT_COLUMN_WIDTH, 1.85)
PLOT_FIGSIZE_TWO_COL = (PLOT_TWO_COLUMN_WIDTH, 2.95)
PLOT_FIGSIZE_TWO_COL_SHORT = (PLOT_TWO_COLUMN_WIDTH, 2.2)
PLOT_FIGSIZE_TWO_COL_TALL = (PLOT_TWO_COLUMN_WIDTH, 4.4)
PLOT_FIGSIZE_TWO_COL_LARGE = (PLOT_TWO_COLUMN_WIDTH, 6.0)
PLOT_FIGSIZE_TWO_COL_WIDE = (8.8, 4.4)
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
    "scenario": list_all_scenarios(),
    "domain": list_supported_domains(),
    "language_senario": LANGUAGE_ORDER + TOOL_MIX_ORDER,
    "normalized_agent_llm": [
        "gpt-5-mini",
        "qwen-3-235b-it",
        "kimi-k2.5",
    ],
}

SCENARIO_ORDER = FILTER_SETTING["scenario"]
SCENARIO_LABELS = {
    scenario: get_scenario_display_name(scenario) for scenario in SCENARIO_ORDER
}
SCENARIO_ID_BY_NAME = {
    scenario: idx for idx, scenario in enumerate(SCENARIO_ORDER, start=1)
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
