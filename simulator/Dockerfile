FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./videos /app/videos

# Install bash for looping script
RUN apt update && apt install -y bash && rm -rf /var/lib/apt/lists/*

# Create a streaming script using FFmpeg with infinite loop and re-encoding for seamless playback
RUN echo '#!/bin/bash\n\
ffmpeg -re -stream_loop -1 \\\n\
  -i /app/videos/drone_test.mp4 \\\n\
  -c:v libx264 -preset ultrafast -tune zerolatency \\\n\
  -g 30 -keyint_min 30 \\\n\
  -b:v 2000k \\\n\
  -f rtsp \\\n\
  -rtsp_transport tcp \\\n\
  rtsp://mediamtx:8554/drone' > /app/stream.sh && chmod +x /app/stream.sh

# Stream video in a loop with minimal gap
CMD ["/app/stream.sh"]
