FROM bluenviron/mediamtx:latest AS mediamtx_source
FROM nvcr.io/nvidia/l4t-jetpack:r36.2.0

WORKDIR /app

COPY --from=mediamtx_source /mediamtx ./mediamtx

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_DEPS=0
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV TORCH_WHL_URL=https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    libgirepository1.0-dev \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    uv \
    fastapi \
    uvicorn \
    python-dotenv \
    pydantic \
    pyyaml \
    pyzmq \
    numpy==1.26.4 \
    pillow \
    scipy \
    requests \
    matplotlib \
    psutil \
    torchsummary

# Force Jetson JP6.1 torch wheel to avoid pulling incompatible torch builds (e.g. cu130).
RUN pip3 uninstall -y torch torchvision || true
RUN pip3 install --no-cache-dir "${TORCH_WHL_URL}"
# Keep ultralytics from mutating torch version during dependency resolution.
RUN pip3 install --no-cache-dir --no-deps ultralytics

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
