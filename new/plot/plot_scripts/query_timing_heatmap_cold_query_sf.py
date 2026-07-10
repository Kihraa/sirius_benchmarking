from __future__ import annotations

from pathlib import Path

from plot.plot_scripts.query_timing_heatmap_hot_query_sf import generate_query_heatmaps

PLOT_NAME = "query_timing_heatmap_cold_query_sf"
TITLE_PREFIX = "Sirius cold time"


def generate(bench_repo: Path, run_name: str) -> list[Path]:
    return generate_query_heatmaps(
        run_name,
        hot=False,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )
