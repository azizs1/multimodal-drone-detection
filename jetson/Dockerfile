# Dockerfile for ML Inference and Fusion
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.27 /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy workspace configuration from root
COPY pyproject.toml uv.lock* /app/

# Copy jetson package
COPY jetson /app/jetson

# Install dependencies using uv
RUN cd jetson && uv sync --frozen --no-dev

# Environment variables for ZeroMQ frame transport
ENV ZMQ_FRAME_CONNECT_ENDPOINT=tcp://stream-simulator:5560

# Environment variables for RTSP publishing
ENV INFERENCE_PUBLISH_RTSP=false
ENV INFERENCE_VISUAL_RTSP_URL=rtsp://mediamtx:8554/visual-inference
ENV INFERENCE_THERMAL_RTSP_URL=rtsp://mediamtx:8554/thermal-inference
# Fusion and backend endpoints
ENV FUSION_ENDPOINT=http://fusion:8050/fusion/ingest


# Output frame sizing
ENV INFERENCE_VISUAL_OUT_WIDTH=640
ENV INFERENCE_VISUAL_OUT_HEIGHT=360
ENV INFERENCE_THERMAL_OUT_WIDTH=160
ENV INFERENCE_THERMAL_OUT_HEIGHT=120

# Encoding parameters for RTSP output
ENV INFERENCE_X264_CRF=30
ENV INFERENCE_X264_MAXRATE=900
ENV INFERENCE_X264_BUFSIZE=900
ENV INFERENCE_X264_KEYINT=12

# Set working directory to jetson
WORKDIR /app/jetson

# Run ML inference and fusion
CMD ["uv", "run", "python", "-m", "ml.inference"]
