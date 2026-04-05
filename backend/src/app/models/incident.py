import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(String(80), nullable=False, unique=True, index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_timestamp = Column(Float, nullable=False)
    has_drone = Column(Boolean, nullable=False)
    decision = Column(String(10), nullable=False)
    confidence_band = Column(String(10), nullable=False)
    alert_level = Column(String(10), nullable=False)
    is_confirmed = Column(Boolean, nullable=False)
    fused_confidence = Column(Float, nullable=False)
    stream_name = Column(String(100), nullable=False)
    primary_frame_url = Column(Text)
    primary_thumbnail_url = Column(Text)
    per_modality_scores = Column(JSON, nullable=False)
    thresholds = Column(JSON, nullable=False)
    gating_reason = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    evidence = Column(JSON, nullable=False)
    media = Column(JSON, nullable=False)
    objects = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": str(self.id),
            "incident_id": self.incident_id,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "source_timestamp": self.source_timestamp,
            "has_drone": self.has_drone,
            "decision": self.decision,
            "confidence_band": self.confidence_band,
            "alert_level": self.alert_level,
            "is_confirmed": self.is_confirmed,
            "fused_confidence": self.fused_confidence,
            "stream_name": self.stream_name,
            "primary_frame_url": self.primary_frame_url,
            "primary_thumbnail_url": self.primary_thumbnail_url,
            "per_modality_scores": self.per_modality_scores,
            "thresholds": self.thresholds,
            "gating_reason": self.gating_reason,
            "latency_ms": self.latency_ms,
            "evidence": self.evidence,
            "media": self.media,
            "objects": self.objects,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
