from __future__ import annotations

from pathlib import Path

from plot.plot_scripts.tpch_timing_heatmap_hot_sweep_sf import generate_tpch_heatmaps

PLOT_NAME = "tpch_timing_heatmap_cold_sweep_sf"
TITLE_PREFIX = "Sirius cold time (Σ Q1–Q22)"


def generate(bench_repo: Path, run_name: str) -> list[Path]:
    return generate_tpch_heatmaps(
        run_name,
        hot=False,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )
