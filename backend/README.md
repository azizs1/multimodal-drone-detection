# Backend API

The backend is a FastAPI service providing a REST API for drone detection management and real-time WebSocket updates.

## Running the Backend

### Locally with uv

```bash
cd backend

# Install dependencies
uv sync

# Start the server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Docker

```bash
cd backend

# Build the image
docker build -t drone-detection-backend .

# Run the container
docker run -p 8000:8000 drone-detection-backend
```

## API Endpoints

### Detection Management

#### Create Detection
**POST** `/detections`

Creates a new drone detection record and broadcasts the detection ID to all connected WebSocket clients.

**Request:**
```json
{
  "detected_at": "2026-02-21T14:32:07Z",
  "confidence": 0.94,
  "direction": "NE",
  "distance_ft": 125.5,
  "visual_confidence": 0.92,
  "thermal_confidence": 0.89,
  "fused_score": 0.94,
  "frame_snapshot_url": "s3://detections/drone/2026-02-21/detection_123.jpg",
  "stream_name": "drone"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "detected_at": "2026-02-21T14:32:07Z",
  "confidence": 0.94,
  "direction": "NE",
  "distance_ft": 125.5,
  "visual_confidence": 0.92,
  "thermal_confidence": 0.89,
  "fused_score": 0.94,
  "frame_snapshot_url": "s3://detections/drone/2026-02-21/detection_123.jpg",
  "stream_name": "drone",
  "created_at": "2026-02-21T14:32:07Z",
  "updated_at": "2026-02-21T14:32:07Z"
}
```

#### Get Detection by ID
**GET** `/detections/{detection_id}`

Retrieve a specific detection record by its UUID.

#### List Detections
**GET** `/detections`

List all detection records with optional filtering.

**Query Parameters:**
- `skip` (int, default=0): Number of records to skip (pagination)
- `limit` (int, default=100, max=1000): Maximum number of records to return
- `stream_name` (str, optional): Filter by stream name

#### Delete Detection
**DELETE** `/detections/{detection_id}`

Delete a detection record by ID (returns 204 No Content).

#### Get Detection Statistics
**GET** `/detections/stats/summary`

Get aggregated statistics about detections.

**Query Parameters:**
- `stream_name` (str, optional): Filter statistics by stream name

**Response:**
```json
{
  "total_detections": 1500,
  "drone_detections": 342,
  "non_drone_detections": 1158,
  "stream_name": "drone"
}
```

### WebSocket Endpoint (Real-time Updates)

#### Alter Endpoint
**WebSocket** `/detections/alter`

Connects to a WebSocket and receives detection IDs in real-time whenever a new detection is created.

**Usage Example (Python):**
```python
import asyncio
import websockets
import json

async def listen_for_detections():
    async with websockets.connect("ws://localhost:8000/detections/alter") as ws:
        while True:
            detection_id = await ws.recv()
            print(f"New detection: {detection_id}")

asyncio.run(listen_for_detections())
```

**Usage Example (JavaScript):**
```javascript
const ws = new WebSocket("ws://localhost:8000/detections/alter");

ws.onmessage = (event) => {
  const detectionId = event.data;
  console.log("New detection:", detectionId);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("WebSocket connection closed");
};
```

### Stream Information

#### List Streams
**GET** `/streams`

Get a list of all available video streams with their connection details.

#### Get Stream Info
**GET** `/streams/{stream_name}`

Get detailed information about a specific stream (RTSP and HLS URLs).

#### Get HLS Stream
**GET** `/streams/{stream_name}/hls/{file_path}`

Get HLS playlist or segment files from MediaMTX.

### Health Checks

#### Basic Health Check
**GET** `/health`

Returns the service health status.

#### Database Health Check
**GET** `/health/db`

Returns the database connection status and basic health information.

#### Readiness Check
**GET** `/health/ready`

Check if the service is ready to serve requests.

#### Liveness Check
**GET** `/health/live`

Check if the service is alive.

## Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest src/tests/test_main.py

# Run tests with coverage
uv run pytest --cov=app src/tests/
```

## Project Structure

```
backend/
├── src/
│   ├── app/
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── api/
│   │   │   └── routers/
│   │   │       ├── detections.py   # Detection endpoints
│   │   │       ├── alter.py        # WebSocket endpoint
│   │   │       ├── streams.py      # Stream info endpoints
│   │   │       └── health.py       # Health check endpoints
│   │   ├── database/
│   │   │   ├── database.py         # Database setup
│   │   │   ├── schemas.py          # Pydantic schemas
│   │   │   └── models.py           # SQLAlchemy models
│   │   ├── models/
│   │   │   └── detection.py        # Detection model
│   │   └── repositories/
│   │       └── detection_repository.py  # Data access layer
│   └── tests/
│       ├── test_main.py            # Main app tests
│       ├── test_detections_websocket.py # WebSocket tests
│       └── conftest.py             # Test configuration
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Development Notes

### Database
- Uses SQLAlchemy ORM with SQLite for local development
- PostgreSQL in production (via environment variables)
- Migrations handled at startup via `Base.metadata.create_all()`

### CORS
- All origins allowed in development (`*`)
- Modify `CORSMiddleware` in `main.py` for production

### WebSocket Broadcasting
The `/detections/alter` endpoint maintains a connection manager that:
- Tracks all active WebSocket connections
- Broadcasts detection IDs to all connected clients when a new detection is created
- Automatically removes stale connections if sending fails

## Common Issues

### Port Already in Use
```bash
# Kill the process using port 8000 (macOS/Linux)
lsof -ti:8000 | xargs kill -9

# Or use a different port
uv run uvicorn app.main:app --reload --port 8001
```

### Database Locked
If you see SQLite locking errors during tests:
```bash
# Delete the test database
rm -f test.db

# Rerun tests
uv run pytest
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
