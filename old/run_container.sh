#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../scripts/ensure_image.sh
source "$ROOT/scripts/ensure_image.sh"

ensure_image sirius-bench:old "$ROOT/old"

docker run --rm --gpus all \
  --security-opt seccomp=unconfined \
  --cap-add SYS_NICE \
  -v "$ROOT":/bench \
  sirius-bench:old \
  /bench/old/old_run_all.sh "$@"
