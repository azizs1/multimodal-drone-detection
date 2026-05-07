# Multimodal Drone Detection - Field Test Branch

This branch contains the code used for drone field testing.

It is intended to run across two machines:

- **Jetson Orin Nano**: runs `jetson-core`
- **Laptop / Mac**: runs the backend, database, and frontend

This branch is not intended to be merged into `main`.

## Field Test Architecture

```text
Jetson Orin Nano
  - RGB camera
  - Thermal camera
  - ML inference
  - Fusion logic
  - RTSP / HLS / WebRTC stream publishing
  - Incident POST requests to laptop backend

Laptop / Mac
  - PostgreSQL database
  - FastAPI backend
  - Next.js frontend dashboard
```

Expected dashboard URL on the laptop:

```text
http://localhost:3000/live-feed
```

## Network Configuration

The IP addresses can change between field-test sessions. Before running the system, confirm:

- Jetson IP address
- Laptop IP address
- Backend incident endpoint
- Stream base URLs

Where these IPs are used:

- `BACKEND_INCIDENT_ENDPOINT` should point from Jetson to the laptop backend.
- `STREAM_RTSP_BASE_URL`, `STREAM_HLS_BASE_URL`, and `STREAM_WEBRTC_BASE_URL` should point from the laptop backend/frontend to the Jetson stream host.

## Laptop / Mac Setup

Run the laptop-side services from the repository root on the Mac.

```bash
STREAM_RTSP_BASE_URL=rtsp://<JETSON_IP>:8554 \
STREAM_HLS_BASE_URL=http://<JETSON_IP>:8888 \
STREAM_WEBRTC_BASE_URL=http://<JETSON_IP>:9998 \
VISUAL_STREAM_WIDTH=1280 \
VISUAL_STREAM_HEIGHT=720 \
VISUAL_STREAM_FPS=15 \
THERMAL_STREAM_WIDTH=512 \
THERMAL_STREAM_HEIGHT=384 \
THERMAL_STREAM_FPS=25 \
docker compose -f docker-compose.mac-jetson.yml up -d --build --force-recreate backend frontend
```

This starts the laptop-side services needed for the field test:

- `postgres`
- `backend`
- `frontend`

Open the dashboard:

```text
http://localhost:3000/live-feed
```

Useful laptop commands:

```bash
docker compose -f docker-compose.mac-jetson.yml ps
docker compose -f docker-compose.mac-jetson.yml logs -f backend
docker compose -f docker-compose.mac-jetson.yml logs -f frontend
docker compose -f docker-compose.mac-jetson.yml down
```

## Jetson Setup

SSH from the Mac into the Jetson:

```bash
ssh capstone26@<JETSON_IP>
```

Go to the project directory on the Jetson:

```bash
cd ~/multimodal-drone-detection
```

Build the Jetson core image:

```bash
docker build \
  -t multimodal-drone-detection-jetson-core \
  -f jetson/Dockerfile \
  jetson
```

Stop and remove any existing `jetson-core` container:

```bash
docker stop jetson-core 2>/dev/null
docker rm jetson-core 2>/dev/null
```

Run `jetson-core`:

```bash
docker run -d \
  --name jetson-core \
  --runtime nvidia \
  --network host \
  --privileged \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e BACKEND_INCIDENT_ENDPOINT=http://<LAPTOP_IP>:8000/incidents \
  -e RGB_MODEL_PATH=/app/offline_ml/weights/visual_no_augmentation_best.pt \
  -e THERMAL_MODEL_PATH=/app/offline_ml/weights/thermal_no_augmentation_best.pt \
  -e THERMAL_CAMERA_DEVICE=/dev/video2 \
  -v /tmp/argus_socket:/tmp/argus_socket \
  -v ~/multimodal-drone-detection/offline_ml/weights:/app/offline_ml/weights:ro \
  --device /dev/video0 \
  --device /dev/video2 \
  multimodal-drone-detection-jetson-core
```

Important values to update when the network changes:

```text
BACKEND_INCIDENT_ENDPOINT=http://<LAPTOP_IP>:8000/incidents
```

Camera/device values used by the previous field-test setup:

```text
RGB camera device: /dev/video0
Thermal camera device: /dev/video2
Thermal env var: THERMAL_CAMERA_DEVICE=/dev/video2
```

## Jetson Logs

Follow the Jetson container logs:

```bash
docker logs -f jetson-core
```

Expected successful log messages:

```text
loaded RGB and thermal models
[path visual] stream is available
[rgb] frame received
[thermal] frame received
fusion response status=200
```

The exact ordering may vary, but the important checks are:

- Both RGB and thermal models load.
- Both RGB and thermal frames are received.
- Fusion posts to the laptop backend successfully.
- The backend returns HTTP `200`.

## Buffer Recovery

If the Jetson stream or inference pipeline appears to have buffer buildup, restart the Jetson container:

```bash
docker restart jetson-core
```

Then watch logs again:

```bash
docker logs -f jetson-core
```

## Field Test Startup Checklist

1. Confirm the Jetson and laptop are on the expected network.
2. Confirm the current Jetson IP and laptop IP.
3. On the laptop, start backend, database, and frontend with `docker-compose.mac-jetson.yml`.
4. SSH into the Jetson.
5. Rebuild and run `jetson-core`.
6. Watch `docker logs -f jetson-core`.
7. Open `http://localhost:3000/live-feed` on the laptop.
8. Confirm RGB stream, thermal stream, detections, and incidents are visible.

## Troubleshooting

### Dashboard loads but streams are unavailable

Check that the laptop-side stream URLs point to the current Jetson IP:

```bash
STREAM_RTSP_BASE_URL=rtsp://<JETSON_IP>:8554
STREAM_HLS_BASE_URL=http://<JETSON_IP>:8888
STREAM_WEBRTC_BASE_URL=http://<JETSON_IP>:9998
```

Restart the laptop services after changing these values.

### Jetson detects frames but incidents do not appear

Check that `BACKEND_INCIDENT_ENDPOINT` points to the current laptop IP:

```bash
BACKEND_INCIDENT_ENDPOINT=http://<LAPTOP_IP>:8000/incidents
```

Also check the backend logs on the laptop:

```bash
docker compose -f docker-compose.mac-jetson.yml logs -f backend
```

### Camera frames are missing

Check the Jetson device mappings:

```bash
ls /dev/video*
```

The previous field-test setup used:

```text
/dev/video0
/dev/video2
```

If the device numbers change, update both the `--device` arguments and `THERMAL_CAMERA_DEVICE`.

### Model files are missing

The Jetson container expects model weights mounted from:

```text
~/multimodal-drone-detection/offline_ml/weights
```

Expected paths inside the container:

```text
/app/offline_ml/weights/visual_no_augmentation_best.pt
/app/offline_ml/weights/thermal_no_augmentation_best.pt
```
