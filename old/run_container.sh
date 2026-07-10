docker run --rm --gpus all \
  --security-opt seccomp=unconfined \
  --cap-add SYS_NICE \
  -v "$(pwd)":/bench \
  sirius-bench \
  /bench/run_all.sh
