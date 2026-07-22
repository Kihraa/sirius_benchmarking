from __future__ import annotations

import csv
import re
from pathlib import Path

from plot.lib.paths import find_sf_iter_dir, find_sf_timing_csv
from plot.lib.timings import QUERIES

EXECUTE_QUERY_RE = re.compile(r"Execute query time: ([0-9.]+) ms")


def find_query_sirius_log(iter_dir: Path, query: str) -> Path | None:
    qdir = iter_dir / "sirius" / query.lower()
    if not qdir.is_dir():
        return None
    logs = sorted(qdir.glob("sirius_*.log"))
    return logs[0] if logs else None


def parse_execute_query_times(log_path: Path) -> list[float]:
    times: list[float] = []
    with log_path.open() as handle:
        for line in handle:
            match = EXECUTE_QUERY_RE.search(line)
            if match:
                times.append(float(match.group(1)) / 1000.0)
    return times


def sirius_iteration_totals(csv_path: Path, query: str) -> dict[int, float]:
    totals: dict[int, float] = {}
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("engine") != "sirius" or row.get("query") != query:
                continue
            runtime = row.get("runtime_s", "").strip()
            if not runtime or runtime.upper() == "N/A":
                continue
            try:
                totals[int(row["iteration"])] = float(runtime)
            except ValueError:
                continue
    return totals


def select_iteration(totals: dict[int, float], *, hot: bool) -> int | None:
    if not totals:
        return None
    if not hot:
        return 1 if 1 in totals else None
    warm = {iteration: runtime for iteration, runtime in totals.items() if iteration > 1}
    if not warm:
        return None
    return min(warm, key=warm.get)


def query_gpu_transfer_breakdown(
    csv_path: Path,
    log_path: Path,
    query: str,
    *,
    hot: bool,
) -> tuple[float, float] | None:
    totals = sirius_iteration_totals(csv_path, query)
    iteration = select_iteration(totals, hot=hot)
    if iteration is None:
        return None

    total = totals.get(iteration)
    if total is None:
        return None

    execute_times = parse_execute_query_times(log_path)
    index = iteration - 1
    if index < 0 or index >= len(execute_times):
        return None

    gpu = execute_times[index]
    transfer = max(total - gpu, 0.0)
    return gpu, transfer


def build_query_gpu_transfer_times(
    sweep_dir: Path,
    sf: int,
    *,
    hot: bool,
) -> tuple[dict[str, float], dict[str, float]]:
    iter_dir = find_sf_iter_dir(sweep_dir, sf)
    csv_path = find_sf_timing_csv(sweep_dir, sf)
    if iter_dir is None or csv_path is None:
        return {}, {}

    gpu_times: dict[str, float] = {}
    transfer_times: dict[str, float] = {}

    for query in QUERIES:
        log_path = find_query_sirius_log(iter_dir, query)
        if log_path is None:
            continue
        breakdown = query_gpu_transfer_breakdown(csv_path, log_path, query, hot=hot)
        if breakdown is None:
            continue
        gpu, transfer = breakdown
        gpu_times[query] = gpu
        transfer_times[query] = transfer

    return gpu_times, transfer_times
