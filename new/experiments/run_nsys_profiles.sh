#!/usr/bin/env bash
# Run profile_tpch_nsys.sh for Q1-Q22 into iter_dir/sirius/qN/nsys/.
set -euo pipefail
ITER_DIR="$1"
SF="$2"
CONFIG="$3"
PARQUET_DIR="$4"
ITERS="$5"

SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"
PROFILE="$SIRIUS_REPO/test/tpch_performance/profile_tpch_nsys.sh"

if ! command -v nsys >/dev/null; then
  echo "nsys not found in PATH" >&2
  exit 1
fi

if [ ! -f "$PROFILE" ]; then
  echo "profile_tpch_nsys.sh not found: $PROFILE" >&2
  exit 1
fi

for q in $(seq 1 22); do
  out_dir="$ITER_DIR/sirius/q${q}/nsys"
  mkdir -p "$out_dir"
  SIRIUS_CONFIG_FILE="$CONFIG" \
  PARQUET_DIR="$PARQUET_DIR" \
  OUTPUT_DIR="$out_dir" \
  ITERATIONS="$ITERS" \
  QUERY_TIMEOUT="${NSYS_TIMEOUT:-${TIMEOUT:-120}}" \
  bash "$PROFILE" "$SF" "$q" || true
done
