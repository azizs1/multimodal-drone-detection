"""Simple data contracts for fusion inputs/outputs (Pydantic for FastAPI)."""
from typing import Dict, List, Literal, Optional, Tuple
import time
from pydantic import BaseModel, Field

Modality = Literal["rgb", "thermal"]
Decision = Literal["drone", "none"]
ConfidenceBand = Literal["low", "medium", "high"]


class ModalityPrediction(BaseModel):
    modality: Modality
    timestamp: float = Field(..., description="Unix epoch seconds (float)")
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        None, description="[x1,y1,x2,y2] in pixels or normalized"
    )
    class_id: str = Field(..., description="class label, e.g., 'drone'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    embedding: Optional[List[float]] = None
    meta: Dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class MediaRef(BaseModel):
    frame_uri: Optional[str] = Field(
        None, description="Path or URL for frame image associated with this decision"
    )
    thumbnail_uri: Optional[str] = None

    model_config = {"extra": "forbid"}


class FusedDecision(BaseModel):
    incident_id: str = Field(..., description="stable id for logging / dashboard")
    fused_confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_band: ConfidenceBand
    decision: Decision
    evidence: Dict[Modality, Optional[ModalityPrediction]]
    per_modality_scores: Dict[Modality, float]
    thresholds: Dict[str, float]
    gating_reason: str
    latency_ms: float
    media: Dict[Modality, Optional[MediaRef]] = Field(
        default_factory=lambda: {"rgb": None, "thermal": None}
    )
    timestamp: float = Field(default_factory=lambda: time.time())

    model_config = {"extra": "forbid"}
