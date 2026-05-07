import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database.database import Base


class IncidentAggregate(Base):
    __tablename__ = "incident_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(String(80), nullable=False, unique=True, index=True)
    stream_name = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    decision = Column(String(10), nullable=False, index=True)
    has_drone = Column(Boolean, nullable=False)
    confidence_band = Column(String(10), nullable=False)
    alert_level = Column(String(10), nullable=False)
    is_confirmed = Column(Boolean, nullable=False)
    fused_confidence = Column(Float, nullable=False)
    avg_fused_confidence = Column(Float, nullable=False)
    frame_count = Column(Integer, nullable=False)
    drone_frame_count = Column(Integer, nullable=False)
    representative_incident_id = Column(String(80), nullable=False)
    raw_incident_ids = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    primary_frame_url = Column(Text)
    primary_thumbnail_url = Column(Text)
    per_modality_scores = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    thresholds = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    gating_reason = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=False)
    evidence = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    media = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    objects = Column(JSONB().with_variant(JSON, "sqlite"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index(
            "idx_incident_aggregates_last_seen_at",
            "last_seen_at",
            postgresql_using="btree",
        ),
    )

    @property
    def incident_id(self) -> str:
        return self.aggregate_id

    @property
    def detected_at(self):
        return self.started_at

    @property
    def source_timestamp(self) -> float:
        return self.last_seen_at.timestamp()
