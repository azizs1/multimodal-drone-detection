# Drone Detection Stream Simulator

The `stream-simulator` service ingests paired RGB and thermal videos, publishes synchronized
frame pairs over ZeroMQ, runs YOLO inference, annotates frames, and publishes RTSP streams to MediaMTX.

## Pipeline

```
videos/*.mp4 -> video_ingestion.py -> ZeroMQ -> jetson/src/ml/inference/__main__.py
                     \-> inference.py -> frame_publisher.py -> MediaMTX (RTSP/HLS)
```

Key behavior:
- ZeroMQ publishes synchronized frame pairs from the ingestion process.
- Inference processes a frame only when a new timestamp arrives (no duplicate re-processing).
- Publisher uses a single-slot queue, so newer frames replace stale ones under load.

## Run Locally

From repository root:

```bash
uv run python3 -m simulator.src.video_ingestion
```

This starts ingestion in the foreground and publishes frame pairs over ZeroMQ. If you want the legacy local inference loop, run `simulator.src.inference` separately.

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

### Stream Output

```bash
SIM_STREAM_HOST=mediamtx
SIM_VISUAL_RTSP_URL=rtsp://mediamtx:8554/visual
SIM_THERMAL_RTSP_URL=rtsp://mediamtx:8554/thermal
SIM_STREAM_FPS=12
SIM_VISUAL_OUT_WIDTH=640
SIM_VISUAL_OUT_HEIGHT=360
SIM_THERMAL_OUT_WIDTH=160
SIM_THERMAL_OUT_HEIGHT=120
```

### Encoder (libx264)

```bash
SIM_RTSP_TRANSPORT=tcp
SIM_X264_PRESET=ultrafast
SIM_X264_TUNE=zerolatency
SIM_X264_CRF=28
SIM_X264_MAXRATE=2000
SIM_X264_BUFSIZE=2000
SIM_X264_KEYINT=12
```

## Diagnostics and Bottleneck Analysis

The simulator emits timing logs in three stages:

- `video_ingestion.py`
  - `Slow frame read: ...ms`
  - `Ingestion lag: frame processing took ...ms`
  - `Ingestion stats: max_frame_read=..., max_sleep=...`

- `inference.py`
  - `Slow inference: ...ms`
  - `Slow frame processing: ...ms (infer=..., annot=..., pub=...)`
  - periodic summary every 30 processed frames:
    - `Inference: avg=..., max=...`
    - `Annotation: avg=...`
    - `Publishing: avg=...`

- `frame_publisher.py`
  - periodic summary every 5 seconds:
    - `stats: published=..., dropped=..., queue_size=..., avg_encode=..., max_encode=...`
  - warnings:
    - `slow encode: ...ms`
    - `writer not available, dropping frame`

Rule of thumb:
- high inference time + low encode time => model compute bottleneck
- growing queue or dropped frames => publisher cannot keep up
- high frame read spikes => video I/O bottleneck

## Files

```
simulator/
├── src/
│   ├── __init__.py
│   ├── shared_buffer.py
│   ├── video_ingestion.py
│   ├── inference.py
│   ├── frame_publisher.py
│   └── frame_annotator.py
├── models/
│   ├── visual_model.pt
│   └── thermal_model.pt
├── videos/
│   ├── drone_visual.mp4
│   └── drone_thermal.mp4
├── mediamtx.yml
└── Dockerfile
```

## Notes

- In production, GPU acceleration can remove the main inference bottleneck.
- Backend HLS access logs show frequent `.m3u8` and `.ts` requests by design (live HLS polling).
