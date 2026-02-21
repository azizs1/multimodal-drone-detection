from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.schemas import DetectionCreate, DetectionResponse, DetectionStats
from app.repositories import DetectionRepository

router = APIRouter(
    prefix="/detections",
    tags=["detections"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=DetectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new detection record",
    description="Creates a new drone detection record with all associated metrics",
)
async def create_detection(detection: DetectionCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Create a new detection record with the following information:

    - **timestamp**: Time when detection occurred
    - **drone_detected**: Whether a drone was detected
    - **confidence**: Overall confidence score (0-1)
    - **direction**: Direction of detected object (e.g., "NE", "SW")
    - **distance_ft**: Distance in feet
    - **visual_confidence**: Visual sensor confidence (0-1)
    - **thermal_confidence**: Thermal sensor confidence (0-1)
    - **fused_score**: Fused multimodal score (0-1)
    - **frame_snapshot_url**: URL to stored frame snapshot
    - **stream_name**: Name of the video stream
    """
    repo = DetectionRepository(db)
    db_detection = repo.create(detection)
    return db_detection


@router.get(
    "/{detection_id}",
    response_model=DetectionResponse,
    summary="Get detection by ID",
    description="Retrieve a specific detection record by its ID",
)
async def get_detection(
    detection_id: Annotated[int, Path(gt=0, description="The ID of the detection to retrieve")],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a single detection record by ID"""
    repo = DetectionRepository(db)
    detection = repo.get_by_id(detection_id)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with id {detection_id} not found",
        )
    return detection


@router.get(
    "",
    response_model=list[DetectionResponse],
    summary="List detections",
    description="List all detection records with optional filtering",
)
async def list_detections(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0, description="Number of records to skip (pagination)")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=1000, description="Maximum number of records to return")
    ] = 100,
    stream_name: Annotated[
        str | None, Query(min_length=1, max_length=100, description="Filter by stream name")
    ] = None,
    drone_only: Annotated[
        bool, Query(description="If true, only return positive drone detections")
    ] = False,
):
    """
    List detections with optional filters:

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (1-1000)
    - **stream_name**: Filter by stream name (e.g., "drone")
    - **drone_only**: If true, only return positive drone detections
    """
    repo = DetectionRepository(db)

    if drone_only:
        detections = repo.get_drone_detections(skip=skip, limit=limit)
    elif stream_name:
        detections = repo.get_by_stream(stream_name, skip=skip, limit=limit)
    else:
        detections = repo.get_all(skip=skip, limit=limit)

    return detections


@router.delete(
    "/{detection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a detection",
    description="Delete a detection record by ID",
)
async def delete_detection(
    detection_id: Annotated[int, Path(gt=0, description="The ID of the detection to delete")],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a detection record"""
    repo = DetectionRepository(db)
    deleted = repo.delete(detection_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Detection with id {detection_id} not found",
        )
    return None


@router.get(
    "/stats/summary",
    response_model=DetectionStats,
    summary="Get detection statistics",
    description="Get aggregated statistics about detections",
)
async def get_detection_stats(
    db: Annotated[Session, Depends(get_db)],
    stream_name: Annotated[
        str | None,
        Query(min_length=1, max_length=100, description="Optional filter by stream name"),
    ] = None,
):
    """
    Get detection statistics:

    - **total_detections**: Total number of detection records
    - **drone_detections**: Number of positive drone detections
    - **non_drone_detections**: Number of non-drone detections
    - **stream_name**: Optional filter by stream name
    """
    repo = DetectionRepository(db)

    total = repo.count_by_stream(stream_name) if stream_name else repo.count()

    drone_detections = len(repo.get_drone_detections(limit=10000))

    return DetectionStats(
        total_detections=total,
        drone_detections=drone_detections,
        non_drone_detections=total - drone_detections,
        stream_name=stream_name,
    )
