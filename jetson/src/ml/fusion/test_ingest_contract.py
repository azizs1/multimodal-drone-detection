"""Contract test for /fusion/ingest endpoint using TestClient.

Run with: python -m pytest jetson/src/ml/fusion/test_ingest_contract.py
"""

import time
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .config import DebounceConfig, FusionConfig, WindowConfig
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
            "meta": {
                "sensor_id": "cam0",
                "frame_uri": "http://localhost:9000/drone-detection/detections/test/rgb.jpg",
            },
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
    assert body["media"]["rgb"]["frame_uri"].startswith("http://localhost:9000/")


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


def _build_app(window_cfg: WindowConfig) -> tuple[FastAPI, TestClient]:
    app = FastAPI()
    app.include_router(
        build_router(
            FusionEngine(
                FusionConfig(
                    debounce=DebounceConfig(consecutive_required=1, window_ms=1000),
                    window=window_cfg,
                )
            )
        )
    )
    return app, TestClient(app)


def _drone_payload(timestamp: float, confidence: float) -> list[dict]:
    return [
        {
            "modality": "rgb",
            "timestamp": timestamp,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": confidence,
            "meta": {"sensor_id": "cam0"},
        },
        {
            "modality": "thermal",
            "timestamp": timestamp,
            "bbox": [0.1, 0.2, 0.3, 0.4],
            "class_id": "drone",
            "confidence": confidence * 0.9,
            "meta": {"sensor_id": "ir0"},
        },
    ]


def test_windowing_reduces_backend_posts():
    """Two same-window detections → one backend post when the next window arrives."""
    _, client = _build_app(WindowConfig(enabled=True, window_width_seconds=1.0))

    now = 1776.0
    with (
        patch("ml.fusion.transport_stub._attach_media_urls_from_predictions"),
        patch("ml.fusion.transport_stub._post_to_backend_incidents") as mock_post,
    ):
        # Two detections in window 1776 (timestamps 1776.1 and 1776.5)
        client.post("/fusion/ingest", json=_drone_payload(now + 0.1, 0.85))
        client.post("/fusion/ingest", json=_drone_payload(now + 0.5, 0.90))
        # Third detection in window 1777 — triggers lazy eviction of window 1776
        client.post("/fusion/ingest", json=_drone_payload(now + 1.1, 0.70))
        time.sleep(0.1)  # let _emit_winner daemon thread complete

    # Window 1776 emits exactly once; window 1777 stays open past the patch window
    assert mock_post.call_count == 1


def test_windowing_disabled_preserves_original_behavior():
    """With window.enabled=False, every fused decision posts to backend immediately."""
    _, client = _build_app(WindowConfig(enabled=False))

    now = 1776.0
    with (
        patch("ml.fusion.transport_stub._emit_winner"),  # block flush-thread contamination
        patch("ml.fusion.transport_stub._attach_media_urls_from_predictions"),
        patch("ml.fusion.transport_stub._post_to_backend_incidents") as mock_post,
    ):
        client.post("/fusion/ingest", json=_drone_payload(now + 0.1, 0.85))
        client.post("/fusion/ingest", json=_drone_payload(now + 0.5, 0.90))
        time.sleep(0.1)  # let daemon threads complete

    assert mock_post.call_count == 2
