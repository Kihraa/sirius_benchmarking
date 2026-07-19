FROM nvidia/cuda:12.9.2-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN     apt-get update && apt-get install -y --no-install-recommends git build-essential curl gnupg bc python3 python3-pip python-is-python3

#get pixi for sirius build
ENV     PIXI_VERSION=v0.71.0
RUN     curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=${PIXI_VERSION} bash
ENV     PATH="/root/.pixi/bin:$PATH"

#sirius
ARG     SIRIUS_REPO=https://github.com/sirius-db/sirius.git
ARG     SIRIUS_REF=bb937b8dd2a57b2f6b6c60679a02209ffb5013d4
RUN     git clone "$SIRIUS_REPO" /sirius
WORKDIR /sirius
RUN     git checkout "$SIRIUS_REF" && git submodule update --init --recursive
RUN     git rev-parse HEAD | tee /sirius_commit.txt
RUN     pixi install -e cuda12
RUN     pixi run -e cuda12 make -j"$(nproc)"

# tpchgen-rs parquet generation (generate_tpch_data.sh standalone: rust + pyarrow)
RUN     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV     PATH="/root/.cargo/bin:${PATH}"
RUN     pip3 install --break-system-packages pyarrow

#Nsight
RUN     echo "deb http://developer.download.nvidia.com/devtools/repos/ubuntu2404/amd64 /" > /etc/apt/sources.list.d/nvidia-devtools.list
RUN     apt-key adv --fetch-keys http://developer.download.nvidia.com/devtools/repos/ubuntu2404/amd64/nvidia.pub
RUN     apt-get update && apt-get install -y nsight-systems-cli


CMD ["/bin/bash"]
