FROM nvidia/cuda:13.2.1-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN     apt-get update && apt-get install -y --no-install-recommends git build-essential curl gnupg bc python3

#get pixi for sirius build
ENV     PIXI_VERSION=v0.70.2
RUN     curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=${PIXI_VERSION} bash
ENV     PATH="/root/.pixi/bin:$PATH"

#sirius
ARG     SIRIUS_REPO=https://github.com/Kihraa/sirius.git
ARG     SIRIUS_REF=dev
RUN     git clone "$SIRIUS_REPO" /sirius-db/sirius
WORKDIR /sirius-db/sirius
RUN     git checkout "$SIRIUS_REF" && git submodule update --init --recursive
RUN     git rev-parse HEAD | tee /sirius-db/sirius_commit.txt
RUN     pixi install
RUN     pixi run make

#Nsight
RUN     echo "deb http://developer.download.nvidia.com/devtools/repos/ubuntu2404/amd64 /" > /etc/apt/sources.list.d/nvidia-devtools.list
RUN     apt-key adv --fetch-keys http://developer.download.nvidia.com/devtools/repos/ubuntu2404/amd64/nvidia.pub
RUN     apt-get update && apt-get install -y nsight-systems-cli


CMD ["/bin/bash"]
