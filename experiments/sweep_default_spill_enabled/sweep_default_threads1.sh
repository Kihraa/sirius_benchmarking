#!/usr/bin/env bash
# Sirius defaults, disk spill enabled (/tmp/sirius_spill), pipeline num_threads=1, multi-session.
set -euo pipefail

RUN_DIR="$1"
SFS="$2"
ITERS="$3"

BENCH_REPO="${BENCH_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius-db/sirius}"
DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
BENCH="$SIRIUS_REPO/test/tpch_performance/benchmark_and_validate.sh"
CONFIG="$BENCH_REPO/configs/default_spill_enabled/default_threads1.yaml"

OUT="$RUN_DIR/sweep_default_spill_enabled_threads1"
mkdir -p "$OUT" /tmp/sirius_spill

for SF in $SFS; do
  log="$OUT/sf${SF}.log"
  "$BENCH" \
    --config "$CONFIG" \
    --iterations "$ITERS" \
    --multi-session \
    "$SF" </dev/null 2>&1 | tee "$log" || true
  src="$(grep -m1 '^Run directory: ' "$log" | sed 's/^Run directory: //')"
  [ -n "$src" ] && [ -d "$src" ] && cp -r "$src" "$OUT/sf${SF}_${ITERS}iter" && rm -rf "$src"
done
