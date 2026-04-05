from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.routers.alert import alert_connection_manager
from app.database.database import get_db
from app.database.schemas import FusedDecisionIngest, IncidentResponse
from app.repositories import IncidentRepository
from app.services.incident_aggregator import aggregate_fused_decision

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident from fused inference",
    description="Receives a fused decision payload, aggregates it, and persists an incident.",
)
async def create_incident(
    payload: FusedDecisionIngest,
    db: Annotated[Session, Depends(get_db)],
):
    repo = IncidentRepository(db)
    existing = repo.get_by_incident_id(payload.incident_id)
    if existing:
        return existing

    incident_create = aggregate_fused_decision(payload)
    db_incident = repo.create(incident_create)

    if incident_create.has_drone is True and incident_create.decision == "drone":
        websocket_payload = {
            "incident_id": db_incident.incident_id,
            "decision": db_incident.decision,
            "fused_confidence": db_incident.fused_confidence,
            "confidence_band": db_incident.confidence_band,
            "gating_reason": db_incident.gating_reason,
            "timestamp": db_incident.source_timestamp,
            "per_modality_scores": db_incident.per_modality_scores,
            "latency_ms": db_incident.latency_ms,
            "media": db_incident.media,
            "objects": db_incident.objects,
        }
        await alert_connection_manager.broadcast_alert(websocket_payload)

    return db_incident


@router.get(
    "",
    response_model=list[IncidentResponse],
    summary="List incidents",
    description="List incident records with optional filtering.",
)
async def list_incidents(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum records to return")] = 100,
    decision: Annotated[
        Literal["drone", "none"] | None, Query(description="Filter by decision")
    ] = None,
    stream_name: Annotated[
        str | None, Query(min_length=1, max_length=100, description="Filter by stream name")
    ] = None,
    from_ts: Annotated[
        datetime | None, Query(description="Filter incidents detected after this timestamp")
    ] = None,
    to_ts: Annotated[
        datetime | None, Query(description="Filter incidents detected before this timestamp")
    ] = None,
):
    repo = IncidentRepository(db)

    return repo.list(
        skip=skip,
        limit=limit,
        decision=decision,
        stream_name=stream_name,
        from_ts=from_ts,
        to_ts=to_ts,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident by incident id",
    description="Retrieve a specific incident record by its incident id.",
)
async def get_incident(
    incident_id: Annotated[str, Path(description="The incident id to retrieve")],
    db: Annotated[Session, Depends(get_db)],
):
    repo = IncidentRepository(db)
    incident = repo.get_by_incident_id(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id {incident_id} not found",
        )
    return incident
