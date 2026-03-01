"""Contract test for /fusion/ingest endpoint using TestClient.

Run with: python -m pytest jetson/src/ml/fusion/test_ingest_contract.py
"""
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .fusion_core import FusionEngine
from .transport_stub import build_router


def test_ingest_returns_fused_decision():
    app = FastAPI()
    app.include_router(build_router(FusionEngine()))
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
    assert body["decision"] == "drone"
    assert isinstance(body["incident_id"], str) and body["incident_id"]
    assert body["confidence_band"] in {"low", "medium", "high"}
    assert "per_modality_scores" in body
    assert set(body["per_modality_scores"]) == {"rgb", "thermal"}
