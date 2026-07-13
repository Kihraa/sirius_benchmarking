#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BENCH_REPO = Path(__file__).resolve().parents[1]
if str(BENCH_REPO) not in sys.path:
    sys.path.insert(0, str(BENCH_REPO))

from plot.lib.paths import bench_repo, list_runs
from plot.lib.style import apply_style
from plot.plot_scripts import (
    query_timing_heatmap_cold_query_sf,
    query_timing_heatmap_hot_query_sf,
    tpch_timing_heatmap_cold_sweep_sf,
    tpch_timing_heatmap_hot_sweep_sf,
)

PLOTS = {
    query_timing_heatmap_hot_query_sf.PLOT_NAME: query_timing_heatmap_hot_query_sf.generate,
    query_timing_heatmap_cold_query_sf.PLOT_NAME: query_timing_heatmap_cold_query_sf.generate,
    tpch_timing_heatmap_hot_sweep_sf.PLOT_NAME: tpch_timing_heatmap_hot_sweep_sf.generate,
    tpch_timing_heatmap_cold_sweep_sf.PLOT_NAME: tpch_timing_heatmap_cold_sweep_sf.generate,
}

VARIANTS = ("old", "new")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate benchmark figures from results/", add_help=False)
    parser.add_argument("--run", required=True, help="Run name (e.g. run09)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    apply_style()
    repo = bench_repo()
    runs = list_runs(args.run)
    if not runs:
        logging.error("run not found: %s", args.run)
        return 1

    run_name = runs[0]
    written: list[Path] = []

    for variant in VARIANTS:
        if not list_runs(run_name, variant):
            logging.warning("skipping %s/%s: no results", run_name, variant)
            continue
        for plot_name in sorted(PLOTS):
            try:
                paths = PLOTS[plot_name](repo, run_name, variant)
                written.extend(paths)
            except Exception:
                logging.exception("plot %s failed for %s/%s; continuing", plot_name, run_name, variant)

    if not written:
        logging.warning("no figures written")

    print(f"wrote {len(written)} figure(s):")
    for path in written:
        print(f"  {path.relative_to(repo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
