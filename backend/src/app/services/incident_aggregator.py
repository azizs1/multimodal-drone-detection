from datetime import datetime, timezone

from app.database.schemas import (
    ConfidenceBand,
    FusedDecisionIngest,
    FusionMediaRef,
    IncidentCreate,
    Modality,
)


def aggregate_fused_decision(payload: FusedDecisionIngest) -> IncidentCreate:
    detected_at = datetime.fromtimestamp(payload.timestamp, tz=timezone.utc)
    primary_frame_url, primary_thumbnail_url = _pick_primary_media_url(payload.media)
    alert_level = _derive_alert_level(payload.fused_confidence, payload.thresholds)
    is_confirmed = payload.decision == "drone" and payload.has_drone

    return IncidentCreate(
        incident_id=payload.incident_id,
        detected_at=detected_at,
        source_timestamp=payload.timestamp,
        has_drone=payload.has_drone,
        decision=payload.decision,
        confidence_band=payload.confidence_band,
        alert_level=alert_level,
        is_confirmed=is_confirmed,
        fused_confidence=payload.fused_confidence,
        stream_name="fusion",
        primary_frame_url=primary_frame_url,
        primary_thumbnail_url=primary_thumbnail_url,
        per_modality_scores=payload.per_modality_scores,
        thresholds=payload.thresholds,
        gating_reason=payload.gating_reason,
        latency_ms=payload.latency_ms,
        evidence=payload.evidence,
        media=payload.media,
        objects=payload.objects,
    )


def _pick_primary_media_url(
    media: dict[Modality, FusionMediaRef | None],
) -> tuple[str | None, str | None]:
    rgb_media = media.get("rgb")
    if rgb_media is not None:
        frame_uri = getattr(rgb_media, "frame_uri", None)
        thumbnail_uri = getattr(rgb_media, "thumbnail_uri", None)
        if frame_uri or thumbnail_uri:
            return frame_uri, thumbnail_uri

    thermal_media = media.get("thermal")
    if thermal_media is not None:
        frame_uri = getattr(thermal_media, "frame_uri", None)
        thumbnail_uri = getattr(thermal_media, "thumbnail_uri", None)
        if frame_uri or thumbnail_uri:
            return frame_uri, thumbnail_uri

    return None, None


def _derive_alert_level(confidence: float, thresholds: dict[str, float]) -> ConfidenceBand:
    alert_threshold = thresholds.get("alert", 0.75)
    hold_threshold = thresholds.get("hold", 0.55)
    if confidence >= alert_threshold:
        return "high"
    if confidence >= hold_threshold:
        return "medium"
    return "low"
