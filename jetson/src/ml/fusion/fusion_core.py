"""Weighted late-fusion with gating (design stub for Sprint 1)."""

from __future__ import annotations

import time
import uuid
from collections import deque
from collections.abc import Iterable

from .config import DEFAULT_CONFIG, FusionConfig
from .schemas import (
    ConfidenceBand,
    FusedDecision,
    FusedObjectConfidence,
    MediaRef,
    ModalityPrediction,
)


class FusionEngine:
    TARGET_CLASS = "drone"

    def __init__(self, config: FusionConfig = DEFAULT_CONFIG):
        self.config = config
        self.fused_history = deque(maxlen=config.buffer_size)

    def fuse(self, preds: Iterable[ModalityPrediction]) -> FusedDecision | None:
        filtered = [p for p in preds if p]
        if not filtered:
            return None

        now = time.time()

        score, reason, per_modality_scores = self._weighted_score(filtered)
        decision = self._gate(score, filtered)
        latency_ms = (time.time() - now) * 1000

        fused_conf_band = self._band(score)

        evidence = self._latest_by_modality(filtered)
        fused = FusedDecision(
            incident_id=str(uuid.uuid4()),
            has_drone=any(p.class_id == self.TARGET_CLASS for p in filtered),
            fused_confidence=score,
            confidence_band=fused_conf_band,
            decision=decision,
            evidence=evidence,
            per_modality_scores=per_modality_scores,
            thresholds={
                "alert": self.config.alert_threshold,
                "hold": self.config.hold_threshold,
            },
            gating_reason=reason,
            latency_ms=latency_ms,
            media=self._media_from_evidence(evidence),
            objects=self._objects_from_preds(filtered),
        )
        self.fused_history.append(fused)

        if self._debounce(fused):
            return fused
        return None

    def _weighted_score(
        self, preds: list[ModalityPrediction]
    ) -> tuple[float, str, dict[str, float]]:
        weights = self.config.weights
        gates = self.config.per_modality_gates
        per_modality_scores = {"rgb": 0.0, "thermal": 0.0}
        for p in preds:
            if p.class_id != self.TARGET_CLASS:
                continue
            per_modality_scores[p.modality] = max(per_modality_scores[p.modality], p.confidence)

        score = 0.0
        used: list[str] = []
        for modality, conf in per_modality_scores.items():
            gate = gates.get(modality, 0.0)
            if conf < gate:
                continue
            score += weights.get(modality, 0.0) * conf
            used.append(modality)

        score = max(0.0, min(1.0, score))
        reason = "no-modality-passed-gate" if not used else "+".join(sorted(set(used)))
        return score, reason, per_modality_scores

    def _gate(self, score: float, preds: list[ModalityPrediction]) -> str:
        if score >= self.config.alert_threshold:
            # optional EO/IR confirmation
            if self.config.eo_ir_required:
                thermal_gate = self.config.per_modality_gates.get("thermal", 0.0)
                has_thermal = any(
                    p.modality == "thermal"
                    and p.class_id == self.TARGET_CLASS
                    and p.confidence >= thermal_gate
                    for p in preds
                )
                if not has_thermal:
                    return "none"
            return "drone"
        if score >= self.config.hold_threshold:
            return "none"  # hold/buffer state is handled by caller; no alert yet
        return "none"

    def _latest_by_modality(
        self, preds: list[ModalityPrediction]
    ) -> dict[str, ModalityPrediction | None]:
        latest = {"rgb": None, "thermal": None}
        for p in preds:
            if latest[p.modality] is None or p.timestamp > latest[p.modality].timestamp:
                latest[p.modality] = p
        return latest

    def _objects_from_preds(self, preds: list[ModalityPrediction]) -> list[FusedObjectConfidence]:
        objects: list[FusedObjectConfidence] = []
        for idx, pred in enumerate(preds):
            object_id = (
                pred.meta.get("object_id")
                or pred.meta.get("track_id")
                or pred.meta.get("frame_id")
                or f"{pred.modality}-{idx}"
            )
            objects.append(
                FusedObjectConfidence(
                    object_id=object_id,
                    modality=pred.modality,
                    class_id=pred.class_id,
                    confidence=pred.confidence,
                    bbox=pred.bbox,
                    timestamp=pred.timestamp,
                )
            )
        return objects

    def _media_from_evidence(
        self, evidence: dict[str, ModalityPrediction | None]
    ) -> dict[str, MediaRef | None]:
        media: dict[str, MediaRef | None] = {"rgb": None, "thermal": None}
        for modality, pred in evidence.items():
            if pred is None:
                continue
            frame_uri = pred.meta.get("frame_uri")
            if frame_uri:
                media[modality] = MediaRef(frame_uri=frame_uri)
        return media

    def _debounce(self, fused: FusedDecision) -> bool:
        if fused.decision != "drone":
            return True  # pass through non-alerts

        cfg = self.config.debounce
        window_start = fused.timestamp - cfg.window_ms / 1000

        for consecutive, decision in enumerate(reversed(self.fused_history), start=1):
            if decision.timestamp < window_start:
                break
            if decision.decision != "drone":
                break
            if consecutive >= cfg.consecutive_required:
                return True

        return False

    def _band(self, score: float) -> ConfidenceBand:
        if score >= 0.8:
            return "high"
        if score >= 0.6:
            return "medium"
        return "low"
