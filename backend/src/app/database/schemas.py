from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Stream schemas
class StreamInfo(BaseModel):
    """Schema for stream information"""

    name: str = Field(..., description="Stream name")
    description: str = Field(..., description="Stream description")
    rtsp_url: str = Field(..., description="RTSP streaming URL")
    hls_url: str = Field(..., description="HLS streaming URL")
    webrtc_url: str | None = Field(None, description="MediaMTX WebRTC viewer URL")
    width: int | None = Field(None, ge=1, description="Stream frame width in pixels")
    height: int | None = Field(None, ge=1, description="Stream frame height in pixels")
    fps: int | None = Field(None, ge=1, description="Expected stream frames per second")
    status: Literal["active", "inactive", "error"] = Field(..., description="Stream status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "drone",
                "description": "Main drone detection stream",
                "rtsp_url": "rtsp://mediamtx:8554/drone",
                "hls_url": "http://mediamtx:8888/drone/index.m3u8",
                "webrtc_url": "http://mediamtx:9998/drone/",
                "width": 1280,
                "height": 720,
                "fps": 15,
                "status": "active",
            }
        }
    )


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
    incidents_table_exists: bool | None = Field(None, description="Whether incidents table exists")
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


# Fusion / incident schemas
Modality = Literal["rgb", "thermal"]
Decision = Literal["drone", "none"]
ConfidenceBand = Literal["low", "medium", "high"]


class FusionModalityPrediction(BaseModel):
    modality: Modality
    timestamp: float = Field(..., description="Unix epoch seconds (float)")
    bbox: tuple[float, float, float, float] | None = Field(
        None, description="[x1,y1,x2,y2] in pixels or normalized"
    )
    class_id: str = Field(..., description="class label, e.g. 'drone'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    embedding: list[float] | None = None
    meta: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class FusionMediaRef(BaseModel):
    frame_uri: str | None = None
    thumbnail_uri: str | None = None

    model_config = ConfigDict(extra="forbid")


def _default_fusion_media_map() -> dict[Modality, FusionMediaRef | None]:
    return {"rgb": None, "thermal": None}


class FusionObjectConfidence(BaseModel):
    object_id: str = Field(..., description="stable object id within this fused response")
    modality: Modality
    class_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: tuple[float, float, float, float] | None = None
    timestamp: float

    model_config = ConfigDict(extra="forbid")


class FusedDecisionIngest(BaseModel):
    incident_id: str = Field(..., description="stable id for logging / dashboard")
    has_drone: bool = Field(
        ..., description="True if any object in this frame is classified as drone"
    )
    fused_confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_band: ConfidenceBand
    decision: Decision
    evidence: dict[Modality, FusionModalityPrediction | None]
    per_modality_scores: dict[Modality, float]
    thresholds: dict[str, float]
    gating_reason: str
    latency_ms: float = Field(..., ge=0.0)
    media: dict[Modality, FusionMediaRef | None] = Field(default_factory=_default_fusion_media_map)
    objects: list[FusionObjectConfidence] = Field(default_factory=list)
    timestamp: float = Field(..., description="Unix epoch seconds")

    model_config = ConfigDict(extra="forbid")


class IncidentCreate(BaseModel):
    incident_id: str = Field(..., description="Stable external incident id")
    detected_at: datetime = Field(..., description="Incident timestamp")
    source_timestamp: float = Field(..., ge=0.0, description="Original fused timestamp")
    has_drone: bool
    decision: Decision
    confidence_band: ConfidenceBand
    alert_level: ConfidenceBand
    is_confirmed: bool
    fused_confidence: float = Field(..., ge=0.0, le=1.0)
    stream_name: str = Field(..., min_length=1, max_length=100)
    primary_frame_url: str | None = None
    primary_thumbnail_url: str | None = None
    per_modality_scores: dict[Modality, float]
    thresholds: dict[str, float]
    gating_reason: str
    latency_ms: float = Field(..., ge=0.0)
    evidence: dict[Modality, FusionModalityPrediction | None]
    media: dict[Modality, FusionMediaRef | None]
    objects: list[FusionObjectConfidence]

    model_config = ConfigDict(extra="forbid")


class IncidentResponse(BaseModel):
    id: UUID = Field(..., description="Unique incident row id")
    incident_id: str
    detected_at: datetime
    source_timestamp: float
    has_drone: bool
    decision: Decision
    confidence_band: ConfidenceBand
    alert_level: ConfidenceBand
    is_confirmed: bool
    fused_confidence: float
    stream_name: str
    primary_frame_url: str | None = None
    primary_thumbnail_url: str | None = None
    per_modality_scores: dict[Modality, float]
    thresholds: dict[str, float]
    gating_reason: str
    latency_ms: float
    evidence: dict[Modality, FusionModalityPrediction | None]
    media: dict[Modality, FusionMediaRef | None]
    objects: list[FusionObjectConfidence]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentAggregateResponse(BaseModel):
    id: UUID = Field(..., description="Unique aggregate row id")
    aggregate_id: str
    incident_id: str = Field(..., description="Compatibility id for incident views")
    stream_name: str
    started_at: datetime
    last_seen_at: datetime
    ended_at: datetime | None = None
    detected_at: datetime = Field(..., description="Compatibility timestamp for incident views")
    source_timestamp: float = Field(..., description="Last seen timestamp as Unix epoch seconds")
    decision: Decision
    has_drone: bool
    confidence_band: ConfidenceBand
    alert_level: ConfidenceBand
    is_confirmed: bool
    fused_confidence: float
    avg_fused_confidence: float
    frame_count: int
    drone_frame_count: int
    representative_incident_id: str
    raw_incident_ids: list[str]
    primary_frame_url: str | None = None
    primary_thumbnail_url: str | None = None
    per_modality_scores: dict[Modality, float]
    thresholds: dict[str, float]
    gating_reason: str
    latency_ms: float
    evidence: dict[Modality, FusionModalityPrediction | None]
    media: dict[Modality, FusionMediaRef | None]
    objects: list[FusionObjectConfidence]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
