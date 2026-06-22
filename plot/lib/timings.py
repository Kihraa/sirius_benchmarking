from __future__ import annotations

import csv
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
    row_labels = tuple(f"SF{sf}" for sf in sfs)
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
