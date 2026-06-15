"""Shared configuration constants for SEA-TauBench figure scripts.

Column names match experiments_all.csv exactly.
"""

from pathlib import Path

from seatau.paths import EXPERIMENTS_CSV

REPO_ROOT = Path(__file__).parents[3]  # src/seatau/plot/config.py -> repo root
DEFAULT_CSV_PATH = EXPERIMENTS_CSV
DEFAULT_FIG_DIR = REPO_ROOT / "figs"

EXPORT_FORMATS = ("pdf", "png")
EXPORT_DPI = 400

# Scenario values as they appear in experiments_all.csv
FILTER_SETTING = {
    "scenario": [
        "1-english-only",
        "2-multilingual-tools",
        "3-crosslingual",
        "4-translated",
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
        "qwen3-235b-a22b-inst",
        "qwen3.6-35b-a3b",
        "kimi-k2.5",
    ],
}

# Maps CSV column names -> internal metric keys used throughout
METRIC_RENAMES = {
    "pass_hat_1": "pass@1",
    "pass_hat_2": "pass@2",
    "pass_hat_3": "pass@3",
    "rho_3": "rho^3",
    "read_action": "read_actions",
    "write_action": "write_actions",
    "db_match": "db_match",
    "agent_language_correctness": "language_correctness",
}

PRIMARY_METRICS = ["pass@1", "pass@2", "pass@3"]
PAPER_METRICS = ["pass@1", "pass@3"]
FIGURE6_METRICS = ["pass@1", "rho^3"]
FIGURE7_METRICS = ["pass@1", "rho^3"]
ACTION_METRICS = ["read_actions", "write_actions", "db_match", "language_correctness"]

SCENARIO_LABELS = {
    1: "EN Baseline",
    2: "L2 Tools",
    3: "L2 Interaction",
    4: "L2 Domain",
}
NON_BASELINE_SCENARIO_ORDER = [3, 2, 4]

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
PLOT_MODEL_KEYS = ["gpt-5-mini", "qwen3-235b-a22b-inst"]
# In these scenarios, all 4 models are shown (not just the 2-model subset)
FIG6_ALL_MODEL_SCENARIO_IDS = {3, 4}
MODEL_LABELS = {
    "gpt-5-mini": "GPT-5 Mini",
    "kimi-k2.5": "Kimi K2.5",
    "qwen3-235b-a22b-inst": "Qwen3-235B-A22B-INST",
    "qwen3.6-35b-a3b": "Qwen3.6-35B-A3B",
}
