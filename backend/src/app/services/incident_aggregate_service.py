import uuid
from datetime import timedelta

from app.models.incident import Incident
from app.models.incident_aggregate import IncidentAggregate
from app.repositories import IncidentAggregateRepository
from sqlalchemy.orm import Session

AGGREGATION_WINDOW_SECONDS = 5
DRONE_GAP_SECONDS = 10


def aggregate_incident_frame(db: Session, incident: Incident) -> IncidentAggregate | None:
    if incident.decision != "drone":
        return None

    repo = IncidentAggregateRepository(db)
    latest = repo.get_latest_for_stream(incident.stream_name)
    if latest and _is_within_active_event(latest, incident):
        return _update_aggregate(repo, latest, incident)

    return repo.create(_new_aggregate(incident))


def _is_within_active_event(aggregate: IncidentAggregate, incident: Incident) -> bool:
    gap = abs(incident.detected_at - aggregate.last_seen_at)
    return gap <= timedelta(seconds=DRONE_GAP_SECONDS)


def _new_aggregate(incident: Incident) -> IncidentAggregate:
    return IncidentAggregate(
        aggregate_id=f"agg-{uuid.uuid4()}",
        stream_name=incident.stream_name,
        started_at=incident.detected_at,
        last_seen_at=incident.detected_at,
        ended_at=incident.detected_at,
        decision="drone",
        has_drone=True,
        confidence_band=incident.confidence_band,
        alert_level=incident.alert_level,
        is_confirmed=True,
        fused_confidence=incident.fused_confidence,
        avg_fused_confidence=incident.fused_confidence,
        frame_count=1,
        drone_frame_count=1,
        representative_incident_id=incident.incident_id,
        raw_incident_ids=[incident.incident_id],
        primary_frame_url=incident.primary_frame_url,
        primary_thumbnail_url=incident.primary_thumbnail_url,
        per_modality_scores=incident.per_modality_scores,
        thresholds=incident.thresholds,
        gating_reason=incident.gating_reason,
        latency_ms=incident.latency_ms,
        evidence=incident.evidence,
        media=incident.media,
        objects=incident.objects,
    )


def _update_aggregate(
    repo: IncidentAggregateRepository,
    aggregate: IncidentAggregate,
    incident: Incident,
) -> IncidentAggregate:
    previous_count = aggregate.frame_count
    next_count = previous_count + 1
    aggregate.frame_count = next_count
    aggregate.drone_frame_count += 1
    aggregate.avg_fused_confidence = (
        (aggregate.avg_fused_confidence * previous_count) + incident.fused_confidence
    ) / next_count
    aggregate.per_modality_scores = _average_modality_scores(
        aggregate.per_modality_scores,
        incident.per_modality_scores,
        previous_count,
        next_count,
    )
    aggregate.last_seen_at = max(aggregate.last_seen_at, incident.detected_at)
    aggregate.ended_at = aggregate.last_seen_at
    aggregate.raw_incident_ids = [*aggregate.raw_incident_ids, incident.incident_id]

    if incident.fused_confidence > aggregate.fused_confidence:
        aggregate.representative_incident_id = incident.incident_id
        aggregate.fused_confidence = incident.fused_confidence
        aggregate.confidence_band = incident.confidence_band
        aggregate.alert_level = incident.alert_level
        aggregate.primary_frame_url = incident.primary_frame_url
        aggregate.primary_thumbnail_url = incident.primary_thumbnail_url
        aggregate.thresholds = incident.thresholds
        aggregate.gating_reason = incident.gating_reason
        aggregate.latency_ms = incident.latency_ms
        aggregate.evidence = incident.evidence
        aggregate.media = incident.media
        aggregate.objects = incident.objects

    return repo.save(aggregate)


def _average_modality_scores(
    current_scores: dict[str, float],
    next_scores: dict[str, float],
    previous_count: int,
    next_count: int,
) -> dict[str, float]:
    modalities = set(current_scores) | set(next_scores)
    return {
        modality: (
            (current_scores.get(modality, 0.0) * previous_count) + next_scores.get(modality, 0.0)
        )
        / next_count
        for modality in modalities
    }
