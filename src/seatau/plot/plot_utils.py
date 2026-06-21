"""Matplotlib style setup and shared plot helpers."""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from seatau.constants import ANALYSES_DIR
from seatau.plot.config import (
    EXPORT_DPI,
    EXPORT_FORMATS,
    FILTER_SETTING,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_LABELS,
    LANGUAGE_ORDER,
    METRIC_RENAMES,
    MODEL_LABELS,
    MODEL_ORDER,
    PLOT_BASE_FONT_SIZE,
    PLOT_FONT_FAMILY,
    PLOT_LABEL_SIZE,
    PLOT_LEGEND_SIZE,
    PLOT_TICK_SIZE,
    PLOT_TITLE_SIZE,
    PRIMARY_METRICS,
    SCENARIO_ID_BY_NAME,
    SCENARIO_LABELS,
    SEA_COLORS,
)

matplotlib.use("Agg")

LANGUAGE_PALETTE = {
    "EN": SEA_COLORS["black"],
    "ZH": SEA_COLORS["blue"],
    "ID": SEA_COLORS["yellow"],
    "TH": SEA_COLORS["red"],
    "VI": SEA_COLORS["blue"],
    "TL": SEA_COLORS["yellow"],
}

METRIC_PALETTE = {
    "pass@1": SEA_COLORS["blue"],
    "pass^2": SEA_COLORS["yellow"],
    "pass^3": SEA_COLORS["black"],
    "rho^3": SEA_COLORS["red"],
}

MODEL_PALETTE = dict(
    zip(
        MODEL_ORDER,
        [SEA_COLORS["blue"], SEA_COLORS["red"], SEA_COLORS["yellow"]],
    )
)
INTERACTION_RECAP_PATH = ANALYSES_DIR / "error_breakdown.csv"


def normalize_key_series(series: pd.Series) -> pd.Series:
    """Normalize identifier columns used by plot inputs."""

    return series.astype("string").str.strip().str.lower()


def normalize_scenario_id_series(series: pd.Series) -> pd.Series:
    """Normalize scenario ids to canonical lower-case ids."""

    return normalize_key_series(series)


def normalize_scenario_column(
    df: pd.DataFrame, column: str = "scenario"
) -> pd.DataFrame:
    """Return a copy with a scenario column normalized to canonical ids."""

    if column not in df.columns:
        return df
    out = df.copy()
    out[column] = normalize_scenario_id_series(out[column])
    return out


def read_interaction_recap(path: Path = INTERACTION_RECAP_PATH) -> pd.DataFrame:
    """Read the interaction/domain recap dataset."""

    df = pd.read_csv(path)
    if "language" in df.columns:
        df["language"] = normalize_key_series(df["language"])
    return df


def parse_scenario_id(series: pd.Series) -> pd.Series:
    """Map canonical scenario names to stable numeric ids."""

    return normalize_scenario_id_series(series).map(SCENARIO_ID_BY_NAME).astype("Int64")


def load_and_prepare(
    csv_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Load, normalize, filter, and deduplicate the experiments CSV."""

    raw = pd.read_csv(csv_path)
    raw.columns = [col.strip() for col in raw.columns]
    df = raw.reset_index(names="source_row").copy()

    for csv_col, metric_key in METRIC_RENAMES.items():
        if csv_col in df.columns:
            df[metric_key] = pd.to_numeric(df[csv_col], errors="coerce")
        else:
            df[metric_key] = np.nan

    df["scenario_raw"] = normalize_scenario_id_series(df["scenario"])
    df["scenario_id"] = parse_scenario_id(df["scenario_raw"])
    df["scenario_label"] = (
        df["scenario_raw"].map(SCENARIO_LABELS).fillna(df["scenario_raw"])
    )

    df["domain_key"] = normalize_key_series(df["domain"])
    df["domain_label"] = df["domain_key"].str.title()
    df["language_key"] = normalize_key_series(df["language_senario"])
    df["language_label"] = (
        df["language_key"].map(LANGUAGE_LABELS).fillna(df["language_key"])
    )
    df["language_display"] = (
        df["language_key"].map(LANGUAGE_DISPLAY_NAMES).fillna(df["language_key"])
    )
    df["language_group"] = np.where(
        df["language_key"].str.startswith("tool_mix_", na=False), "tool_mix", "language"
    )
    df["model_key"] = normalize_key_series(df["normalized_agent_llm"])
    df["model_label"] = df["model_key"].map(MODEL_LABELS).fillna(df["model_key"])

    has_primary_metric = df[list(PRIMARY_METRICS)].notna().any(axis=1)
    filter_mask = (
        df["scenario_raw"].isin(FILTER_SETTING["scenario"])
        & df["domain_key"].isin(FILTER_SETTING["domain"])
        & df["language_key"].isin(FILTER_SETTING["language_senario"])
        & df["model_key"].isin(FILTER_SETTING["normalized_agent_llm"])
    )
    with_metrics = df.loc[filter_mask & has_primary_metric].copy()

    dedupe_keys = ["scenario_raw", "domain_key", "language_key", "model_key"]
    duplicate_summary = (
        with_metrics.groupby(dedupe_keys, dropna=False)
        .size()
        .reset_index(name="row_count")
        .query("row_count > 1")
        .sort_values("row_count", ascending=False)
    )
    clean = (
        with_metrics.sort_values("source_row")
        .drop_duplicates(dedupe_keys, keep="last")
        .sort_values("source_row")
        .reset_index(drop=True)
    )

    audit = {
        "raw_rows": len(raw),
        "rows_matching_filter": int(filter_mask.sum()),
        "filtered_rows_with_primary_metrics_before_dedupe": len(with_metrics),
        "clean_rows_after_dedupe": len(clean),
        "duplicate_groups_resolved": len(duplicate_summary),
        "excluded_rows_by_filter_or_missing_metrics": len(df) - len(with_metrics),
    }
    return raw, df, clean, duplicate_summary, audit


def experiment_language_metric_breakdown(
    clean_df: pd.DataFrame,
    metrics: tuple[str, ...] = PRIMARY_METRICS,
) -> pd.DataFrame:
    """Summarize experiment metrics by domain, model, and display language."""

    language_rows = clean_df.loc[clean_df["language_group"].eq("language")].copy()
    long = language_rows.melt(
        id_vars=["domain_label", "model_key", "language_key"],
        value_vars=list(metrics),
        var_name="Metric",
        value_name="value",
    ).dropna(subset=["value"])
    summary = (
        long.groupby(
            ["domain_label", "model_key", "Metric", "language_key"],
            observed=True,
            as_index=False,
        )["value"]
        .mean()
        .pivot_table(
            index=["domain_label", "model_key", "Metric"],
            columns="language_key",
            values="value",
            aggfunc="mean",
        )
        .reindex(columns=LANGUAGE_ORDER)
        .reset_index()
        .rename(columns={"domain_label": "Domain", "model_key": "Model"})
    )
    return summary


def apply_style() -> None:
    """Apply publication-quality rcParams. Call once at script startup."""
    plt.style.use("default")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": EXPORT_DPI,
            "savefig.bbox": "tight",
            "savefig.facecolor": SEA_COLORS["white"],
            "font.family": PLOT_FONT_FAMILY,
            "font.size": PLOT_BASE_FONT_SIZE,
            "figure.facecolor": SEA_COLORS["white"],
            "axes.facecolor": SEA_COLORS["white"],
            "text.color": SEA_COLORS["black"],
            "axes.labelcolor": SEA_COLORS["black"],
            "axes.edgecolor": SEA_COLORS["black"],
            "xtick.color": SEA_COLORS["black"],
            "ytick.color": SEA_COLORS["black"],
            "axes.titlesize": PLOT_TITLE_SIZE,
            "axes.labelsize": PLOT_LABEL_SIZE,
            "xtick.labelsize": PLOT_TICK_SIZE,
            "ytick.labelsize": PLOT_TICK_SIZE,
            "legend.fontsize": PLOT_LEGEND_SIZE,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
            "axes.linewidth": 0.7,
            "grid.linewidth": 0.45,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def despine(ax: plt.Axes) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def save_figure(
    fig: plt.Figure, name: str, fig_dir: Path, formats: tuple[str, ...] = EXPORT_FORMATS
) -> list[Path]:
    """Save fig to fig_dir/<name>.<ext> for each format.

    Args:
        fig: Matplotlib figure to save.
        name: Output filename stem (no extension).
        fig_dir: Directory to write into (created if missing).
        formats: Tuple of file extensions, e.g. ("pdf", "png", "svg").

    Returns:
        List of written paths.
    """
    fig_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for ext in formats:
        out = fig_dir / f"{name}.{ext}"
        fig.savefig(
            out,
            dpi=EXPORT_DPI,
            bbox_inches="tight",
            facecolor=SEA_COLORS["white"],
        )
        saved.append(out)
    print(f"Saved {name}:")
    for p in saved:
        print(f"  {p}")
    return saved
