"""Contract test for /fusion/ingest endpoint using TestClient.

Run with: python -m pytest jetson/src/ml/fusion/test_ingest_contract.py
"""

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from . import transport_stub as transport_module
from .config import DebounceConfig, FusionConfig, WindowConfig
from .fusion_core import FusionEngine
from .schemas import ModalityPrediction
from .transport_stub import _build_backend_incident_payload, build_router


def test_ingest_returns_fused_decision():
    app = FastAPI()
    app.include_router(
        build_router(
            FusionEngine(
                FusionConfig(debounce=DebounceConfig(consecutive_required=1, window_ms=1000))
            )
        )
    )
    client = TestClient(app)

    now = time.time()
    payload = [
        {
            "modality": "rgb",
            "timestamp": now,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.8,
            "meta": {"sensor_id": "cam0"},
        },
        {
            "modality": "thermal",
            "timestamp": now - 0.01,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.7,
            "meta": {"sensor_id": "ir0"},
        },
    ]

    resp = client.post("/fusion/ingest", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    # Core contract fields
    assert body["has_drone"] is True
    assert body["decision"] == "drone"
    assert isinstance(body["incident_id"], str) and body["incident_id"]
    assert body["confidence_band"] in {"low", "medium", "high"}
    assert "per_modality_scores" in body
    assert set(body["per_modality_scores"]) == {"rgb", "thermal"}
    assert len(body["objects"]) == 2
    assert {obj["modality"] for obj in body["objects"]} == {"rgb", "thermal"}


def test_debounce_counts_fused_events_not_modalities():
    engine = FusionEngine(
        FusionConfig(debounce=DebounceConfig(consecutive_required=2, window_ms=1000))
    )

    now = time.time()
    preds = [
        ModalityPrediction(
            modality="rgb",
            timestamp=now,
            bbox=None,
            class_id="drone",
            confidence=0.8,
            meta={"sensor_id": "cam0"},
        ),
        ModalityPrediction(
            modality="thermal",
            timestamp=now,
            bbox=None,
            class_id="drone",
            confidence=0.7,
            meta={"sensor_id": "ir0"},
        ),
    ]

    first = engine.fuse(preds)
    assert first is None

    second = engine.fuse([pred.model_copy(update={"timestamp": now + 0.2}) for pred in preds])
    assert second is not None
    assert second.decision == "drone"


def test_non_drone_predictions_do_not_trigger_drone_decision():
    engine = FusionEngine(
        FusionConfig(debounce=DebounceConfig(consecutive_required=1, window_ms=1000))
    )

    now = time.time()
    preds = [
        ModalityPrediction(
            modality="rgb",
            timestamp=now,
            bbox=None,
            class_id="bird",
            confidence=0.95,
            meta={"sensor_id": "cam0"},
        ),
        ModalityPrediction(
            modality="thermal",
            timestamp=now,
            bbox=None,
            class_id="plane",
            confidence=0.9,
            meta={"sensor_id": "ir0"},
        ),
    ]

    fused = engine.fuse(preds)
    assert fused is not None
    assert fused.has_drone is False
    assert fused.decision == "none"
    assert fused.fused_confidence == 0.0


def test_multiple_detections_per_modality_are_capped_and_object_listed():
    engine = FusionEngine(
        FusionConfig(debounce=DebounceConfig(consecutive_required=1, window_ms=1000))
    )

    now = time.time()
    preds = [
        ModalityPrediction(
            modality="rgb",
            timestamp=now,
            bbox=(0.0, 0.0, 0.3, 0.3),
            class_id="drone",
            confidence=0.9,
            meta={"sensor_id": "cam0"},
        ),
        ModalityPrediction(
            modality="rgb",
            timestamp=now,
            bbox=(0.4, 0.4, 0.7, 0.7),
            class_id="drone",
            confidence=0.85,
            meta={"sensor_id": "cam0"},
        ),
        ModalityPrediction(
            modality="thermal",
            timestamp=now,
            bbox=(0.0, 0.0, 0.3, 0.3),
            class_id="drone",
            confidence=0.8,
            meta={"sensor_id": "ir0"},
        ),
    ]

    fused = engine.fuse(preds)
    assert fused is not None
    assert 0.0 <= fused.fused_confidence <= 1.0
    assert len(fused.objects) == 3


def test_window_aggregation_emits_on_next_time_bucket():
    app = FastAPI()
    app.include_router(
        build_router(
            FusionEngine(
                FusionConfig(
                    debounce=DebounceConfig(consecutive_required=1, window_ms=1000),
                    window=WindowConfig(enabled=True, window_width_seconds=1.0),
                )
            )
        )
    )
    client = TestClient(app)

    base = time.time()
    bucket_a_ts = float(int(base)) + 0.10
    bucket_b_ts = float(int(base)) + 1.10

    payload_a = [
        {
            "modality": "rgb",
            "timestamp": bucket_a_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.8,
            "meta": {"sensor_id": "cam0"},
        },
        {
            "modality": "thermal",
            "timestamp": bucket_a_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.7,
            "meta": {"sensor_id": "ir0"},
        },
    ]
    payload_b = [
        {
            "modality": "rgb",
            "timestamp": bucket_b_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.9,
            "meta": {"sensor_id": "cam0"},
        },
        {
            "modality": "thermal",
            "timestamp": bucket_b_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.6,
            "meta": {"sensor_id": "ir0"},
        },
    ]

    resp_a = client.post("/fusion/ingest", json=payload_a)
    assert resp_a.status_code == 200
    assert resp_a.json() is None

    # Feeding a decision in the next bucket closes the previous bucket.
    resp_b = client.post("/fusion/ingest", json=payload_b)
    assert resp_b.status_code == 200
    body = resp_b.json()
    assert body is not None
    # The emitted decision belongs to bucket A and should preserve bucket A timestamp.
    assert abs(body["timestamp"] - bucket_a_ts) < 1e-6


def test_window_aggregation_posts_only_closed_window_winner(monkeypatch):
    posted: list[tuple[float, str]] = []

    def _capture_emit(winner, predictions):
        sensor = ""
        if predictions:
            sensor = predictions[0].meta.get("sensor_id", "")
        posted.append((winner.timestamp, sensor))

    monkeypatch.setattr(transport_module, "_emit_winner", _capture_emit)

    app = FastAPI()
    app.include_router(
        build_router(
            FusionEngine(
                FusionConfig(
                    debounce=DebounceConfig(consecutive_required=1, window_ms=1000),
                    window=WindowConfig(
                        enabled=True,
                        window_width_seconds=1.0,
                        flush_interval_seconds=60.0,
                    ),
                )
            )
        )
    )
    client = TestClient(app)

    base = float(int(time.time()))
    # Two events in the same bucket; second one should win by confidence.
    a1_ts = base + 0.10
    a2_ts = base + 0.30
    b_ts = base + 1.10

    payload_a1 = [
        {
            "modality": "rgb",
            "timestamp": a1_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.65,
            "meta": {"sensor_id": "cam-a1"},
        },
        {
            "modality": "thermal",
            "timestamp": a1_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.55,
            "meta": {"sensor_id": "ir-a1"},
        },
    ]
    payload_a2 = [
        {
            "modality": "rgb",
            "timestamp": a2_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.95,
            "meta": {"sensor_id": "cam-a2"},
        },
        {
            "modality": "thermal",
            "timestamp": a2_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.90,
            "meta": {"sensor_id": "ir-a2"},
        },
    ]
    payload_b = [
        {
            "modality": "rgb",
            "timestamp": b_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.8,
            "meta": {"sensor_id": "cam-b"},
        },
        {
            "modality": "thermal",
            "timestamp": b_ts,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": 0.7,
            "meta": {"sensor_id": "ir-b"},
        },
    ]

    assert client.post("/fusion/ingest", json=payload_a1).json() is None
    assert client.post("/fusion/ingest", json=payload_a2).json() is None
    # Entering next bucket should emit exactly one winner for previous bucket.
    assert client.post("/fusion/ingest", json=payload_b).status_code == 200

    deadline = time.time() + 1.0
    while time.time() < deadline and len(posted) < 1:
        time.sleep(0.02)

    assert len(posted) == 1
    emitted_ts, emitted_sensor = posted[0]
    assert abs(emitted_ts - a2_ts) < 1e-6
    assert emitted_sensor == "cam-a2"


def test_backend_payload_keeps_bbox_for_overlay_and_strips_b64_blob():
    engine = FusionEngine(
        FusionConfig(debounce=DebounceConfig(consecutive_required=1, window_ms=1000))
    )

    now = time.time()
    preds = [
        ModalityPrediction(
            modality="rgb",
            timestamp=now,
            bbox=(0.1, 0.2, 0.3, 0.4),
            class_id="drone",
            confidence=0.9,
            meta={"sensor_id": "cam0", "frame_jpeg_b64": "dGVzdA=="},
        ),
        ModalityPrediction(
            modality="thermal",
            timestamp=now,
            bbox=(0.2, 0.3, 0.4, 0.5),
            class_id="drone",
            confidence=0.8,
            meta={"sensor_id": "ir0", "frame_jpeg_b64": "dGVzdA=="},
        ),
    ]

    fused = engine.fuse(preds)
    assert fused is not None
    payload = _build_backend_incident_payload(fused)

    assert payload["objects"]
    assert payload["objects"][0]["bbox"] is not None
    assert "frame_jpeg_b64" not in payload["evidence"]["rgb"]["meta"]
    assert "frame_jpeg_b64" not in payload["evidence"]["thermal"]["meta"]
