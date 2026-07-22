from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot.lib.paths import DEFAULT_SFS, figure_path_for_sweep, results_root
from plot.lib.style import BAR_LINEWIDTH, BAR_OUTLINE, DEFAULT_FIGSIZE, save_figure
from plot.lib.timings import QUERIES, build_usage_limit_query_times

logger = logging.getLogger(__name__)

PLOT_NAME = "query_timing_bar_hot_usage_limit"
TITLE_PREFIX = "Sirius memory usage limit hot best time"
FAMILY = "sweep_memory_usage_limit"
LIMIT_COLORS = ("#d6ebff", "#9ec5e8", "#6eb5ff", "#3d8fd9", "#1f5f99")


def generate_usage_limit_bars(
    run_name: str,
    variant: str,
    *,
    hot: bool,
    plot_name: str,
    title_prefix: str,
) -> list[Path]:
    written: list[Path] = []
    family_dir = results_root() / run_name / variant / FAMILY
    if not family_dir.is_dir():
        logger.warning("missing sweep family: %s", family_dir)
        return written

    for sf in DEFAULT_SFS:
        times, limit_labels = build_usage_limit_query_times(family_dir, sf, hot=hot)
        if not any(times[query] for query in QUERIES):
            logger.warning("no timing data in %s sf%d", family_dir, sf)
            continue

        out_path = figure_path_for_sweep(family_dir, f"{plot_name}_sf{sf}")
        _render_usage_limit_bars(
            times,
            limit_labels,
            title=f"{title_prefix} — {run_name} / {FAMILY} / sf{sf}",
            out_path=out_path,
        )
        written.append(out_path)
        logger.info("wrote %s", out_path)

    return written


def generate(bench_repo: Path, run_name: str, variant: str) -> list[Path]:
    return generate_usage_limit_bars(
        run_name,
        variant,
        hot=True,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )


def _render_usage_limit_bars(
    times: dict[str, dict[str, float]],
    limit_labels: tuple[str, ...],
    title: str,
    out_path: Path,
) -> None:
    x = np.arange(len(QUERIES))
    n_limits = len(limit_labels)
    width = 0.8 / n_limits
    offsets = (np.arange(n_limits) - (n_limits - 1) / 2) * width

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    for idx, label in enumerate(limit_labels):
        values = [times[query].get(label, np.nan) for query in QUERIES]
        color = LIMIT_COLORS[idx % len(LIMIT_COLORS)]
        ax.bar(
            x + offsets[idx],
            values,
            width,
            label=label,
            facecolor=color,
            edgecolor=BAR_OUTLINE,
            linewidth=BAR_LINEWIDTH,
        )

    ax.set_xticks(x, QUERIES, rotation=90)
    ax.set_xlabel("TPC-H query")
    ax.set_ylabel("Time (s)")
    ax.set_title(title)
    ax.legend(title="Usage limit", ncol=n_limits)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    save_figure(fig, out_path)
    plt.close(fig)
