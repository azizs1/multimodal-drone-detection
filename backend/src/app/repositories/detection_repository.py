from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.detection import Detection
from app.schemas import DetectionCreate


class DetectionRepository:
    """Repository for Detection model operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, detection: DetectionCreate) -> Detection:
        """Create a new detection record"""
        db_detection = Detection(**detection.model_dump())
        self.db.add(db_detection)
        self.db.commit()
        self.db.refresh(db_detection)
        return db_detection

    def get_by_id(self, detection_id: int) -> Optional[Detection]:
        """Get detection by ID"""
        return self.db.query(Detection).filter(Detection.id == detection_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Detection]:
        """Get all detections with pagination"""
        return self.db.query(Detection)\
            .order_by(desc(Detection.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_stream(self, stream_name: str, skip: int = 0, limit: int = 100) -> List[Detection]:
        """Get detections by stream name"""
        return self.db.query(Detection)\
            .filter(Detection.stream_name == stream_name)\
            .order_by(desc(Detection.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_drone_detections(self, skip: int = 0, limit: int = 100) -> List[Detection]:
        """Get only positive drone detections"""
        return self.db.query(Detection)\
            .filter(Detection.drone_detected == True)\
            .order_by(desc(Detection.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()

    def count(self) -> int:
        """Count total detections"""
        return self.db.query(Detection).count()

    def count_by_stream(self, stream_name: str) -> int:
        """Count detections by stream"""
        return self.db.query(Detection)\
            .filter(Detection.stream_name == stream_name)\
            .count()

    def delete(self, detection_id: int) -> bool:
        """Delete a detection by ID"""
        detection = self.get_by_id(detection_id)
        if detection:
            self.db.delete(detection)
            self.db.commit()
            return True
        return False

    def update(self, detection_id: int, **kwargs) -> Optional[Detection]:
        """Update detection fields"""
        detection = self.get_by_id(detection_id)
        if detection:
            for key, value in kwargs.items():
                if hasattr(detection, key):
                    setattr(detection, key, value)
            self.db.commit()
            self.db.refresh(detection)
            return detection
        return None
