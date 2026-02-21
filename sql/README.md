# PostgreSQL Database for Drone Detection System

This directory contains the PostgreSQL database setup for the multimodal drone detection system.

## Database Schema

The database is designed to store detection events, stream metadata, sensor information, and analytics.

### Tables

#### `detections`
Stores drone detection events with multimodal sensor data.

| Column               | Type         | Description                                     |
| -------------------- | ------------ | ----------------------------------------------- |
| `id`                 | UUID         | Primary key (auto-generated)                    |
| `timestamp`          | TIMESTAMPTZ  | Detection timestamp from sensor data            |
| `confidence`         | NUMERIC(4,3) | Overall detection confidence (0.0-1.0)          |
| `direction`          | VARCHAR(3)   | Cardinal direction (N, NE, E, SE, S, SW, W, NW) |
| `distance_ft`        | INTEGER      | Distance to detected drone in feet              |
| `visual_confidence`  | NUMERIC(4,3) | Visual sensor confidence (0.0-1.0)              |
| `thermal_confidence` | NUMERIC(4,3) | Thermal sensor confidence (0.0-1.0)             |
| `fused_score`        | NUMERIC(4,3) | Multimodal fusion score (0.0-1.0)               |
| `frame_snapshot_url` | TEXT         | S3 URL to saved frame snapshot                  |
| `created_at`         | TIMESTAMPTZ  | Record creation timestamp                       |
| `updated_at`         | TIMESTAMPTZ  | Record last update timestamp                    |

**Indexes:**
- `idx_detections_timestamp` - On `timestamp DESC` for time-based queries
- `idx_detections_confidence` - On `confidence DESC` for high-confidence queries
### Views

#### `high_confidence_detections`
Positive detections with `confidence >= 0.8`


## Connection Details

**Host:** `postgres` (within Docker network) or `localhost` (from host machine)
**Port:** `5432`
**Database:** `drone_detection`
**User:** `droneuser`
**Password:** `dronepass`

### Connection Strings

**PostgreSQL URL:**
```
postgresql://droneuser:dronepass@postgres:5432/drone_detection
```

**SQLAlchemy:**
```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://droneuser:dronepass@postgres:5432/drone_detection"
)
```

## Usage

### Starting the Database

```bash
# Start all services including database
docker-compose -f docker-compose-dev.yml up -d

# Check database status
docker-compose -f docker-compose-dev.yml ps postgres

# View database logs
docker logs postgres
```

### Connecting to the Database

**From host machine:**
```bash
psql -h localhost -p 5432 -U droneuser -d drone_detection
# Password: dronepass
```

**From within Docker:**
```bash
docker exec -it postgres psql -U droneuser -d drone_detection
```

### Example Queries

**Insert a detection:**
```sql
INSERT INTO detections (
    timestamp, drone_detected, confidence, direction, distance_ft,
    visual_confidence, thermal_confidence, fused_score, frame_snapshot_url
)
VALUES (
    '2026-04-15T14:32:07Z', true, 0.94, 'NE', 18,
    0.92, 0.89, 0.94, 'https://s3.amazonaws.com/bucket/detection_001.jpg'
);
```

**Get recent detections:**
```sql
SELECT * FROM detections
ORDER BY timestamp DESC
LIMIT 10;
```

**Get high-confidence positive detections:**
```sql
SELECT * FROM high_confidence_detections
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

**Count detections by hour:**
```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_detections,
    SUM(CASE WHEN drone_detected THEN 1 ELSE 0 END) as positive_detections,
    AVG(confidence) as avg_confidence
FROM detections
GROUP BY hour
ORDER BY hour DESC;
```

**Get detections by direction:**
```sql
SELECT
    direction,
    COUNT(*) as count,
    AVG(distance_ft) as avg_distance,
    AVG(confidence) as avg_confidence
FROM detections
WHERE drone_detected = true
GROUP BY direction
ORDER BY count DESC;
```

**Find detections with mismatched sensor confidence:**
```sql
SELECT *
FROM detections
WHERE drone_detected = true
  AND ABS(visual_confidence - thermal_confidence) > 0.2
ORDER BY timestamp DESC;
```

## Backup and Restore

### Backup
```bash
# Backup entire database
docker exec postgres pg_dump -U droneuser drone_detection > backup.sql

# Backup with compression
docker exec postgres pg_dump -U droneuser drone_detection | gzip > backup.sql.gz
```

### Restore
```bash
# Restore from backup
cat backup.sql | docker exec -i postgres psql -U droneuser -d drone_detection

# Restore from compressed backup
gunzip -c backup.sql.gz | docker exec -i postgres psql -U droneuser -d drone_detection
```

## Database Management

### Reset Database
```bash
# Stop containers
docker-compose -f docker-compose-dev.yml down

# Remove database volume
docker volume rm multimodal-drone-detection_postgres-data

# Restart (will reinitialize database)
docker-compose -f docker-compose-dev.yml up -d
```