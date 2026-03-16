FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./videos /app/videos

# Install bash for looping script
RUN apt update && apt install -y bash && rm -rf /var/lib/apt/lists/*

# Create a streaming script that uses environment variables for stream name and video file
RUN echo '#!/bin/bash\n\
    STREAM_NAME=${STREAM_NAME:-drone}\n\
    VIDEO_FILE=${VIDEO_FILE:-drone_test.mp4}\n\
    echo "Streaming ${VIDEO_FILE} to rtsp://mediamtx:8554/${STREAM_NAME}"\n\
    ffmpeg -re -stream_loop -1 \\\n\
    -i /app/videos/${VIDEO_FILE} \\\n\
    -c:v libx264 -preset ultrafast -tune zerolatency \\\n\
    -g 30 -keyint_min 30 \\\n\
    -b:v 2000k \\\n\
    -f rtsp \\\n\
    -rtsp_transport tcp \\\n\
    rtsp://mediamtx:8554/${STREAM_NAME}' > /app/stream.sh && chmod +x /app/stream.sh

CMD ["/app/stream.sh"]
