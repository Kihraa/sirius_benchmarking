from __future__ import annotations

from pathlib import Path

from plot.plot_scripts.query_timing_bar_hot_usage_limit import generate_usage_limit_bars

PLOT_NAME = "query_timing_bar_cold_usage_limit"
TITLE_PREFIX = "Sirius memory usage limit cold time"


def generate(bench_repo: Path, run_name: str, variant: str) -> list[Path]:
    return generate_usage_limit_bars(
        run_name,
        variant,
        hot=False,
        plot_name=PLOT_NAME,
        title_prefix=TITLE_PREFIX,
    )
