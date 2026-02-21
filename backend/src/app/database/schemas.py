from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DirectionEnum(StrEnum):
    """Valid compass directions"""

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class DetectionCreate(BaseModel):
    """Schema for creating a new detection"""

    timestamp: datetime = Field(..., description="Time when detection occurred")
    drone_detected: bool = Field(..., description="Whether a drone was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    direction: DirectionEnum | None = Field(
        None, description="Direction of detected object (N, NE, E, SE, S, SW, W, NW)"
    )
    distance_ft: float | None = Field(
        None, gt=0.0, description="Distance in feet (must be positive)"
    )
    visual_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Visual sensor confidence"
    )
    thermal_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Thermal sensor confidence"
    )
    fused_score: float = Field(..., ge=0.0, le=1.0, description="Fused multimodal score")
    frame_snapshot_url: str | None = Field(None, description="URL to stored frame snapshot in S3")
    stream_name: str | None = Field(
        None, min_length=1, max_length=100, description="Name of the video stream"
    )

    @field_validator("frame_snapshot_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate that frame_snapshot_url is a valid URL or S3 path"""
        if v is None:
            return v
        if not (v.startswith("http://") or v.startswith("https://") or v.startswith("s3://")):
            raise ValueError("frame_snapshot_url must be a valid HTTP, HTTPS, or S3 URL")
        return v

    @field_validator("stream_name")
    @classmethod
    def validate_stream_name(cls, v: str | None) -> str | None:
        """Validate stream name contains only alphanumeric, dash, and underscore"""
        if v is None:
            return v
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "stream_name must contain only alphanumeric characters, dashes, and underscores"
            )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-21T14:32:07Z",
                "drone_detected": True,
                "confidence": 0.94,
                "direction": "NE",
                "distance_ft": 125.5,
                "visual_confidence": 0.92,
                "thermal_confidence": 0.89,
                "fused_score": 0.94,
                "frame_snapshot_url": "s3://detections/drone/2026-02-21/detection_123.jpg",
                "stream_name": "drone",
            }
        }


class DetectionResponse(BaseModel):
    """Schema for detection response"""

    id: int = Field(..., gt=0, description="Unique detection ID")
    timestamp: datetime = Field(..., description="Detection timestamp")
    drone_detected: bool = Field(..., description="Whether a drone was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    direction: str | None = Field(None, description="Direction of detected object")
    distance_ft: float | None = Field(None, description="Distance in feet")
    visual_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Visual sensor confidence"
    )
    thermal_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Thermal sensor confidence"
    )
    fused_score: float = Field(..., ge=0.0, le=1.0, description="Fused multimodal score")
    frame_snapshot_url: str | None = Field(None, description="URL to stored frame snapshot")
    stream_name: str | None = Field(None, description="Stream name")
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Last update time")

    class Config:
        from_attributes = True


class DetectionStats(BaseModel):
    """Schema for detection statistics"""

    total_detections: int = Field(..., ge=0, description="Total number of detections")
    drone_detections: int = Field(..., ge=0, description="Number of positive drone detections")
    non_drone_detections: int = Field(..., ge=0, description="Number of non-drone detections")
    stream_name: str | None = Field(None, description="Stream name if filtered")

    class Config:
        json_schema_extra = {
            "example": {
                "total_detections": 1500,
                "drone_detections": 342,
                "non_drone_detections": 1158,
                "stream_name": "drone",
            }
        }


# Query parameter models
class DetectionQueryParams(BaseModel):
    """Query parameters for listing detections"""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")
    stream_name: str | None = Field(None, description="Filter by stream name")
    drone_only: bool = Field(False, description="If true, only return positive drone detections")


# Stream schemas
class StreamInfo(BaseModel):
    """Schema for stream information"""

    name: str = Field(..., description="Stream name")
    description: str = Field(..., description="Stream description")
    rtsp_url: str = Field(..., description="RTSP streaming URL")
    hls_url: str = Field(..., description="HLS streaming URL")
    status: Literal["active", "inactive", "error"] = Field(..., description="Stream status")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "drone",
                "description": "Main drone detection stream",
                "rtsp_url": "rtsp://mediamtx:8554/drone",
                "hls_url": "http://mediamtx:8888/drone/index.m3u8",
                "status": "active",
            }
        }


class StreamListResponse(BaseModel):
    """Schema for stream list response"""

    streams: list[StreamInfo] = Field(..., description="List of available streams")
    total: int = Field(..., ge=0, description="Total number of streams")


# Health check schemas
class HealthCheckResponse(BaseModel):
    """Schema for basic health check"""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    timestamp: float = Field(..., gt=0, description="Unix timestamp")


class DatabaseHealthResponse(BaseModel):
    """Schema for database health check"""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    database: Literal["connected", "disconnected"] = Field(
        ..., description="Database connection status"
    )
    version: list[str] | None = Field(None, description="Database version")
    detections_table_exists: bool | None = Field(
        None, description="Whether detections table exists"
    )
    timestamp: float = Field(..., gt=0, description="Unix timestamp")
    error: str | None = Field(None, description="Error message if unhealthy")


class ReadinessCheckResponse(BaseModel):
    """Schema for readiness check"""

    status: Literal["ready", "not_ready"] = Field(..., description="Readiness status")
    reason: str | None = Field(None, description="Reason if not ready")
    timestamp: float = Field(..., gt=0, description="Unix timestamp")


class LivenessCheckResponse(BaseModel):
    """Schema for liveness check"""

    status: Literal["alive", "dead"] = Field(..., description="Liveness status")
    timestamp: str = Field(..., description="Timestamp string")
