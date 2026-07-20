from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from plot.lib.paths import DEFAULT_SFS, figure_path_for_sweep, find_sf_validation_csv, results_root
from plot.lib.style import (
    BAR_LINEWIDTH,
    BAR_MISMATCH,
    BAR_OUTLINE,
    DEFAULT_FIGSIZE,
    DUCKDB_BAR_FACE,
    DUCKDB_HATCH,
    SIRIUS_BAR_FACE,
    SIRIUS_FAILED_COLOR,
    SIRIUS_FAILED_MARKER,
    SIRIUS_FAILED_MARKERSIZE,
    SIRIUS_HATCH,
    save_figure,
)
from plot.lib.timings import QUERIES, build_query_engine_times, sirius_failures, validation_mismatches

logger = logging.getLogger(__name__)

PLOT_NAME = "query_timing_bar_hot"
TITLE_PREFIX = "Sirius vs DuckDB hot best time"
TARGETS = (
    ("sweep_baseline", None),
    ("sirius_parquet/sweep_baseline", None),
)


def generate_query_bars(
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

            for sf in DEFAULT_SFS:
                sirius_times, duckdb_times = build_query_engine_times(sweep_dir, sf, hot=hot)
                if not sirius_times and not duckdb_times:
                    logger.warning("no timing data in %s sf%d", sweep_dir, sf)
                    continue

                mismatches: set[str] = set()
                failures: set[str] = set()
                validation_csv = find_sf_validation_csv(sweep_dir, sf)
                if validation_csv is not None:
                    mismatches = validation_mismatches(validation_csv)
                    failures = sirius_failures(validation_csv)
                for query in QUERIES:
                    if query not in sirius_times:
                        failures.add(query)

                out_path = figure_path_for_sweep(sweep_dir, f"{plot_name}_sf{sf}")
                _render_bars(
                    sirius_times,
                    duckdb_times,
                    mismatches,
                    failures,
                    title=f"{title_prefix} — {run_name} / {family} / sf{sf}",
                    out_path=out_path,
                )
                written.append(out_path)
                logger.info("wrote %s", out_path)

    return written


def generate(bench_repo: Path, run_name: str, variant: str) -> list[Path]:
    return generate_query_bars(
        run_name,
        variant,
        hot=True,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )


def _render_bars(
    sirius_times: dict[str, float],
    duckdb_times: dict[str, float],
    mismatches: set[str],
    failures: set[str],
    title: str,
    out_path: Path,
) -> None:
    x = np.arange(len(QUERIES))
    width = 0.35

    sirius_values = [sirius_times.get(q, np.nan) for q in QUERIES]
    duckdb_values = [duckdb_times.get(q, np.nan) for q in QUERIES]

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    sirius_bars = ax.bar(
        x - width / 2,
        sirius_values,
        width,
        facecolor=SIRIUS_BAR_FACE,
        edgecolor=BAR_OUTLINE,
        hatch=SIRIUS_HATCH,
        linewidth=BAR_LINEWIDTH,
    )
    ax.bar(
        x + width / 2,
        duckdb_values,
        width,
        facecolor=DUCKDB_BAR_FACE,
        edgecolor=BAR_OUTLINE,
        hatch=DUCKDB_HATCH,
        linewidth=BAR_LINEWIDTH,
    )

    for bar, query in zip(sirius_bars, QUERIES):
        if query in mismatches and query not in failures and not np.isnan(bar.get_height()):
            bar.set_edgecolor(BAR_MISMATCH)

    for idx, query in enumerate(QUERIES):
        if query not in failures:
            continue
        ax.plot(
            x[idx] - width / 2,
            0,
            marker=SIRIUS_FAILED_MARKER,
            color=SIRIUS_FAILED_COLOR,
            markersize=SIRIUS_FAILED_MARKERSIZE,
            linestyle="none",
            clip_on=False,
            zorder=5,
        )

    ax.set_xticks(x, QUERIES, rotation=90)
    ax.set_xlabel("TPC-H query")
    ax.set_ylabel("Time (s)")
    ax.set_title(title)
    legend_handles = [
        Patch(
            facecolor=SIRIUS_BAR_FACE,
            edgecolor=BAR_OUTLINE,
            hatch=SIRIUS_HATCH,
            linewidth=BAR_LINEWIDTH,
            label="Sirius",
        ),
        Patch(
            facecolor=DUCKDB_BAR_FACE,
            edgecolor=BAR_OUTLINE,
            hatch=DUCKDB_HATCH,
            linewidth=BAR_LINEWIDTH,
            label="DuckDB",
        ),
    ]
    if failures:
        legend_handles.append(
            Line2D(
                [],
                [],
                marker=SIRIUS_FAILED_MARKER,
                color=SIRIUS_FAILED_COLOR,
                linestyle="none",
                markersize=SIRIUS_FAILED_MARKERSIZE,
                label="Sirius failed",
            )
        )
    ax.legend(handles=legend_handles)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    save_figure(fig, out_path)
    plt.close(fig)
