docker run --rm --gpus all \
  -v "$(pwd)":/bench \
  -v /mnt/bigdisk/sirius_data:/data \
  sirius-bench \
  /bench/run_all.sh --sf 100,1000 --experiments timing,memory