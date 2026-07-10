#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../scripts/ensure_image.sh
source "$ROOT/scripts/ensure_image.sh"

ensure_image sirius-bench:new "$ROOT/new"

docker run --rm --gpus all \
  --security-opt seccomp=unconfined \
  --cap-add SYS_NICE \
  -v "$ROOT":/bench \
  sirius-bench:new \
  /bench/new/new_run_all.sh "$@"
