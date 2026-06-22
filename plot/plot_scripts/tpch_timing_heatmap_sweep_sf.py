from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from plot.lib.paths import figure_path_for_sweep, results_root
from plot.lib.style import log_blue_cmap, log_green_cmap, log_norm, save_figure
from plot.lib.timings import build_threads_sf_sum_matrix

logger = logging.getLogger(__name__)

PLOT_NAME = "tpch_timing_heatmap_sweep_sf"
TARGET_FAMILY = "sweep_default_spill_enabled"
THREAD_SWEEP_NAMES = (
    "sweep_default_threads1",
    "sweep_default_threads4",
    "sweep_default_threads8",
    "sweep_default_threads16",
)
FIGSIZE = (8, 5)


def generate(bench_repo: Path, run_name: str) -> list[Path]:
    written: list[Path] = []
    family_dir = results_root() / run_name / TARGET_FAMILY
    if not family_dir.is_dir():
        logger.warning("missing sweep family: %s", family_dir)
        return written

    matrix, incomplete, row_labels, col_labels = build_threads_sf_sum_matrix(family_dir, THREAD_SWEEP_NAMES)
    if np.all(np.isnan(matrix)):
        logger.warning("no timing data in %s", family_dir)
        return written

    out_path = figure_path_for_sweep(family_dir, PLOT_NAME)
    _render_heatmap(
        matrix,
        row_labels,
        col_labels,
        incomplete,
        title=f"Sirius warm best time (Σ Q1–Q22) — {run_name} / {TARGET_FAMILY}",
        out_path=out_path,
    )
    written.append(out_path)
    logger.info("wrote %s", out_path)
    return written


def _render_heatmap(
    matrix: np.ndarray,
    row_labels: tuple[str, ...],
    col_labels: tuple[str, ...],
    incomplete: np.ndarray,
    title: str,
    out_path: Path,
) -> None:
    col_totals = np.nansum(matrix, axis=0)

    fig = plt.figure(figsize=FIGSIZE)
    gs = GridSpec(2, 1, figure=fig, height_ratios=[5, 1], hspace=0.05)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_sum = fig.add_subplot(gs[1, 0], sharex=ax_main)

    blue_cmap = log_blue_cmap()
    green_cmap = log_green_cmap()
    blue_norm = log_norm(matrix)
    green_norm = log_norm(col_totals)

    masked = np.ma.masked_invalid(matrix)
    ax_main.imshow(masked, aspect="auto", cmap=blue_cmap, norm=blue_norm, origin="upper")
    ax_main.set_xticks(range(len(col_labels)), col_labels)
    ax_main.set_yticks(range(len(row_labels)), row_labels)
    ax_main.set_ylabel("Scale factor")
    ax_main.set_title(title)
    ax_main.tick_params(axis="x", labelbottom=False)

    totals_matrix = col_totals.reshape(1, -1)
    masked_totals = np.ma.masked_invalid(totals_matrix)
    ax_sum.imshow(masked_totals, aspect="auto", cmap=green_cmap, norm=green_norm, origin="upper")
    ax_sum.set_yticks([0], ["Σ SF"])
    ax_sum.set_xticks(range(len(col_labels)), col_labels)
    ax_sum.set_xlabel("Threads")
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
