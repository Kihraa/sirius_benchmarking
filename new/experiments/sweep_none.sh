#!/usr/bin/env bash
# Baseline Sirius config + DuckDB reference run per SF on Sirius tpchgen-rs parquet (no pinning).
set -euo pipefail

RUN_DIR="$1"
SFS="$2"
ITERS="$3"

BENCH_REPO="${BENCH_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
BENCH="$SIRIUS_REPO/test/tpch_performance/benchmark_and_validate.sh"
CONFIG="$BENCH_REPO/configs/baseline.yaml"

mkdir -p "$RUN_DIR"

for SF in $SFS; do
  parquet_dir="$DATA_DIR/tpch_parquet_sirius_sf${SF}"
  dest="$RUN_DIR/sf${SF}_${ITERS}iter"
  log="$RUN_DIR/sf${SF}.log"
  "$BENCH" \
    --config "$CONFIG" \
    --timeout "${TIMEOUT:-120}" \
    --parquet-dir "$parquet_dir" \
    --iterations "$ITERS" \
    --pinning-mode none \
    "$SF" </dev/null 2>&1 | tee "$log" || true
  src="$(grep -m1 '^Run directory: ' "$log" | sed 's/^Run directory: //')"
  if [ -n "$src" ] && [ -d "$src" ]; then
    cp -r "$src" "$dest" && rm -rf "$src"
    if [ "${NSYS:-0}" = 1 ]; then
      bash "$BENCH_REPO/experiments/run_nsys_profiles.sh" \
        "$dest" "$SF" "$CONFIG" "$parquet_dir" "$ITERS"
    fi
  fi
done
