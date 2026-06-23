#!/usr/bin/env bash
# Generate TPC-H parquet for one scale factor via Sirius tpchgen-rs. Skips if present.
set -euo pipefail

SF="$1"
OUT="$2"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"

[ -d "$OUT" ] && exit 0

bash "$SIRIUS_REPO/test/tpch_performance/generate_tpch_data.sh" \
  "$SF" --format parquet --output "$OUT" --jobs "${JOBS:-$(nproc)}"
