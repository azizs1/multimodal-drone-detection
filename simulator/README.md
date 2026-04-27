# Drone Detection Stream Simulator

The `stream-simulator` service ingests paired RGB and thermal videos and publishes synchronized
frame pairs over ZeroMQ.

## Pipeline

```text
videos/*.mp4 -> video_ingestion.py -> ZeroMQ -> jetson/src/ml/inference/__main__.py -> MediaMTX (RTSP/HLS)
```

Key behavior:

- ZeroMQ publishes synchronized frame pairs from the ingestion process.

## Run Locally

From the `simulator/` directory:

```bash
cd simulator && uv run python3 -m src.video_ingestion
```

This starts ingestion in the foreground and publishes frame pairs over ZeroMQ.

## Run With Docker Compose

The active service name is `stream-simulator` in `docker-compose-dev.yml`.

```bash
docker compose -f docker-compose-dev.yml up stream-simulator mediamtx
```

To inspect logs:

```bash
docker compose -f docker-compose-dev.yml logs -f stream-simulator mediamtx
```

## Important Environment Variables

### Ingestion

```bash
RGB_VIDEO_PATH=videos/drone_visual.mp4
THERMAL_VIDEO_PATH=videos/drone_thermal.mp4
PLAYBACK_FPS=20
LOOP_VIDEO=true
RGB_WIDTH=1280
RGB_HEIGHT=720
THERMAL_WIDTH=160
THERMAL_HEIGHT=120
ZMQ_FRAME_BIND_ENDPOINT=tcp://*:5560
```

## Diagnostics and Bottleneck Analysis

The simulator emits timing logs in one stage:

- `video_ingestion.py`
  - `Slow frame read: ...ms`
  - `Ingestion lag: frame processing took ...ms`
  - `Ingestion stats: max_frame_read=..., max_sleep=...`

Rule of thumb:

- high frame read spikes => video I/O bottleneck

## Files

```text
simulator/
├── src/
│   ├── __init__.py
│   ├── frame_pair_transport.py
│   └── video_ingestion.py
├── videos/
│   ├── drone_visual.mp4
│   └── drone_thermal.mp4
├── mediamtx.yml
└── Dockerfile
```

## Notes

- In production, GPU acceleration can remove the main inference bottleneck.
- Backend HLS access logs show frequent `.m3u8` and `.ts` requests by design (live HLS polling).
