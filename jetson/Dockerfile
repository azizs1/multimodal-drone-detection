# https://docs.nvidia.com/metropolis/deepstream/6.0.1/dev-guide/text/DS_docker_containers.html
# this is for JetPack 4.6.1, but NO DEEPSTREAM (switch later if needed)
FROM nvcr.io/nvidia/l4t-base:r32.7.1

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    tzdata \
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
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# RUN pip3 install uv

#COPY pyproject.toml uv.lock ./
COPY pyproject.toml ./
COPY src ./src

# JetPack 4.6.1 older PyTorch (1.10.0). also install this separately since there is special jetson version
# figure this out later
# RUN pip3 install --no-cache-dir \
#     https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl

# RUN uv sync --frozen --no-install torch

#CMD ["uv", "run", "python3", "-m", "run_both"]
# CMD ["uv", "run", "python3", "-m", "sensor_ingestion.ingest_gi"]
CMD ["python3", "sensor_ingestion.ingest_gi"]
