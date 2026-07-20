from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm

DEFAULT_DPI = 150
DEFAULT_FIGSIZE = (15, 5)
MISSING_COLOR = "#eeeeee"

SIRIUS_BAR_FACE = "#9ec5e8"
DUCKDB_BAR_FACE = "#d4c4e8"
BAR_OUTLINE = "black"
BAR_MISMATCH = "red"
SIRIUS_HATCH = "/"
DUCKDB_HATCH = "-"
BAR_LINEWIDTH = 0.8
SIRIUS_FAILED_MARKER = "x"
SIRIUS_FAILED_COLOR = "black"
SIRIUS_FAILED_MARKERSIZE = 8


def log_blue_cmap() -> LinearSegmentedColormap:
    cmap = LinearSegmentedColormap.from_list(
        "log_blue",
        ["#ffffff", "#d6ebff", "#6eb5ff", "#3d8fd9"],
        N=256,
    )
    cmap.set_bad(color=MISSING_COLOR)
    return cmap


def log_green_cmap() -> LinearSegmentedColormap:
    cmap = LinearSegmentedColormap.from_list(
        "log_green",
        ["#ffffff", "#d6f0d6", "#7dd67d", "#3da63d"],
        N=256,
    )
    cmap.set_bad(color=MISSING_COLOR)
    return cmap


def log_norm(values: np.ndarray, floor: float = 1e-3) -> LogNorm:
    positive = values[np.isfinite(values) & (values > 0)]
    if positive.size == 0:
        return LogNorm(vmin=floor, vmax=floor * 10)
    vmin = max(float(np.min(positive)), floor)
    vmax = float(np.max(positive))
    if vmax <= vmin:
        vmax = vmin * 10
    return LogNorm(vmin=vmin, vmax=vmax)


def annotation_color(value: float, norm: LogNorm) -> str:
    if value <= 0:
        return "black"
    log_pos = (np.log10(value) - np.log10(norm.vmin)) / (np.log10(norm.vmax) - np.log10(norm.vmin))
    return "white" if log_pos > 0.55 else "black"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": DEFAULT_DPI,
            "savefig.dpi": DEFAULT_DPI,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
