# Dockerfile for running video ingestion with uv
FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.14 /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app/simulator

# Copy simulator project metadata and source
COPY simulator/pyproject.toml ./pyproject.toml
COPY simulator /app/simulator

# Install dependencies using uv
RUN uv sync --no-dev

# Environment variables for video paths and settings
ENV RGB_VIDEO_PATH=videos/visible.mp4
ENV THERMAL_VIDEO_PATH=videos/infrared.mp4
ENV PLAYBACK_FPS=30
ENV LOOP_VIDEO=true
ENV RGB_WIDTH=1280
ENV RGB_HEIGHT=720
ENV THERMAL_WIDTH=160
ENV THERMAL_HEIGHT=120

# Run video ingestion
CMD ["uv", "run", "python3", "-m", "src.video_ingestion"]
