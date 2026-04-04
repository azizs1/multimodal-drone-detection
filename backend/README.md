# Backend API

The backend is a FastAPI service providing incident ingestion/query APIs, stream metadata endpoints, health checks, and real-time WebSocket alerts.

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

### Incident Management

#### Create Incident From Fusion
**POST** `/incidents`

Receives a fused decision payload from `fusion_service`, aggregates the payload into a persistence-friendly incident, and stores it in the database.

**Request:**
```json
{
  "incident_id": "incident-123",
  "has_drone": true,
  "fused_confidence": 0.83,
  "confidence_band": "high",
  "decision": "drone",
  "evidence": {
    "rgb": {
      "modality": "rgb",
      "timestamp": 1739994727.123,
      "bbox": [0.1, 0.2, 0.3, 0.4],
      "class_id": "drone",
      "confidence": 0.86,
      "embedding": null,
      "meta": {"sensor_id": "cam0"}
    },
    "thermal": null
  },
  "per_modality_scores": {
    "rgb": 0.86,
    "thermal": 0.79
  },
  "thresholds": {
    "alert": 0.75,
    "hold": 0.55
  },
  "gating_reason": "rgb+thermal",
  "latency_ms": 21.2,
  "media": {
    "rgb": {
      "frame_uri": "s3://detections/drone/frame_001.jpg",
      "thumbnail_uri": null
    },
    "thermal": null
  },
  "objects": [],
  "timestamp": 1739994727.123
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "incident_id": "incident-123",
  "detected_at": "2026-02-21T14:32:07Z",
  "source_timestamp": 1739994727.123,
  "has_drone": true,
  "decision": "drone",
  "confidence_band": "high",
  "alert_level": "high",
  "is_confirmed": true,
  "fused_confidence": 0.83,
  "stream_name": "fusion",
  "primary_frame_url": "s3://detections/drone/frame_001.jpg",
  "primary_thumbnail_url": null,
  "per_modality_scores": {
    "rgb": 0.86,
    "thermal": 0.79
  },
  "thresholds": {
    "alert": 0.75,
    "hold": 0.55
  },
  "gating_reason": "rgb+thermal",
  "latency_ms": 21.2,
  "evidence": {},
  "media": {},
  "objects": [],
  "created_at": "2026-02-21T14:32:07Z",
  "updated_at": "2026-02-21T14:32:07Z"
}
```

#### List Incidents
**GET** `/incidents`

List incident records with optional filtering.

**Query Parameters:**
- `skip` (int, default=0): Number of records to skip
- `limit` (int, default=100, max=1000): Maximum number of records to return
- `decision` (str, optional): Filter by `drone` or `none`
- `stream_name` (str, optional): Filter by stream name
- `from_ts` (datetime, optional): ISO timestamp lower bound
- `to_ts` (datetime, optional): ISO timestamp upper bound

#### Get Incident by ID
**GET** `/incidents/{incident_id}`

Retrieve a specific incident record by its incident id.

### WebSocket Endpoint (Real-time Updates)

#### Alert Endpoint
**WebSocket** `/detections/alert`

Connects to a WebSocket and receives incident alert payloads in real-time whenever a drone-positive incident is created.

**Usage Example (Python):**
```python
import asyncio
import websockets

async def listen_for_detections():
  async with websockets.connect("ws://localhost:8000/detections/alert") as ws:
        while True:
            alert_payload = await ws.recv()
            print(f"New incident alert: {alert_payload}")

asyncio.run(listen_for_detections())
```

**Usage Example (JavaScript):**
```javascript
const ws = new WebSocket("ws://localhost:8000/detections/alert");

ws.onmessage = (event) => {
  const alertPayload = JSON.parse(event.data);
  console.log("New incident alert:", alertPayload);
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
│   │   │       ├── incidents.py    # Incident endpoints
│   │   │       ├── alert.py        # WebSocket endpoint
│   │   │       ├── streams.py      # Stream info endpoints
│   │   │       └── health.py       # Health check endpoints
│   │   ├── database/
│   │   │   ├── database.py         # Database setup
│   │   │   ├── schemas.py          # Pydantic schemas
│   │   │   └── models.py           # SQLAlchemy models
│   │   ├── models/
│   │   │   └── incident.py         # Incident model
│   │   └── repositories/
│   │       └── incident_repository.py    # Incident data access layer
│   └── tests/
│       ├── test_main.py            # Main app tests
│       ├── test_incidents.py       # Incident API and WebSocket tests
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
The `/detections/alert` endpoint maintains a connection manager that:
- Tracks all active WebSocket connections
- Broadcasts incident alert payloads when a drone-positive incident is created
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
