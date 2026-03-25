from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_alert_connections():
    # This fixture is kept for potential future setup/teardown needs,
    # but it deliberately avoids reaching into private attributes like
    # `alter_connection_manager._connections` to prevent tight coupling
    # to internal implementation details.
    yield


def test_create_detection_broadcasts_id_to_all_alert_clients(monkeypatch: pytest.MonkeyPatch):
    client = TestClient(app)
    detection_id = uuid4()
    now = datetime.now(UTC)

    def mock_create(self, detection):
        return SimpleNamespace(
            id=detection_id,
            detected_at=detection.detected_at,
            confidence=detection.confidence,
            direction=detection.direction,
            distance_ft=detection.distance_ft,
            visual_confidence=detection.visual_confidence,
            thermal_confidence=detection.thermal_confidence,
            fused_score=detection.fused_score,
            frame_snapshot_url=detection.frame_snapshot_url,
            stream_name=detection.stream_name,
            created_at=now,
            updated_at=now,
        )

    monkeypatch.setattr("app.api.routers.detections.DetectionRepository.create", mock_create)

    payload = {
        "detected_at": "2026-02-21T14:32:07Z",
        "confidence": 0.94,
        "direction": "NE",
        "distance_ft": 125.5,
        "visual_confidence": 0.92,
        "thermal_confidence": 0.89,
        "fused_score": 0.94,
        "frame_snapshot_url": "s3://detections/drone/2026-02-21/detection_123.jpg",
        "stream_name": "drone",
    }

    with (
        client.websocket_connect("/detections/alert") as ws_one,
        client.websocket_connect("/detections/alert") as ws_two,
    ):
        response = client.post("/detections", json=payload)
        assert response.status_code == 201

        assert ws_one.receive_text() == str(detection_id)
        assert ws_two.receive_text() == str(detection_id)
