from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from plot.lib.paths import figure_path_for_sweep, results_root
from plot.lib.style import (
    DEFAULT_FIGSIZE,
    log_blue_cmap,
    log_green_cmap,
    log_norm,
    save_figure,
)
from plot.lib.timings import build_query_sf_matrix, build_query_sf_validation_matrix

logger = logging.getLogger(__name__)

PLOT_NAME = "query_timing_heatmap_query_sf"
TARGET_SWEEP_FAMILY = "sweep_default_spill_enabled"
TARGET_SWEEP_NAMES = (
    "sweep_default_threads1",
    "sweep_default_threads4",
    "sweep_default_threads8",
    "sweep_default_threads16",
)


def generate(bench_repo: Path, run_name: str) -> list[Path]:
    written: list[Path] = []
    family_dir = results_root() / run_name / TARGET_SWEEP_FAMILY
    if not family_dir.is_dir():
        logger.warning("missing sweep family: %s", family_dir)
        return written

    for sweep_name in TARGET_SWEEP_NAMES:
        sweep_dir = family_dir / sweep_name
        if not sweep_dir.is_dir():
            logger.warning("missing sweep dir: %s", sweep_dir)
            continue

        matrix, row_labels, col_labels = build_query_sf_matrix(sweep_dir)
        mismatch = build_query_sf_validation_matrix(sweep_dir)
        if np.all(np.isnan(matrix)):
            logger.warning("no timing data in %s", sweep_dir)
            continue

        out_path = figure_path_for_sweep(sweep_dir, PLOT_NAME)
        _render_heatmap(
            matrix,
            row_labels,
            col_labels,
            mismatch,
            title=f"Sirius warm best time — {run_name} / {TARGET_SWEEP_FAMILY} / {sweep_name}",
            out_path=out_path,
        )
        written.append(out_path)
        logger.info("wrote %s", out_path)

    return written


def _render_heatmap(
    matrix: np.ndarray,
    row_labels: tuple[str, ...],
    col_labels: tuple[str, ...],
    mismatch: np.ndarray,
    title: str,
    out_path: Path,
) -> None:
    row_totals = np.nansum(matrix, axis=1)

    fig = plt.figure(figsize=DEFAULT_FIGSIZE)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[22, 1], wspace=0.05)
    ax_main = fig.add_subplot(gs[0, 0])
    ax_sum = fig.add_subplot(gs[0, 1], sharey=ax_main)

    blue_cmap = log_blue_cmap()
    green_cmap = log_green_cmap()
    blue_norm = log_norm(matrix)
    green_norm = log_norm(row_totals)

    masked = np.ma.masked_invalid(matrix)
    ax_main.imshow(masked, aspect="auto", cmap=blue_cmap, norm=blue_norm, origin="upper")
    ax_main.set_xticks(range(len(col_labels)), col_labels, rotation=90)
    ax_main.set_yticks(range(len(row_labels)), row_labels)
    ax_main.set_xlabel("TPC-H query")
    ax_main.set_ylabel("Scale factor")
    ax_main.set_title(title)

    totals_matrix = row_totals.reshape(-1, 1)
    masked_totals = np.ma.masked_invalid(totals_matrix)
    ax_sum.imshow(masked_totals, aspect="auto", cmap=green_cmap, norm=green_norm, origin="upper")
    ax_sum.set_xticks([0], ["Σ Q"])
    ax_sum.set_yticks([])
    ax_sum.tick_params(axis="x", labelsize=8)

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
                color="red" if mismatch[row, col] else "black",
                fontsize=7,
            )

    for row, value in enumerate(row_totals):
        if np.isnan(value):
            continue
        ax_sum.text(
            0,
            row,
            f"{value:.2f}",
            ha="center",
            va="center",
            color="black",
            fontsize=7,
        )

    save_figure(fig, out_path)
    plt.close(fig)
