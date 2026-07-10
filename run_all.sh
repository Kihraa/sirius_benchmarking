#!/usr/bin/env bash
# Build variant images if needed, then run old and new benchmarks sequentially.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/ensure_image.sh
source "$ROOT/scripts/ensure_image.sh"

NAME=""
FORWARD_ARGS=()

run_variant() {
  local tag="$1" script="$2"
  echo "running $script with image $tag"
  docker run --rm --gpus all \
    --security-opt seccomp=unconfined \
    --cap-add SYS_NICE \
    -v "$ROOT":/bench \
    "$tag" \
    "$script" "${FORWARD_ARGS[@]}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --sf)
      FORWARD_ARGS+=(--sf "$2")
      shift 2
      ;;
    --iterations)
      FORWARD_ARGS+=(--iterations "$2")
      shift 2
      ;;
    --timeout)
      FORWARD_ARGS+=(--timeout "$2")
      shift 2
      ;;
    --name)
      NAME="$2"
      shift 2
      ;;
    --nsys)
      FORWARD_ARGS+=(--nsys)
      shift
      ;;
    --experiment)
      echo "error: --experiment is not supported by root run_all.sh yet" >&2
      exit 1
      ;;
    *)
      echo "unknown flag: $1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$NAME" ]; then
  NAME="$(printf 'run%02d' $(( $(find "$ROOT/results" -maxdepth 1 -name 'run*' -type d 2>/dev/null | wc -l) + 1 )))"
fi
FORWARD_ARGS+=(--name "$NAME")

ensure_image sirius-bench:old "$ROOT/old"
ensure_image sirius-bench:new "$ROOT/new"

run_variant sirius-bench:old /bench/old/old_run_all.sh
run_variant sirius-bench:new /bench/new/new_run_all.sh
