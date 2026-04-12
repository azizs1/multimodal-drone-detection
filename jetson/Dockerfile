FROM bluenviron/mediamtx:latest AS mediamtx_source
# https://docs.nvidia.com/metropolis/deepstream/6.0.1/dev-guide/text/DS_docker_containers.html
# this is for JetPack 4.6.1, but NO DEEPSTREAM (switch later if needed)
# FROM nvcr.io/nvidia/l4t-base:r32.7.1
# TODO: Switch to the following once we have Orin nano:
FROM nvcr.io/nvidia/l4t-ml:r36.2.0-py3


WORKDIR /app

COPY --from=mediamtx_source /mediamtx ./mediamtx
COPY mediamtx.yml ./mediamtx.yml

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    tzdata \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-glib-2.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    uv \
    ultralytics \
    fastapi \
    uvicorn \
    python-dotenv \
    pydantic \
    numpy \
    pyzmq

#COPY pyproject.toml uv.lock ./
COPY pyproject.toml ./
COPY src/ ./src/

# MediaMTX ports: 
# 8554: RTSP
# 8888: HLS (backend proxy)
# 8889: MediaMTX API
EXPOSE 8554 8888 8889

# This is commented out for now for running on Jetson Nano
# RUN uv sync --frozen --no-install torch

#CMD ["uv", "run", "python3", "-m", "run_both"]
# CMD ["uv", "run", "python3", "-m", "sensor_ingestion.ingest_gi"]
ENV GST_DEBUG=3
# CMD ["python3", "-m", "sensor_ingestion.ingest_gi"]
CMD ["python3", "-u", "src/run_jetson_components.py"]
