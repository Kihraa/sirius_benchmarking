docker run --rm --gpus all \
  -v "$(pwd)":/bench \
  sirius-bench \
  /bench/run_all.sh