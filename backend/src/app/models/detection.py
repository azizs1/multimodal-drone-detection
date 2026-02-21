from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database.database import Base


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    drone_detected = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    direction = Column(String(10))
    distance_ft = Column(Float)
    visual_confidence = Column(Float)
    thermal_confidence = Column(Float)
    fused_score = Column(Float, nullable=False)
    frame_snapshot_url = Column(Text)
    stream_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "drone_detected": self.drone_detected,
            "confidence": self.confidence,
            "direction": self.direction,
            "distance_ft": self.distance_ft,
            "visual_confidence": self.visual_confidence,
            "thermal_confidence": self.thermal_confidence,
            "fused_score": self.fused_score,
            "frame_snapshot_url": self.frame_snapshot_url,
            "stream_name": self.stream_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
