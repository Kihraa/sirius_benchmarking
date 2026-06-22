from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from plot.lib.paths import figure_path_for_sweep, results_root
from plot.lib.style import log_blue_cmap, log_green_cmap, log_norm, save_figure
from plot.lib.timings import (
    build_sweep_sf_sum_matrix,
    downgrade_trigger_label,
    thread_label,
    usage_limit_label,
)

logger = logging.getLogger(__name__)

PLOT_NAME = "tpch_timing_heatmap_sweep_sf"
THREAD_SWEEP_NAMES = (
    "sweep_default_threads1",
    "sweep_default_threads4",
    "sweep_default_threads8",
    "sweep_default_threads16",
)
USAGE_LIMIT_SWEEP_NAMES = (
    "sweep_usage_limit_0P0",
    "sweep_usage_limit_0P1",
    "sweep_usage_limit_0P5",
    "sweep_usage_limit_0P8",
    "sweep_usage_limit_0P9",
    "sweep_usage_limit_0P95",
)
DOWNGRADE_TRIGGER_SWEEP_NAMES = (
    "sweep_trigger_0P0_stop_0P0",
    "sweep_trigger_0P1_stop_0P07",
    "sweep_trigger_0P5_stop_0P35",
    "sweep_trigger_0P9_stop_0P63",
    "sweep_trigger_0P95_stop_0P67",
    "sweep_trigger_1P0_stop_0P7",
)
TARGETS = (
    ("sweep_default_spill_disabled", THREAD_SWEEP_NAMES, "Threads", thread_label),
    ("sweep_default_spill_enabled", THREAD_SWEEP_NAMES, "Threads", thread_label),
    ("sweep_memory_usage_limit", USAGE_LIMIT_SWEEP_NAMES, "Usage limit", usage_limit_label),
    ("sweep_memory_downgrade_trigger", DOWNGRADE_TRIGGER_SWEEP_NAMES, "Downgrade trigger", downgrade_trigger_label),
)


def generate(bench_repo: Path, run_name: str) -> list[Path]:
    written: list[Path] = []

    for family, sweep_names, x_label, col_label_fn in TARGETS:
        family_dir = results_root() / run_name / family
        if not family_dir.is_dir():
            logger.warning("missing sweep family: %s", family_dir)
            continue

        matrix, incomplete, row_labels, col_labels = build_sweep_sf_sum_matrix(
            family_dir, sweep_names, col_label_fn
        )
        if np.all(np.isnan(matrix)):
            logger.warning("no timing data in %s", family_dir)
            continue

        out_path = figure_path_for_sweep(family_dir, PLOT_NAME)
        _render_heatmap(
            matrix,
            row_labels,
            col_labels,
            incomplete,
            x_label=x_label,
            title=f"Sirius warm best time (Σ Q1–Q22) — {run_name} / {family}",
            out_path=out_path,
        )
        written.append(out_path)
        logger.info("wrote %s", out_path)

    return written


def _figsize(n_cols: int) -> tuple[float, float]:
    return (max(8.0, 1.5 * n_cols), 5.0)


def _render_heatmap(
    matrix: np.ndarray,
    row_labels: tuple[str, ...],
    col_labels: tuple[str, ...],
    incomplete: np.ndarray,
    x_label: str,
    title: str,
    out_path: Path,
) -> None:
    col_totals = np.nansum(matrix, axis=0)
    rotate_xticks = any("/" in label for label in col_labels)

    fig = plt.figure(figsize=_figsize(len(col_labels)))
    gs = GridSpec(2, 1, figure=fig, height_ratios=[5, 1], hspace=0.05)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_sum = fig.add_subplot(gs[1, 0], sharex=ax_main)

    blue_cmap = log_blue_cmap()
    green_cmap = log_green_cmap()
    blue_norm = log_norm(matrix)
    green_norm = log_norm(col_totals)

    masked = np.ma.masked_invalid(matrix)
    ax_main.imshow(masked, aspect="auto", cmap=blue_cmap, norm=blue_norm, origin="upper")
    ax_main.set_xticks(range(len(col_labels)), col_labels, rotation=45 if rotate_xticks else 0, ha="right")
    ax_main.set_yticks(range(len(row_labels)), row_labels)
    ax_main.set_ylabel("Scale factor")
    ax_main.set_title(title)
    ax_main.tick_params(axis="x", labelbottom=False)

    totals_matrix = col_totals.reshape(1, -1)
    masked_totals = np.ma.masked_invalid(totals_matrix)
    ax_sum.imshow(masked_totals, aspect="auto", cmap=green_cmap, norm=green_norm, origin="upper")
    ax_sum.set_yticks([0], ["Σ SF"])
    ax_sum.set_xticks(range(len(col_labels)), col_labels, rotation=45 if rotate_xticks else 0, ha="right")
    ax_sum.set_xlabel(x_label)
    ax_sum.tick_params(axis="y", labelsize=8)

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix[row, col]
            if np.isnan(value):
                continue
            ax_main.text(
                col,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                color="red" if incomplete[row, col] else "black",
                fontsize=7,
            )

    for col, value in enumerate(col_totals):
        if np.isnan(value):
            continue
        ax_sum.text(
            col,
            0,
            f"{value:.2f}",
            ha="center",
            va="center",
            color="black",
            fontsize=7,
        )

    save_figure(fig, out_path)
    plt.close(fig)
