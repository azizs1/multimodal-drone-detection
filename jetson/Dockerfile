# https://docs.nvidia.com/metropolis/deepstream/6.0.1/dev-guide/text/DS_docker_containers.html
# this is for JetPack 4.6.1 and has DeepStream
FROM nvcr.io/nvidia/l4t-multimedia:r32.7.1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    python3-opencv \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-glib-2.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install uv

COPY pyproject.toml uv.lock ./
COPY src ./src

# JetPack 4.6.1 older PyTorch (1.10.0). also install this separately since there is special jetson version
RUN pip3 install \
  https://developer.download.nvidia.com/compute/redist/jp/v46/pytorch/torch-1.10.0-cp36-cp36m-linux_aarch64.whl

RUN uv sync --frozen --no-install torch

CMD ["uv", "run", "python3", "-m", "run_both"]
