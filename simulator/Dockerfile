FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    libgstrtspserver-1.0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./videos /app/videos

# Install bash for looping script
RUN apt update && apt install -y bash && rm -rf /var/lib/apt/lists/*

# Create a script that handles seamless looping with minimal interruption
RUN echo '#!/bin/bash\n\
    while true; do\n\
    gst-launch-1.0 -q \\\n\
    filesrc location=/app/videos/drone_test.mp4 ! \\\n\
    qtdemux ! h264parse ! \\\n\
    queue max-size-buffers=0 max-size-time=0 max-size-bytes=0 ! \\\n\
    rtspclientsink location=rtsp://mediamtx:8554/drone protocols=tcp latency=0 \\\n\
    || echo "Stream ended, restarting immediately...";\n\
    done' > /app/stream.sh && chmod +x /app/stream.sh

# Stream video in a loop with minimal gap
CMD ["/app/stream.sh"]
