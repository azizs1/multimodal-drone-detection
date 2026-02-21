from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DetectionCreate(BaseModel):
    """Schema for creating a new detection"""
    timestamp: datetime
    drone_detected: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    direction: Optional[str] = None
    distance_ft: Optional[float] = None
    visual_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    thermal_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    fused_score: float = Field(..., ge=0.0, le=1.0)
    frame_snapshot_url: Optional[str] = None
    stream_name: Optional[str] = None


class DetectionResponse(BaseModel):
    """Schema for detection response"""
    id: int
    timestamp: datetime
    drone_detected: bool
    confidence: float
    direction: Optional[str] = None
    distance_ft: Optional[float] = None
    visual_confidence: Optional[float] = None
    thermal_confidence: Optional[float] = None
    fused_score: float
    frame_snapshot_url: Optional[str] = None
    stream_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
