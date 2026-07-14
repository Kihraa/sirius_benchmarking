#!/usr/bin/env bash
# Sirius defaults but pipeline num_threads=128, multi-session, duckdb parquet.
set -euo pipefail

RUN_DIR="$1"
SFS="$2"
ITERS="$3"

BENCH_REPO="${BENCH_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius-db/sirius}"
DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
BENCH="$SIRIUS_REPO/test/tpch_performance/benchmark_and_validate.sh"
CONFIG="$BENCH_REPO/configs/default_spill_disabled/default_threads128.yaml"

OUT="$RUN_DIR/sweep_default_threads128"
mkdir -p "$OUT"

for SF in $SFS; do
  parquet_dir="$DATA_DIR/tpch_parquet_sf${SF}"
  dest="$OUT/sf${SF}_${ITERS}iter"
  log="$OUT/sf${SF}.log"
  DUCKDB_BASELINE="${DUCKDB_BASELINE_DIR:?}/sf${SF}_${ITERS}iter"
  "$BENCH" \
    --config "$CONFIG" \
    --timeout "${TIMEOUT:-120}" \
    --duckdb-results "$DUCKDB_BASELINE" \
    --parquet-dir "$parquet_dir" \
    --iterations "$ITERS" \
    --multi-session \
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
