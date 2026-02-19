# Multimodal Drone Detection
**Authors:** Chia-Yu Chang, Yu-Chieh Cheng, Li-Chieh Kung, Ethan Mauger, Aziz Shaik
**Course:** CS 5934: Capstone Design (Spring 2026)

This MEng capstone project aims to build a drone detection system with an AI-enabled multimodal approach.

## Architecture

The system consists of four main components:

1. **Simulator** - GStreamer-based video streamer that loops drone footage to RTSP
2. **MediaMTX** - RTSP/HLS media server that handles stream distribution
3. **Backend** - FastAPI service providing REST API and stream information
4. **Jetson** - Edge AI processing on Jetson Nano (ML + sensor ingestion)

### Streaming Pipeline

```
[Simulator] --RTSP--> [MediaMTX] --HLS--> [Clients/Frontend]
                           ^
                           |
                      [Backend API]
```

## Quick Start

### Using Docker Compose (Recommended)

Start all services:
```bash
docker compose -f docker-compose-dev.yml up --build
```

Access points:
- **Video Stream (HLS Player):** http://localhost:8888/drone/
- **Backend API:** http://localhost:8000/
- **Stream Info:** http://localhost:8000/info/drone
- **Health Check:** http://localhost:8000/health

### Individual Services

Stop all services:
```bash
docker compose -f docker-compose-dev.yml down
```

Rebuild specific service:
```bash
docker compose -f docker-compose-dev.yml up -d --build simulator
```

## Prerequisites

### Python Package Manager: uv
This project uses [uv](https://github.com/astral-sh/uv) as the Python package manager for the backend, machine learning, and sensor ingestion components.

#### Installing uv

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (via pip):**
```bash
pip install uv
```

#### Using uv

After installing uv, navigate to the project directory and sync dependencies:

```bash
# Install dependencies from uv.lock
uv sync

# Install development dependencies
uv sync --dev

# Install only production dependencies
uv sync --no-dev
```

When running Python scripts, use `uv run`:
```bash
uv run python your_script.py
```

For package-specific commands:
```bash

cd backend

# Run the backend server
uv run uvicorn backend.src.app.main:app --reload

# Run tests
uv run pytest
```

## How to Use

### Simulator
The simulator streams drone video footage to the MediaMTX server using GStreamer.

**Directory:** `simulator/`

**Configuration:**
- Video files: Place `.mp4` files in `simulator/videos/`
- Default video: `drone_test.mp4`

**Standalone Build:**
```bash
cd simulator
docker build -t drone-simulator .
docker run --network host drone-simulator
```

### MediaMTX (Streaming Server)
MediaMTX handles RTSP ingestion and HLS distribution.

**Configuration:** `mediamtx.yml`

**Features:**
- RTSP server on port 8554
- HLS server on port 8888
- Built-in web player

**Access:**
- RTSP URL: `rtsp://localhost:8554/drone`
- HLS URL: `http://localhost:8888/drone/index.m3u8`
- Web Player: `http://localhost:8888/drone/`

### Frontend
#### Development
\<how to initialize this for dev\>
#### Deployment
\<how to deploy the docker container for this\>

### Backend
Backend provides REST API for stream information and system management.

**Directory:** `backend/`
**Tech Stack:** FastAPI, Python 3.12, uv

#### API Endpoints
- `GET /` - API information and quick links
- `GET /streams` - List all available streams
- `GET /info/{stream_name}` - Get stream details
- `GET /health` - Health check

#### Development
1. Install uv (see Prerequisites above)
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Install dependencies:
   ```bash
   uv sync --no-dev
   ```
4. Run the development server:
   ```bash
   uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Deployment
Using Docker Compose:
```bash
docker compose -f docker-compose-dev.yml up -d backend
```

Standalone:
```bash
docker build -t drone-detection-backend -f backend/Dockerfile ./backend
docker run -p 8000:8000 drone-detection-backend
```

### Jetson
Jetson components handle edge AI processing and sensor ingestion.

**Directory:** `jetson/`
**Hardware:** NVIDIA Jetson Nano
**Tech Stack:** Python, uv

#### Development
1. Install uv (see Prerequisites above)
2. Navigate to the jetson directory:
   ```bash
   cd jetson
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Run the components:
   ```bash
   uv run python src/run_both.py
   ```

#### Deployment
Using Docker Compose (Jetson-specific):
```bash
docker compose -f docker-compose.jetson.yaml up --build
```

## Troubleshooting

### No video in HLS player
1. Check if simulator is streaming:
   ```bash
   docker logs gst-simulator --tail 20
   ```
2. Verify MediaMTX is receiving the stream:
   ```bash
   docker logs mediamtx --tail 20
   ```
   Look for: `[HLS] [muxer drone] is converting into HLS`

3. Wait 10-15 seconds after starting services for HLS segments to generate

### Stream keeps reconnecting
- The simulator loops the video file, causing brief disconnections
- This is normal behavior; the stream will reconnect automatically

### Port conflicts
If you get "port already in use" errors:
```bash
# Check what's using the ports
netstat -an | findstr "8000 8554 8888"

# Stop conflicting services or change ports in docker-compose-dev.yml
```

### Backend can't find HLS files
- MediaMTX serves HLS dynamically via HTTP, not by writing to disk
- Access streams via MediaMTX port 8888, not through backend static files

## Project Structure

```
multimodal-drone-detection/
├── simulator/              # GStreamer video streamer
│   ├── Dockerfile
│   └── videos/            # Video files
│       └── drone_test.mp4
├── backend/               # FastAPI backend service
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       └── app/
│           └── main.py
├── frontend/              # Frontend application
│   ├── Dockerfile
│   └── src/
├── jetson/                # Jetson Nano components
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/
│       ├── ml/           # Machine learning models
│       └── sensor_ingestion/
├── mediamtx.yml          # MediaMTX configuration
├── docker-compose-dev.yml # Development compose file
└── docker-compose.jetson.yaml  # Jetson-specific compose
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `uv run pytest`
4. Submit a pull request

## License

[Add license information]
