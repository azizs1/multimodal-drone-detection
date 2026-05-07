from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.incident_aggregate import IncidentAggregate


class IncidentAggregateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, aggregate: IncidentAggregate) -> IncidentAggregate:
        self.db.add(aggregate)
        self.db.commit()
        self.db.refresh(aggregate)
        return aggregate

    def save(self, aggregate: IncidentAggregate) -> IncidentAggregate:
        self.db.add(aggregate)
        self.db.commit()
        self.db.refresh(aggregate)
        return aggregate

    def get_by_aggregate_id(self, aggregate_id: str) -> IncidentAggregate | None:
        return (
            self.db.query(IncidentAggregate)
            .filter(IncidentAggregate.aggregate_id == aggregate_id)
            .first()
        )

    def get_latest_for_stream(self, stream_name: str) -> IncidentAggregate | None:
        return (
            self.db.query(IncidentAggregate)
            .filter(IncidentAggregate.stream_name == stream_name)
            .order_by(desc(IncidentAggregate.last_seen_at))
            .first()
        )

    def _apply_filters(
        self,
        query,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ):
        if decision:
            query = query.filter(IncidentAggregate.decision == decision)
        if stream_name:
            query = query.filter(IncidentAggregate.stream_name == stream_name)
        if from_ts:
            query = query.filter(IncidentAggregate.started_at >= from_ts)
        if to_ts:
            query = query.filter(IncidentAggregate.started_at <= to_ts)
        return query

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> list[IncidentAggregate]:
        query = self.db.query(IncidentAggregate)
        query = self._apply_filters(query, decision, stream_name, from_ts, to_ts)
        return query.order_by(desc(IncidentAggregate.last_seen_at)).offset(skip).limit(limit).all()

    def count(
        self,
        decision: str | None = None,
        stream_name: str | None = None,
        from_ts: datetime | None = None,
        to_ts: datetime | None = None,
    ) -> int:
        query = self.db.query(IncidentAggregate)
        query = self._apply_filters(query, decision, stream_name, from_ts, to_ts)
        return query.count()
