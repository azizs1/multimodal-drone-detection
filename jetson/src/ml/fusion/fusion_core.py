"""Weighted late-fusion with gating (design stub for Sprint 1)."""
from __future__ import annotations

import time
import uuid
from collections import deque
from collections.abc import Iterable

from .config import DEFAULT_CONFIG, FusionConfig
from .schemas import ConfidenceBand, FusedDecision, ModalityPrediction


class FusionEngine:
    def __init__(self, config: FusionConfig = DEFAULT_CONFIG):
        self.config = config
        self.buffer = deque(maxlen=config.buffer_size)

    def fuse(self, preds: Iterable[ModalityPrediction]) -> FusedDecision | None:
        filtered = [p for p in preds if p]
        if not filtered:
            return None

        # Keep for debugging and debounce.
        now = time.time()
        for p in filtered:
            self.buffer.append(p)

        score, reason, per_modality_scores = self._weighted_score(filtered)
        decision = self._gate(score, filtered)
        latency_ms = (time.time() - now) * 1000

        fused_conf_band = self._band(score)

        fused = FusedDecision(
            incident_id=str(uuid.uuid4()),
            fused_confidence=score,
            confidence_band=fused_conf_band,
            decision=decision,
            evidence=self._latest_by_modality(filtered),
            per_modality_scores=per_modality_scores,
            thresholds={
                "alert": self.config.alert_threshold,
                "hold": self.config.hold_threshold,
            },
            gating_reason=reason,
            latency_ms=latency_ms,
        )

        if self._debounce(fused):
            return fused
        return None

    def _weighted_score(
        self, preds: list[ModalityPrediction]
    ) -> tuple[float, str, dict[str, float]]:
        weights = self.config.weights
        score = 0.0
        per_modality_scores = {"rgb": 0.0, "thermal": 0.0}
        used = []
        for p in preds:
            w = weights.get(p.modality, 0.0)
            per_modality_scores[p.modality] = p.confidence
            gate = self.config.per_modality_gates.get(p.modality, 0.0)
            if p.confidence < gate:
                continue
            score += w * p.confidence
            used.append(p.modality)
        reason = "no-modality-passed-gate" if not used else "+".join(sorted(set(used)))
        return score, reason, per_modality_scores

    def _gate(self, score: float, preds: list[ModalityPrediction]) -> str:
        if score >= self.config.alert_threshold:
            # optional EO/IR confirmation
            if self.config.eo_ir_required:
                has_thermal = any(p.modality == "thermal" for p in preds)
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

    def _debounce(self, fused: FusedDecision) -> bool:
        if fused.decision != "drone":
            return True  # pass through non-alerts
        cfg = self.config.debounce
        window_start = fused.timestamp - cfg.window_ms / 1000
        positives = [p for p in self.buffer if p.timestamp >= window_start]
        return len(positives) >= cfg.consecutive_required

    def _band(self, score: float) -> ConfidenceBand:
        if score >= 0.8:
            return "high"
        if score >= 0.6:
            return "medium"
        return "low"
