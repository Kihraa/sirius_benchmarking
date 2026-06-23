#!/usr/bin/env bash
# Baseline Sirius config + DuckDB reference run per SF on Sirius tpchgen-rs parquet.
set -euo pipefail

RUN_DIR="$1"
SFS="$2"
ITERS="$3"

BENCH_REPO="${BENCH_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
BENCH="$SIRIUS_REPO/test/tpch_performance/benchmark_and_validate.sh"
CONFIG="$BENCH_REPO/configs/baseline.yaml"

mkdir -p "$RUN_DIR"

for SF in $SFS; do
  log="$RUN_DIR/sf${SF}.log"
  "$BENCH" \
    --config "$CONFIG" \
    --timeout "${TIMEOUT:-120}" \
    --parquet-dir "$DATA_DIR/tpch_parquet_sirius_sf${SF}" \
    --iterations "$ITERS" \
    --multi-session \
    "$SF" </dev/null 2>&1 | tee "$log" || true
  src="$(grep -m1 '^Run directory: ' "$log" | sed 's/^Run directory: //')"
  [ -n "$src" ] && [ -d "$src" ] && cp -r "$src" "$RUN_DIR/sf${SF}_${ITERS}iter" && rm -rf "$src"
done
