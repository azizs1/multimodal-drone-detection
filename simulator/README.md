# Drone Detection Simulator

Video ingestion system that reads pre-recorded drone videos and provides them through a shared buffer for ML inference testing.

## Quick Start

### Option 1: Local Development

```bash
# Just run video ingestion
./simulator/start.sh

# Or from repository root
uv run python3 -m simulator.src.video_ingestion
```

### Option 2: Docker

```bash
cd simulator
docker-compose -f docker-compose.simulator.yml up
```

## Architecture

```
Video Files → Video Ingestion → Shared Buffer → Your Inference Code
```

**Simple and Clean:**
- Video ingestion runs standalone or as a background thread
- Shared buffer stores latest frame pair (thread-safe)
- Your inference code polls the buffer
- No complex orchestration needed

## Directory Structure

```
simulator/
├── src/
│   ├── __init__.py              # Exports shared buffer
│   ├── shared_buffer.py         # Thread-safe frame storage
│   ├── video_ingestion.py       # Main video ingestion
│   └── run_inference.py         # Template for YOUR code
├── videos/
│   ├── drone_visual.mp4         # RGB video
│   └── drone_thermal.mp4        # Thermal video
├── Dockerfile.inference         # Python-based inference container
├── docker-compose.simulator.yml # Docker Compose configuration
└── start.sh                     # Quick start script
```

## Writing Your Inference Code

### Approach 1: Modify the Template

Edit `src/run_inference.py` - it already has the boilerplate:

```python
# Load your models
from ultralytics import YOLO
rgb_model = YOLO("models/visual_model.pt")
thermal_model = YOLO("models/thermal_model.pt")

# In the main loop (around line 70)
rgb_results = rgb_model(rgb_frame, verbose=False)[0]
thermal_results = thermal_model(thermal_frame, verbose=False)[0]

# Process results...
```

Run with:
```bash
uv run python3 simulator/src/run_inference.py
```

### Approach 2: Write Your Own Script

```python
#!/usr/bin/env python3
"""Your custom inference script."""

import threading
from simulator.src import buffer
from simulator.src.video_ingestion import start_ingestion

# Start video ingestion in background
thread = threading.Thread(target=start_ingestion, daemon=True)
thread.start()

# Load your models
# ... your model loading code ...

# Main inference loop
while True:
    frame_data = buffer.get()
    if frame_data:
        rgb = frame_data["rgb"]
        thermal = frame_data["thermal"]
        
        # Run your inference
        # ... your inference code ...
```

### Approach 3: Standalone Ingestion

Run video ingestion separately, then run your inference in another terminal:

```bash
# Terminal 1: Video ingestion
./simulator/start.sh

# Terminal 2: Your inference
python your_inference.py
```

In `your_inference.py`:
```python
from simulator.src import buffer

while True:
    frame_data = buffer.get()
    if frame_data:
        # Process frames...
```

## Environment Variables

```bash
# Video paths (relative to simulator/)
export RGB_VIDEO_PATH=videos/drone_visual.mp4
export THERMAL_VIDEO_PATH=videos/drone_thermal.mp4

# Playback settings
export PLAYBACK_FPS=30
export LOOP_VIDEO=true

# Frame dimensions
export RGB_WIDTH=1280
export RGB_HEIGHT=720
export THERMAL_WIDTH=160
export THERMAL_HEIGHT=120
```

## Docker Usage

### Build and Run

```bash
cd simulator

# Build the image
docker build -f Dockerfile.inference -t simulator-inference ..

# Run video ingestion only
docker run -it --rm \
  -v $(pwd)/videos:/app/videos:ro \
  simulator-inference

# Run with custom videos
docker run -it --rm \
  -v /path/to/your/videos:/app/videos:ro \
  -e RGB_VIDEO_PATH=videos/my_rgb.mp4 \
  -e THERMAL_VIDEO_PATH=videos/my_thermal.mp4 \
  simulator-inference
```

### Docker Compose

The `docker-compose.simulator.yml` file is ready for you to customize:

```yaml
services:
  simulator-ingestion:
    # Video ingestion service (ready to use)
    
  simulator-inference:
    # YOUR inference service (uncomment and customize)
    # Mount your models, add your command
```

Start with:
```bash
docker-compose -f docker-compose.simulator.yml up
```

## Frame Format

- **RGB:** 1280x720, BGR format (ready for OpenCV/YOLO)
- **Thermal:** 160x120, BGR format (upscaled from grayscale)
- **Buffer:** Latest frame pair only (not a queue)
- **Timestamp:** Microseconds since epoch

## Testing

Test video ingestion:
```bash
# Should show frame updates every second
timeout 5 ./simulator/start.sh
```

Expected output:
```
Frame     30 | Elapsed:    1.0s | FPS:  30.0 | Buffer updated
Frame     60 | Elapsed:    2.0s | FPS:  30.0 | Buffer updated
```

## Dependencies

Required:
- Python 3.12+
- opencv-python >= 4.8.0
- numpy >= 1.24.0

Install:
```bash
uv sync
# or
pip install opencv-python numpy
```

## Troubleshooting

**Videos not found:**
- Check paths are relative to `simulator/` directory
- Ensure video files exist in `simulator/videos/`

**Import errors:**
- Use `uv run` or install dependencies first
- Check you're running from repository root

**No frames in buffer:**
- Video ingestion must start before your inference code
- Check ingestion output for errors
- Verify videos are valid MP4 files
