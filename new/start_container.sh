ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm -it --gpus all \
  --security-opt seccomp=unconfined \
  --cap-add SYS_NICE \
  -v "$ROOT":/bench \
  sirius-bench:new
