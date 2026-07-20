from __future__ import annotations

from pathlib import Path

from plot.plot_scripts.query_timing_bar_hot_query_sf import generate_query_bars

PLOT_NAME = "query_timing_bar_cold"
TITLE_PREFIX = "Sirius vs DuckDB cold time"


def generate(bench_repo: Path, run_name: str, variant: str) -> list[Path]:
    return generate_query_bars(
        run_name,
        variant,
        hot=False,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )
