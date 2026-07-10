#!/usr/bin/env bash
# Generate TPC-H parquet for one scale factor via DuckDB dbgen. Skips if present.
set -euo pipefail

SF="$1"
OUT="$2"
DUCKDB="${DUCKDB:-${SIRIUS_REPO:-/sirius-db/sirius}/build/release/duckdb}"

[ -d "$OUT" ] && exit 0

SIRIUS_DISABLE=1 "$DUCKDB" -c \
  "INSTALL tpch; LOAD tpch; CALL dbgen(sf=${SF}); EXPORT DATABASE '${OUT}' (FORMAT PARQUET);"
