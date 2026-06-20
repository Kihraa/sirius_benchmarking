#!/usr/bin/env bash
# Single entry point: generate data, then run benchmark experiments.
set -euo pipefail

BENCH_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export BENCH_REPO
export SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
export DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"

SFS="1 3 10 30 100"
ITERS=5
TIMEOUT=120
export TIMEOUT
NAME=""

while [ $# -gt 0 ]; do
  case "$1" in
    --sf) SFS="${2//,/ }"; shift 2 ;;
    --iterations) ITERS="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; export TIMEOUT; shift 2 ;;
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

BASELINE_RUN_DIR="$RUN_DIR/sweep_baseline"
mkdir -p "$BASELINE_RUN_DIR"
bash "$BENCH_REPO/experiments/sweep_baseline.sh" "$BASELINE_RUN_DIR" "$SFS" "$ITERS"
export DUCKDB_BASELINE_DIR="$BASELINE_RUN_DIR"

EXPERIMENT_DIRS="sweep_default_spill_disabled sweep_default_spill_enabled"
EXPERIMENTS="sweep_default_threads1 sweep_default_threads4 sweep_default_threads8 sweep_default_threads16"
for exp_dir in $EXPERIMENT_DIRS; do
  EXP_RUN_DIR="$RUN_DIR/$exp_dir"
  mkdir -p "$EXP_RUN_DIR"
  for exp in $EXPERIMENTS; do
    bash "$BENCH_REPO/experiments/${exp_dir}/${exp}.sh" "$EXP_RUN_DIR" "$SFS" "$ITERS"
  done
done

USAGE_LIMIT_RUN_DIR="$RUN_DIR/sweep_usage_limit"
mkdir -p "$USAGE_LIMIT_RUN_DIR"
USAGE_LIMIT_EXPS="sweep_usage_limit_0P0 sweep_usage_limit_0P1 sweep_usage_limit_0P5 sweep_usage_limit_0P8 sweep_usage_limit_0P9 sweep_usage_limit_0P95"
for exp in $USAGE_LIMIT_EXPS; do
  bash "$BENCH_REPO/experiments/sweep_usage_limit/${exp}.sh" "$USAGE_LIMIT_RUN_DIR" "$SFS" "$ITERS"
done

DOWNGRADE_TRIGGER_RUN_DIR="$RUN_DIR/sweep_memory_downgrade_trigger"
mkdir -p "$DOWNGRADE_TRIGGER_RUN_DIR"
DOWNGRADE_TRIGGER_EXPS="sweep_trigger_0P0_stop_0P0 sweep_trigger_0P1_stop_0P07 sweep_trigger_0P5_stop_0P35 sweep_trigger_0P9_stop_0P63 sweep_trigger_0P95_stop_0P67 sweep_trigger_1P0_stop_0P7"
for exp in $DOWNGRADE_TRIGGER_EXPS; do
  bash "$BENCH_REPO/experiments/sweep_memory_downgrade_trigger/${exp}.sh" "$DOWNGRADE_TRIGGER_RUN_DIR" "$SFS" "$ITERS"
done
