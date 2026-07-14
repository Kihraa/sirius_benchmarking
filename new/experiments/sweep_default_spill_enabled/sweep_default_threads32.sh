#!/usr/bin/env bash
# Sirius defaults, disk spill enabled (/tmp/sirius_spill), pipeline num_threads=32, single-session.
set -euo pipefail

RUN_DIR="$1"
SFS="$2"
ITERS="$3"

BENCH_REPO="${BENCH_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
BENCH="$SIRIUS_REPO/test/tpch_performance/benchmark_and_validate.sh"
CONFIG="$BENCH_REPO/configs/default_spill_enabled/default_threads32.yaml"

OUT="$RUN_DIR/sweep_default_threads32"
mkdir -p "$OUT" /tmp/sirius_spill

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
    --pinning-mode per-query \
    --pin-after-iteration 1 \
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
