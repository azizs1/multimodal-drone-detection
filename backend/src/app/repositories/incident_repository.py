from datetime import datetime
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.schemas import IncidentCreate
from app.models.incident import Incident


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, incident: IncidentCreate) -> Incident:
        db_incident = Incident(**incident.model_dump())
        self.db.add(db_incident)
        self.db.commit()
        self.db.refresh(db_incident)
        return db_incident

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def get_by_incident_id(self, incident_id: str) -> Incident | None:
        return self.db.query(Incident).filter(Incident.incident_id == incident_id).first()

    def _apply_filters(
        self,
        query,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ):
        if decision:
            query = query.filter(Incident.decision == decision)
        if stream_name:
            query = query.filter(Incident.stream_name == stream_name)
        if from_ts:
            query = query.filter(Incident.detected_at >= from_ts)
        if to_ts:
            query = query.filter(Incident.detected_at <= to_ts)
        return query

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> list[Incident]:
        query = self.db.query(Incident)
        query = self._apply_filters(query, decision, stream_name, from_ts, to_ts)
        return query.order_by(desc(Incident.detected_at)).offset(skip).limit(limit).all()

    def count(
        self,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> int:
        query = self.db.query(Incident)
        query = self._apply_filters(query, decision, stream_name, from_ts, to_ts)
        return query.count()
