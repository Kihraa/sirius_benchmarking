#!/usr/bin/env bash
# Generate TPC-H parquet for one scale factor via Sirius tpchgen-rs. Skips if present.
set -euo pipefail

SF="$1"
OUT="$2"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"

[ -d "$OUT" ] && exit 0

(cd "$SIRIUS_REPO/test/tpch_performance" && \
  pixi run bash generate_tpch_data.sh "$SF" --format parquet --output "$OUT" --jobs "${JOBS:-$(nproc)}")
