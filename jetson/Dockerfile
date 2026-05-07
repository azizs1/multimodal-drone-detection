FROM bluenviron/mediamtx:latest AS mediamtx_source
FROM nvcr.io/nvidia/l4t-jetpack:r36.4.0

WORKDIR /app

COPY --from=mediamtx_source /mediamtx ./mediamtx

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_DEPS=0
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    libgirepository1.0-dev \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    libopenblas-dev \
    wget \
    xz-utils \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-sbsa/libcusparse_lt-linux-sbsa-0.5.2.1-archive.tar.xz \
    && tar xf libcusparse_lt-linux-sbsa-0.5.2.1-archive.tar.xz \
    && cp -a libcusparse_lt-linux-sbsa-0.5.2.1-archive/include/* /usr/local/cuda/include/ \
    && cp -a libcusparse_lt-linux-sbsa-0.5.2.1-archive/lib/* /usr/local/cuda/lib64/ \
    && ldconfig \
    && rm -rf libcusparse_lt-linux-sbsa-0.5.2.1-archive*

RUN pip3 install --no-cache-dir numpy==1.26.4
RUN pip3 install --no-cache-dir \
    https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl \
    https://github.com/ultralytics/assets/releases/download/v0.0.0/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl

RUN pip3 install --no-cache-dir \
    uv \
    fastapi \
    uvicorn \
    python-dotenv \
    pydantic \
    pyyaml \
    ultralytics \
    pyzmq

RUN pip3 install --no-cache-dir --force-reinstall "numpy<2"

#COPY pyproject.toml uv.lock ./
COPY mediamtx.yml ./mediamtx.yml
COPY pyproject.toml ./
COPY src/ ./src/

# MediaMTX ports: 
# 8554: RTSP
# 8888: HLS (backend proxy)
# 8889: MediaMTX API
EXPOSE 8554 8888 8889

ENV GST_DEBUG=3
CMD ["python3", "-u", "src/run_jetson_components.py"]
