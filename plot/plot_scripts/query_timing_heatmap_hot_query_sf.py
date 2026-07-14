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

PLOT_NAME = "query_timing_heatmap_hot_query_sf"
TITLE_PREFIX = "Sirius hot best time"
THREAD_SWEEP_NAMES = (
    "sweep_default_threads1",
    "sweep_default_threads4",
    "sweep_default_threads8",
    "sweep_default_threads16",
    "sweep_default_threads32",
    "sweep_default_threads64",
    "sweep_default_threads128",
)
USAGE_LIMIT_SWEEP_NAMES = (
    "sweep_usage_limit_0P1",
    "sweep_usage_limit_0P3",
    "sweep_usage_limit_0P5",
    "sweep_usage_limit_0P7",
    "sweep_usage_limit_0P9",
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
    ("sweep_default_spill_disabled", THREAD_SWEEP_NAMES),
    ("sweep_default_spill_enabled", THREAD_SWEEP_NAMES),
    ("sweep_baseline", None),
    ("sirius_parquet/sweep_baseline", None),
    ("sweep_memory_usage_limit", USAGE_LIMIT_SWEEP_NAMES),
    ("sweep_memory_downgrade_trigger", DOWNGRADE_TRIGGER_SWEEP_NAMES),
)


def _heatmap_title(
    run_name: str,
    family: str,
    sweep_dir: Path,
    sweep_names: tuple[str, ...] | None,
    title_prefix: str,
) -> str:
    if sweep_names is None:
        return f"{title_prefix} — {run_name} / {family}"
    return f"{title_prefix} — {run_name} / {family} / {sweep_dir.name}"


def generate_query_heatmaps(
    run_name: str,
    variant: str,
    *,
    hot: bool,
    plot_name: str,
    title_prefix: str,
) -> list[Path]:
    written: list[Path] = []

    for family, sweep_names in TARGETS:
        family_dir = results_root() / run_name / variant / family
        if not family_dir.is_dir():
            logger.warning("missing sweep family: %s", family_dir)
            continue

        sweep_dirs = [family_dir] if sweep_names is None else [family_dir / name for name in sweep_names]

        for sweep_dir in sweep_dirs:
            if not sweep_dir.is_dir():
                logger.warning("missing sweep dir: %s", sweep_dir)
                continue

            matrix, row_labels, col_labels = build_query_sf_matrix(sweep_dir, hot=hot)
            mismatch = build_query_sf_validation_matrix(sweep_dir)
            if np.all(np.isnan(matrix)):
                logger.warning("no timing data in %s", sweep_dir)
                continue

            out_path = figure_path_for_sweep(sweep_dir, plot_name)
            _render_heatmap(
                matrix,
                row_labels,
                col_labels,
                mismatch,
                title=_heatmap_title(run_name, family, sweep_dir, sweep_names, title_prefix),
                out_path=out_path,
            )
            written.append(out_path)
            logger.info("wrote %s", out_path)

    return written


def generate(bench_repo: Path, run_name: str, variant: str) -> list[Path]:
    return generate_query_heatmaps(
        run_name,
        variant,
        hot=True,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )


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
    ax_main.set_xlabel("TPC-H query")
    ax_main.set_ylabel("Scale factor")
    ax_main.set_title(title)

    totals_matrix = row_totals.reshape(-1, 1)
    masked_totals = np.ma.masked_invalid(totals_matrix)
    ax_sum.imshow(masked_totals, aspect="auto", cmap=green_cmap, norm=green_norm, origin="upper")
    ax_sum.set_xticks([0], ["Σ Q"])
    ax_sum.set_yticks([])
    ax_sum.tick_params(axis="x", labelsize=8)
    ax_main.set_yticks(range(len(row_labels)), row_labels)
    ax_sum.tick_params(axis="y", left=False, right=False, labelleft=False, labelright=False)

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
