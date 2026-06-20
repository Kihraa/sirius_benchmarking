#!/usr/bin/env bash
# Single entry point: generate data, then run benchmark experiments.
set -euo pipefail

BENCH_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BENCH_REPO
export SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
export DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"

SFS="1 3 10 30 100"
ITERS=5
NAME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --sf) SFS="${2//,/ }"; shift 2 ;;
    --iterations) ITERS="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$NAME" ]; then
  NAME="$(printf 'run%02d' $(( $(find "$BENCH_REPO/results" -maxdepth 1 -name 'run*' -type d 2>/dev/null | wc -l) + 1 )))"
fi
RUN_DIR="$BENCH_REPO/results/$NAME"
mkdir -p "$RUN_DIR"

for SF in $SFS; do
  bash "$BENCH_REPO/test_gen/tpch_duck.sh" "$SF" "$DATA_DIR/tpch_parquet_sf${SF}"
done

EXPERIMENT_DIRS="sweep_default_spill_disabled sweep_default_spill_enabled"
EXPERIMENTS="sweep_default_threads1 sweep_default_threads4 sweep_default_threads8 sweep_default_threads16"
for exp_dir in $EXPERIMENT_DIRS; do
  for exp in $EXPERIMENTS; do
    bash "$BENCH_REPO/experiments/${exp_dir}/${exp}.sh" "$RUN_DIR" "$SFS" "$ITERS"
  done
done
