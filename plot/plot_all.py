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
from plot.plot_scripts import query_timing_heatmap_sf_query

PLOTS = {
    query_timing_heatmap_sf_query.PLOT_NAME: query_timing_heatmap_sf_query.generate,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate benchmark figures from results/")
    parser.add_argument("--run", help="Run name (e.g. run09). Default: all runs in results/")
    parser.add_argument(
        "--plot",
        action="append",
        dest="plots",
        choices=sorted(PLOTS),
        help="Plot to generate (repeatable). Default: all registered plots.",
    )
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
        logging.error("no runs found%s", f" for {args.run!r}" if args.run else "")
        return 1

    plot_names = args.plots or sorted(PLOTS)
    written: list[Path] = []

    for run_name in runs:
        for plot_name in plot_names:
            paths = PLOTS[plot_name](repo, run_name)
            written.extend(paths)

    if not written:
        logging.warning("no figures written")
        return 1

    print(f"wrote {len(written)} figure(s):")
    for path in written:
        print(f"  {path.relative_to(repo)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
