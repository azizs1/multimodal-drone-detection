"""Contract test for /fusion/ingest endpoint using TestClient.

Run with: python -m pytest jetson/src/ml/fusion/test_ingest_contract.py
"""

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .config import DebounceConfig, FusionConfig
from .fusion_core import FusionEngine
from .schemas import ModalityPrediction
from .transport_stub import build_router


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
