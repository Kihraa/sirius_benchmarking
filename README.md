# sirius_benchmarking

TPC-H benchmarks for two Sirius snapshots:

- **old** — April snapshot (GPU table cache)
- **new** — July snapshot (cuCascade pinning / spilling)

Each snapshot is built into its own Docker image. Results land under `results/`; figures under `figures/`.

## Prerequisites

- Docker with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) (`docker run --gpus all` must work)
- An NVIDIA GPU and a driver new enough for **CUDA 13.2**
- Python 3 with `matplotlib` and `numpy` (plotting only)

## Run the benchmarks

From the repo root:

```bash
./run_all.sh --name my_run
```

This builds `sirius-bench:old` and `sirius-bench:new` if they are missing, then runs **every** experiment for both snapshots. Outputs go to `results/my_run/{old,new}/`.

If `--name` is omitted, the next `runNN` directory is chosen automatically.

Useful flags:

| Flag | What it does |
|---|---|
| `--name NAME` | Result directory under `results/` |
| `--sf 1,10,100` | Scale factors (default: `1 3 10 30 100`) |
| `--nsys` | Also collect Nsight Systems profiles (takes a long time) |
| `--no-cache` | Rebuild both images from scratch |

`--experiment` is **not** supported on this script. To run a subset, use the per-snapshot helpers:

```bash
./old/run_container.sh --name my_run --experiment sweep_baseline --sf 10
./new/run_container.sh --name my_run --experiment sweep_baseline --sf 10
```

## Plot results

```bash
pip install -r plot/requirements.txt
python3 plot/plot_all.py --run my_run
```

`--run` must match a directory under `results/` (for example `my_run` or `L4_nsys`).

It generates bar charts and heatmaps for `old` and `new` when those result trees exist. Failed plots are skipped; the rest still run. Figures are written to `figures/` with the same layout as `results/`.

## Machine requirements (current configs)

These configs were written for the L4 / H100 machines used in the thesis. Smaller machines need YAML edits, not just a smaller `--sf`. There is currently no easy way to change the configs for all experiments at once.

- **Host RAM.** Baseline sets `memory.host.capacity_bytes: 64Gi` of pinned host memory **per NUMA node**. With the default of 2 NUMA nodes that is 128 GB, plus extra for DuckDB, the OS, and Parquet generation.
- **x86_64.** Images are Ubuntu 24.04 / amd64.

## Project structure

```
run_all.sh          # build both images, run old then new
old/                # April snapshot
new/                # July snapshot
plot/               # figure generation
results/            # benchmark output
figures/            # plot output
```

### `old/` and `new/`

Same layout in both:

| Path | What it is |
|---|---|
| `Dockerfile` | CUDA 13.2 image, clones and builds that Sirius commit |
| `configs/` | Sirius YAML. `baseline.yaml` is the default; other folders are one-parameter sweeps |
| `experiments/` | One script per config |
| `test_gen/` | TPC-H Parquet generation (`tpch_duck.sh`, `tpch_sirius.sh`) |
| `*_run_all.sh` | In-container entry: generate data, then run experiments (does not build the image) |
| `run_container.sh` | `docker run` wrapper around `*_run_all.sh` |
| `start_container.sh` | Interactive shell in the image |

Configs, experiments, figures, and results share the same path structure. For example, `configs/memory_usage_limit/usage_limit_0P5.yaml` is driven by `experiments/sweep_memory_usage_limit/sweep_usage_limit_0P5.sh`.

**old** sweeps: baseline, Sirius Parquet, spill on/off × thread counts, GPU usage limit, downgrade trigger.

**new** sweeps: baseline, Sirius Parquet, host-thread counts, GPU pin, no pin, usage limit, downgrade trigger.
