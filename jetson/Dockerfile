# https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-base
FROM nvcr.io/nvidia/l4t-base:r35.3.1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libopenblas-base libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install uv

COPY pyproject.toml uv.lock ./
COPY src ./src

# install everything except torch. install jetson torch separately
RUN uv sync --frozen --no-install torch
RUN pip3 install \
    https://developer.download.nvidia.com/compute/redist/jp/v50/pytorch/torch-2.1.0-cp38-cp38-linux_aarch64.whl

CMD ["uv", "run", "python3", "-m", "run_both"]
