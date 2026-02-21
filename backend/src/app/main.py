from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import DetectionRepository
from app.schemas import DetectionCreate, DetectionResponse

app = FastAPI(title="Multimodal Drone Detection API")

# Available stream configurations
STREAMS = {
    "drone": {
        "name": "drone",
        "description": "Main drone detection stream",
        "rtsp_url": "rtsp://localhost:8554/drone",
        "hls_url": "http://localhost:8888/drone/index.m3u8",
        "hls_player": "http://localhost:8888/drone/",  # Built-in player
    }
}


@app.get("/")
async def root():
    return {
        "message": "Multimodal Drone Detection API",
        "version": "1.0.0",
        "endpoints": {
            "streams": "/streams",
            "stream_info": "/info/{stream_name}",
            "health": "/health",
            "detections": "/detections",
            "detection_stats": "/detections/stats/count",
        },
        "quick_links": {
            "watch_stream": "http://localhost:8888/drone/",
            "hls_url": "http://localhost:8888/drone/index.m3u8",
        },
    }


@app.get("/streams")
async def list_streams():
    """List all available streams"""
    return {"streams": list(STREAMS.values()), "count": len(STREAMS)}


@app.get("/info/{stream_name}")
async def get_stream(stream_name: str):
    """Get HLS and RTSP URLs for a specific stream"""
    if stream_name in STREAMS:
        return STREAMS[stream_name]
    return {
        "error": "Stream not found",
        "stream": stream_name,
        "available_streams": list(STREAMS.keys()),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mediamtx_rtsp": "mediamtx:8554",
        "mediamtx_hls": "mediamtx:8888",
    }


# ============ Detection Endpoints ============

@app.post("/detections", response_model=DetectionResponse, status_code=201)
async def create_detection(
    detection: DetectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new detection record"""
    repo = DetectionRepository(db)
    db_detection = repo.create(detection)
    return db_detection


@app.get("/detections/{detection_id}", response_model=DetectionResponse)
async def get_detection(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Get a detection by ID"""
    repo = DetectionRepository(db)
    detection = repo.get_by_id(detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection


@app.get("/detections", response_model=List[DetectionResponse])
async def list_detections(
    skip: int = 0,
    limit: int = 100,
    stream_name: Optional[str] = None,
    drone_only: bool = False,
    db: Session = Depends(get_db)
):
    """List detections with optional filters"""
    repo = DetectionRepository(db)

    if drone_only:
        detections = repo.get_drone_detections(skip=skip, limit=limit)
    elif stream_name:
        detections = repo.get_by_stream(stream_name, skip=skip, limit=limit)
    else:
        detections = repo.get_all(skip=skip, limit=limit)

    return detections


@app.delete("/detections/{detection_id}", status_code=204)
async def delete_detection(
    detection_id: int,
    db: Session = Depends(get_db)
):
    """Delete a detection by ID"""
    repo = DetectionRepository(db)
    deleted = repo.delete(detection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Detection not found")
    return None


@app.get("/detections/stats/count")
async def get_detection_stats(
    stream_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detection statistics"""
    repo = DetectionRepository(db)

    if stream_name:
        total = repo.count_by_stream(stream_name)
    else:
        total = repo.count()

    drone_detections = len(repo.get_drone_detections(limit=10000))

    return {
        "total_detections": total,
        "drone_detections": drone_detections,
        "non_drone_detections": total - drone_detections,
    }
