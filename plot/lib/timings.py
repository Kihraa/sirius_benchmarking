from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

import numpy as np

from plot.lib.paths import DEFAULT_SFS, find_sf_timing_csv, find_sf_validation_csv

QUERIES = tuple(f"Q{i}" for i in range(1, 23))
VALIDATION_MISMATCH = "validation"


def _parse_runtime(value: str) -> float | None:
    value = value.strip()
    if not value or value.upper() == "N/A":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def warm_sirius_times(csv_path: Path) -> dict[str, float]:
    warm: dict[str, list[float]] = {q: [] for q in QUERIES}
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("engine") != "sirius":
                continue
            iteration = int(row["iteration"])
            if iteration == 1:
                continue
            query = row["query"]
            if query not in warm:
                continue
            runtime = _parse_runtime(row["runtime_s"])
            if runtime is None:
                continue
            warm[query].append(runtime)
    return {q: min(times) for q, times in warm.items() if times}


def build_query_sf_matrix(
    sweep_dir: Path,
    sfs: tuple[int, ...] = DEFAULT_SFS,
) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
    row_labels = tuple(f"sf{sf}" for sf in sfs)
    col_labels = QUERIES
    matrix = np.full((len(sfs), len(QUERIES)), np.nan, dtype=float)

    for row_idx, sf in enumerate(sfs):
        csv_path = find_sf_timing_csv(sweep_dir, sf)
        if csv_path is None:
            continue
        times = warm_sirius_times(csv_path)
        for col_idx, query in enumerate(QUERIES):
            if query in times:
                matrix[row_idx, col_idx] = times[query]

    return matrix, row_labels, col_labels


def validation_mismatches(csv_path: Path) -> set[str]:
    mismatches: set[str] = set()
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            query = row.get("query", "")
            status = row.get("status", "").strip()
            if query in QUERIES and status == VALIDATION_MISMATCH:
                mismatches.add(query)
    return mismatches


def build_query_sf_validation_matrix(
    sweep_dir: Path,
    sfs: tuple[int, ...] = DEFAULT_SFS,
) -> np.ndarray:
    matrix = np.zeros((len(sfs), len(QUERIES)), dtype=bool)

    for row_idx, sf in enumerate(sfs):
        csv_path = find_sf_validation_csv(sweep_dir, sf)
        if csv_path is None:
            continue
        mismatches = validation_mismatches(csv_path)
        for col_idx, query in enumerate(QUERIES):
            if query in mismatches:
                matrix[row_idx, col_idx] = True

    return matrix


def warm_sirius_sum_incomplete(csv_path: Path) -> tuple[float | None, bool]:
    times = warm_sirius_times(csv_path)
    incomplete = any(query not in times for query in QUERIES)
    if not times:
        return None, True
    return sum(times.values()), incomplete


def _fraction_token(token: str) -> str:
    if "P" not in token:
        return token
    whole, frac = token.split("P", 1)
    if not frac:
        return whole or "0"
    return str(float(f"{whole or '0'}.{frac}"))


def thread_label(sweep_name: str) -> str:
    prefix = "sweep_default_threads"
    if sweep_name.startswith(prefix):
        return sweep_name[len(prefix) :]
    return sweep_name


def usage_limit_label(sweep_name: str) -> str:
    token = sweep_name.removeprefix("sweep_usage_limit_")
    return _fraction_token(token)


def downgrade_trigger_label(sweep_name: str) -> str:
    body = sweep_name.removeprefix("sweep_trigger_")
    if "_stop_" not in body:
        return body
    trigger, stop = body.split("_stop_", 1)
    return f"{_fraction_token(trigger)}/{_fraction_token(stop)}"


def build_sweep_sf_sum_matrix(
    family_dir: Path,
    sweep_names: tuple[str, ...],
    col_label_fn: Callable[[str], str],
    sfs: tuple[int, ...] = DEFAULT_SFS,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], tuple[str, ...]]:
    row_labels = tuple(f"sf{sf}" for sf in sfs)
    col_labels = tuple(col_label_fn(name) for name in sweep_names)
    matrix = np.full((len(sfs), len(sweep_names)), np.nan, dtype=float)
    incomplete = np.zeros((len(sfs), len(sweep_names)), dtype=bool)

    for col_idx, sweep_name in enumerate(sweep_names):
        sweep_dir = family_dir / sweep_name
        if not sweep_dir.is_dir():
            incomplete[:, col_idx] = True
            continue
        for row_idx, sf in enumerate(sfs):
            csv_path = find_sf_timing_csv(sweep_dir, sf)
            if csv_path is None:
                incomplete[row_idx, col_idx] = True
                continue
            total, inc = warm_sirius_sum_incomplete(csv_path)
            if total is not None:
                matrix[row_idx, col_idx] = total
            incomplete[row_idx, col_idx] = inc

    return matrix, incomplete, row_labels, col_labels


def build_threads_sf_sum_matrix(
    family_dir: Path,
    thread_sweep_names: tuple[str, ...],
    sfs: tuple[int, ...] = DEFAULT_SFS,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], tuple[str, ...]]:
    return build_sweep_sf_sum_matrix(family_dir, thread_sweep_names, thread_label, sfs)
