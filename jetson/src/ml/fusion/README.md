# Fusion Framework Design (Sprint 1)

Owner: Chia Yu Chang — Multimodal Fusion & Data Transport

## Objectives
- Fuse RGB and thermal/IR detector outputs into a single drone/none decision with per-class confidence.
- Achieve product targets from proposal: ≥90% detection probability, ≤5% false positive rate, decision within ~5–15 s window.
- Support late-fusion with weighted confidence and gating logic; expose fused decisions plus per-modality evidence to the backend/dashboard.

## Scope (Sprint 1)
Design only (interfaces + config). No model training here. Implementation will plug into trained YOLO/other detectors for each modality and run on Jetson Orin Nano.

## Data Contracts
- **Per-modality prediction (input)**
  ```json
  {
    "modality": "rgb" | "thermal",
    "timestamp": 1739999999.123,
    "bbox": [x1, y1, x2, y2],
    "class_id": "drone",
    "confidence": 0.0–1.0,
    "embedding": [floats],           // optional, for future multimodal classifier
    "meta": {"sensor_id": "cam0", "frame_id": "..."}
  }
  ```
- **Fused decision (output)**
  ```json
  {
    "incident_id": "uuid",
    "fused_confidence": 0.0–1.0,
    "confidence_band": "low" | "medium" | "high",
    "decision": "drone" | "none",
    "per_modality_scores": {"rgb": 0.8, "thermal": 0.7},
    "evidence": {"rgb": {...}, "thermal": {...}},
    "media": {"rgb": {"frame_uri": "..."}, "thermal": {"frame_uri": "..."}},
    "thresholds": {"alert": 0.75, "hold": 0.55},
    "gating_reason": "both-high" | "rgb-high" | "thermal-high" | "low-confidence",
    "latency_ms": 0,
    "timestamp": 1739999999.456
  }
  ```

### Example payload (for dashboard contract)
```json
{
  "incident_id": "0d6eac18-6c8c-4c35-9f42-c5a6e6c7b6c8",
  "fused_confidence": 0.82,
  "confidence_band": "high",
  "decision": "drone",
  "per_modality_scores": {"rgb": 0.78, "thermal": 0.70},
  "evidence": {
    "rgb": {"modality": "rgb", "timestamp": 1739999999.12, "bbox": [0.1,0.2,0.3,0.4], "class_id": "drone", "confidence": 0.78, "meta": {"sensor_id": "cam0"}},
    "thermal": {"modality": "thermal", "timestamp": 1739999999.11, "bbox": [0.1,0.2,0.3,0.4], "class_id": "drone", "confidence": 0.70, "meta": {"sensor_id": "ir0"}}
  },
  "media": {
    "rgb": {"frame_uri": "/evidence/rgb/incident_0d6eac18.jpg"},
    "thermal": {"frame_uri": "/evidence/thermal/incident_0d6eac18.jpg"}
  },
  "thresholds": {"alert": 0.75, "hold": 0.55},
  "gating_reason": "rgb+thermal",
  "latency_ms": 35.4,
  "timestamp": 1739999999.456
}
```

## Fusion Logic (late fusion)
1. **Normalize confidences** per modality (temperature-scaled sigmoid if needed) to comparable ranges.
2. **Weighted average**: `score = sum(w_m * conf_m)`; default `w_rgb = 0.6`, `w_thermal = 0.4` (configurable).
3. **Gating rules** (align with proposal: alerts only if fused score exceeds threshold, EO/IR confirmation preferred):
   - `score >= alert_threshold` **and** at least one modality above its own gate → `decision = drone`.
   - `hold_threshold <= score < alert_threshold` → keep buffering frames; request next N frames before deciding.
   - Otherwise → `decision = none`.
4. **EO/IR confirmation hook**: optional rule that requires thermal confirmation if RGB-only alert occurs at long range.
5. **Debounce**: require K consecutive positive fused frames (default K=2) within 1 s to emit an incident.

## Configuration (config.py)
- `weights`: per-modality weight map.
- `alert_threshold`, `hold_threshold` (default 0.75 / 0.55) chosen to target <5% FPR; will be tuned with validation set.
- `per_modality_gates`: minimum confidence for each modality to be considered in fusion.
- `debounce`: `consecutive_required`, `window_ms`.
- `logging`: paths for saving evidence frames/embeddings.

## Data Transport
- **Ingress**: predictions pushed from modality-specific workers via ZeroMQ PUB/SUB (`topic = inference.rgb` / `inference.thermal`).
- **Fusion service** subscribes, aligns by timestamp (±50 ms), fuses, and publishes `fusion.alert` messages and writes to local ring buffer.
- **Egress to backend**: expose a lightweight FastAPI router (see `transport_stub.py`) that the backend container can mount, sending fused incidents and evidence to PostgreSQL + dashboard. Also keep an on-device JSONL log for offline audit.

## Telemetry & Metrics
- Track per-modality precision/recall, fused precision/recall, latency per stage.
- Persist confusion matrix snapshots per sprint to verify 90% / 5% goals.
- Include debug flag to dump fusion traces when scores sit near thresholds.

## File Layout
- `config.py` — central configuration for weights, thresholds, debounce, topics.
- `schemas.py` — Pydantic models for validation of inputs/outputs.
- `fusion_core.py` — FusionEngine implementing weighted fusion + gating.
- `transport_stub.py` — FastAPI router + ZeroMQ publisher for fused outputs.
- `__init__.py` — exports for easy imports.

## Next Steps (Sprint 2+)
- Integrate real detector outputs (YOLOv8/YOLOv11 weights) and embeddings.
- Implement calibration notebook to tune weights/thresholds from validation set.
- Add unit tests for fusion edge cases and debounce logic.
- Wire into backend API routes and dashboard overlays.
- Contract test: `python -m pytest jetson/src/ml/fusion/test_ingest_contract.py` to validate `/fusion/ingest` JSON schema.
