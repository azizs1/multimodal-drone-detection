# https://docs.nvidia.com/metropolis/deepstream/6.0.1/dev-guide/text/DS_docker_containers.html
# this is for JetPack 4.6.1 and has DeepStream
FROM nvcr.io/nvidia/deepstream-l4t:6.0.1-devel

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install uv

COPY pyproject.toml uv.lock ./
COPY src ./src

# JetPack 4.6.1 older PyTorch (1.10.0). also install this separately since there is special jetson version
RUN pip3 install \
  https://developer.download.nvidia.com/compute/redist/jp/v46/pytorch/torch-1.10.0-cp36-cp36m-linux_aarch64.whl

RUN uv sync --frozen --no-install torch

CMD ["uv", "run", "python3", "-m", "run_both"]
