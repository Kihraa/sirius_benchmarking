#!/usr/bin/env bash
# Single entry point: generate data, then run benchmark experiments.
set -euo pipefail

BENCH_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_REPO="$(cd "$BENCH_REPO/.." && pwd)"
VARIANT=new
export BENCH_REPO ROOT_REPO VARIANT
export SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
export DATA_DIR="${DATA_DIR:-$SIRIUS_REPO/test_datasets}"
SIRIUS_SPILL_DIR="${SIRIUS_SPILL_DIR:-/tmp/sirius_spill}"
export SIRIUS_SPILL_DIR
export SIRIUS_PIN_TIER="${SIRIUS_PIN_TIER:-host}"

SFS="1 3 10 30 100"
ITERS=5
TIMEOUT=120
NSYS=0
export TIMEOUT
NAME=""
SELECTED=""

VALID_EXPERIMENTS="sirius_parquet sweep_baseline sweep_default_spill_disabled sweep_default_spill_enabled sweep_memory_usage_limit sweep_memory_downgrade_trigger"

normalize_experiment() {
  case "$1" in
    sirius_parquet|sirius_parquet/sweep_baseline) echo sirius_parquet ;;
    sweep_baseline) echo sweep_baseline ;;
    sweep_default_spill_disabled) echo sweep_default_spill_disabled ;;
    sweep_default_spill_enabled) echo sweep_default_spill_enabled ;;
    sweep_memory_usage_limit) echo sweep_memory_usage_limit ;;
    sweep_memory_downgrade_trigger) echo sweep_memory_downgrade_trigger ;;
    *) return 1 ;;
  esac
}

add_experiment() {
  local name
  name="$(normalize_experiment "$1")" || {
    echo "unknown experiment: $1" >&2
    echo "valid experiments: $VALID_EXPERIMENTS (alias: sirius_parquet/sweep_baseline)" >&2
    exit 1
  }
  case " $SELECTED " in
    *" $name "*) ;;
    *) SELECTED="${SELECTED:+$SELECTED }$name" ;;
  esac
}

while [ $# -gt 0 ]; do
  case "$1" in
    --sf) SFS="${2//,/ }"; shift 2 ;;
    --iterations) ITERS="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; export TIMEOUT; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --nsys) NSYS=1; shift ;;
    --experiment) add_experiment "$2"; shift 2 ;;
    *) echo "unknown flag: $1" >&2; exit 1 ;;
  esac
done

export NSYS

run_exp() {
  [ -z "$SELECTED" ] && return 0
  case " $SELECTED " in
    *" $1 "*) return 0 ;;
    *) return 1 ;;
  esac
}

if [ -z "$NAME" ]; then
  NAME="$(printf 'run%02d' $(( $(find "$ROOT_REPO/results" -maxdepth 1 -name 'run*' -type d 2>/dev/null | wc -l) + 1 )))"
fi
RUN_DIR="$ROOT_REPO/results/$NAME/$VARIANT"
mkdir -p "$RUN_DIR" "$SIRIUS_SPILL_DIR"

DEFAULT_THREAD_EXPS="sweep_default_threads1 sweep_default_threads4 sweep_default_threads8 sweep_default_threads16"
USAGE_LIMIT_EXPS="sweep_usage_limit_0P0 sweep_usage_limit_0P1 sweep_usage_limit_0P5 sweep_usage_limit_0P8 sweep_usage_limit_0P9 sweep_usage_limit_0P95"
DOWNGRADE_TRIGGER_EXPS="sweep_trigger_0P0_stop_0P0 sweep_trigger_0P1_stop_0P07 sweep_trigger_0P5_stop_0P35 sweep_trigger_0P9_stop_0P63 sweep_trigger_0P95_stop_0P67 sweep_trigger_1P0_stop_0P7"

for SF in $SFS; do
  bash "$BENCH_REPO/test_gen/tpch_duck.sh" "$SF" "$DATA_DIR/tpch_parquet_sf${SF}"
done

if run_exp sirius_parquet; then
  for SF in $SFS; do
    bash "$BENCH_REPO/test_gen/tpch_sirius.sh" "$SF" "$DATA_DIR/tpch_parquet_sirius_sf${SF}"
  done
fi

if run_exp sirius_parquet; then
  SIRIUS_PARQUET_BASELINE="$RUN_DIR/sirius_parquet/sweep_baseline"
  mkdir -p "$SIRIUS_PARQUET_BASELINE"
  bash "$BENCH_REPO/experiments/sirius_parquet/sweep_baseline.sh" \
    "$SIRIUS_PARQUET_BASELINE" "$SFS" "$ITERS"
fi

BASELINE_RUN_DIR="$RUN_DIR/sweep_baseline"
mkdir -p "$BASELINE_RUN_DIR"
bash "$BENCH_REPO/experiments/sweep_baseline.sh" "$BASELINE_RUN_DIR" "$SFS" "$ITERS"
export DUCKDB_BASELINE_DIR="$BASELINE_RUN_DIR"

if run_exp sweep_default_spill_disabled; then
  EXP_RUN_DIR="$RUN_DIR/sweep_default_spill_disabled"
  mkdir -p "$EXP_RUN_DIR"
  for exp in $DEFAULT_THREAD_EXPS; do
    bash "$BENCH_REPO/experiments/sweep_default_spill_disabled/${exp}.sh" "$EXP_RUN_DIR" "$SFS" "$ITERS"
  done
fi

if run_exp sweep_default_spill_enabled; then
  EXP_RUN_DIR="$RUN_DIR/sweep_default_spill_enabled"
  mkdir -p "$EXP_RUN_DIR"
  for exp in $DEFAULT_THREAD_EXPS; do
    bash "$BENCH_REPO/experiments/sweep_default_spill_enabled/${exp}.sh" "$EXP_RUN_DIR" "$SFS" "$ITERS"
  done
fi

if run_exp sweep_memory_usage_limit; then
  USAGE_LIMIT_RUN_DIR="$RUN_DIR/sweep_memory_usage_limit"
  mkdir -p "$USAGE_LIMIT_RUN_DIR"
  for exp in $USAGE_LIMIT_EXPS; do
    bash "$BENCH_REPO/experiments/sweep_memory_usage_limit/${exp}.sh" "$USAGE_LIMIT_RUN_DIR" "$SFS" "$ITERS"
  done
fi

if run_exp sweep_memory_downgrade_trigger; then
  DOWNGRADE_TRIGGER_RUN_DIR="$RUN_DIR/sweep_memory_downgrade_trigger"
  mkdir -p "$DOWNGRADE_TRIGGER_RUN_DIR"
  for exp in $DOWNGRADE_TRIGGER_EXPS; do
    bash "$BENCH_REPO/experiments/sweep_memory_downgrade_trigger/${exp}.sh" "$DOWNGRADE_TRIGGER_RUN_DIR" "$SFS" "$ITERS"
  done
fi
