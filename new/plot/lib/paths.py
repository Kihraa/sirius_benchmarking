from __future__ import annotations

import re
from pathlib import Path

DEFAULT_SFS = (1, 3, 10, 30, 100)


def bench_repo() -> Path:
    return Path(__file__).resolve().parents[2]


def results_root() -> Path:
    return bench_repo() / "results"


def figures_root() -> Path:
    return bench_repo() / "figures"


def list_runs(run: str | None = None) -> list[str]:
    root = results_root()
    if not root.is_dir():
        return []
    if run is not None:
        return [run] if (root / run).is_dir() else []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and re.fullmatch(r"run\d+", p.name))


def figure_path_for_sweep(sweep_dir: Path, plot_name: str, ext: str = ".png") -> Path:
    repo = bench_repo()
    rel = sweep_dir.resolve().relative_to((repo / "results").resolve())
    return figures_root() / rel / f"{plot_name}{ext}"


def find_sf_iter_dir(sweep_dir: Path, sf: int) -> Path | None:
    pattern = f"sf{sf}_*iter"
    for child in sorted(sweep_dir.glob(pattern)):
        if child.is_dir():
            return child
    return None


def find_sf_timing_csv(sweep_dir: Path, sf: int) -> Path | None:
    iter_dir = find_sf_iter_dir(sweep_dir, sf)
    if iter_dir is None:
        return None
    csv_path = iter_dir / "timings.csv"
    return csv_path if csv_path.is_file() else None


def find_sf_validation_csv(sweep_dir: Path, sf: int) -> Path | None:
    iter_dir = find_sf_iter_dir(sweep_dir, sf)
    if iter_dir is None:
        return None
    csv_path = iter_dir / "validation.csv"
    return csv_path if csv_path.is_file() else None
