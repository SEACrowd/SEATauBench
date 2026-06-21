"""Shared configuration constants for SEA-TauBench figure scripts.

Column names match experiments_all.csv exactly.
"""

from pathlib import Path

from seatau.experiment_matrix import get_scenario_display_name
from seatau.paths import EXPERIMENTS_CSV

REPO_ROOT = Path(__file__).parents[3]  # src/seatau/plot/config.py -> repo root
DEFAULT_CSV_PATH = EXPERIMENTS_CSV
DEFAULT_FIG_DIR = REPO_ROOT / "figs"

EXPORT_FORMATS = ("pdf", "png")
EXPORT_DPI = 400

FILTER_SETTING = {
    "scenario": [
        "english",
        "l2_tools",
        "l2_interaction",
        "l2_domain",
    ],
    "domain": ["airline", "retail", "telecom"],
    "language_senario": [
        "english",
        "chinese",
        "indonesian",
        "thai",
        "vietnamese",
        "filipino",
        "tool_mix_2",
        "tool_mix_3",
        "tool_mix_4",
        "tool_mix_5",
    ],
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
    "english": 1,
    "l2_tools": 2,
    "l2_interaction": 3,
    "l2_domain": 4,
}
SCENARIO_NAME_BY_ID = {value: key for key, value in SCENARIO_ID_BY_NAME.items()}
NON_BASELINE_SCENARIO_ORDER = ["l2_interaction", "l2_tools", "l2_domain"]

LANGUAGE_ORDER = [
    "english",
    "thai",
    "vietnamese",
    "filipino",
    "indonesian",
    "chinese",
]
TOOL_MIX_ORDER = ["tool_mix_2", "tool_mix_3", "tool_mix_4", "tool_mix_5"]

LANGUAGE_LABELS = {
    "english": "EN",
    "chinese": "ZH",
    "indonesian": "ID",
    "thai": "TH",
    "vietnamese": "VI",
    "filipino": "TL",
    "tool_mix_2": "Mix 2",
    "tool_mix_3": "Mix 3",
    "tool_mix_4": "Mix 4",
    "tool_mix_5": "Mix 5",
}
LANGUAGE_DISPLAY_NAMES = {
    "english": "English",
    "chinese": "Chinese",
    "indonesian": "Indonesian",
    "thai": "Thai",
    "vietnamese": "Vietnamese",
    "filipino": "Filipino",
    "tool_mix_2": "Tool Mix 2",
    "tool_mix_3": "Tool Mix 3",
    "tool_mix_4": "Tool Mix 4",
    "tool_mix_5": "Tool Mix 5",
}

MODEL_ORDER = FILTER_SETTING["normalized_agent_llm"]
PLOT_MODEL_KEYS = ["gpt-5-mini", "qwen-3-235b-it"]
FIG6_ALL_MODEL_SCENARIOS = {"l2_interaction", "l2_domain"}
MODEL_LABELS = {
    "gpt-5-mini": "GPT 5 Mini",
    "kimi-k2.5": "Kimi K2.5",
    "qwen-3-235b-it": "Qwen3 235B IT",
}
