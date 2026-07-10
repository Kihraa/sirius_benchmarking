docker run --rm -it --gpus all \
  --security-opt seccomp=unconfined \
  --cap-add SYS_NICE \
  -v "$(pwd)":/bench \
  sirius-bench