#!/usr/bin/env bash
# Generate TPC-H parquet for one scale factor via Sirius tpchgen-rs. Skips if present.
set -euo pipefail

SF="$1"
OUT="$2"
SIRIUS_REPO="${SIRIUS_REPO:-/sirius}"

[ -d "$OUT" ] && exit 0

if ! command -v python >/dev/null 2>&1; then
  PYTHON3="$(command -v python3)"
  PYTHON_SHIM="$(mktemp -d)"
  ln -s "$PYTHON3" "$PYTHON_SHIM/python"
  export PATH="$PYTHON_SHIM:$PATH"
  trap 'rm -rf "$PYTHON_SHIM"' EXIT
fi

bash "$SIRIUS_REPO/test/tpch_performance/generate_tpch_data.sh" \
  "$SF" --format parquet --output "$OUT" --jobs "${JOBS:-$(nproc)}"
