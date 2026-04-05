import json
from datetime import UTC, datetime

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _incident_payload(incident_id: str, decision: str = "drone", confidence: float = 0.83):
    now_ts = datetime.now(UTC).timestamp()
    return {
        "incident_id": incident_id,
        "has_drone": decision == "drone",
        "fused_confidence": confidence,
        "confidence_band": "high" if confidence >= 0.8 else "medium",
        "decision": decision,
        "evidence": {
            "rgb": {
                "modality": "rgb",
                "timestamp": now_ts,
                "bbox": [0.1, 0.2, 0.3, 0.4],
                "class_id": "drone",
                "confidence": confidence,
                "embedding": None,
                "meta": {"sensor_id": "cam0"},
            },
            "thermal": None,
        },
        "per_modality_scores": {"rgb": confidence, "thermal": 0.0},
        "thresholds": {"alert": 0.75, "hold": 0.55},
        "gating_reason": "rgb",
        "latency_ms": 20.5,
        "media": {
            "rgb": {"frame_uri": "s3://detections/drone/frame_001.jpg", "thumbnail_uri": None},
            "thermal": None,
        },
        "objects": [
            {
                "object_id": "rgb-0",
                "modality": "rgb",
                "class_id": "drone",
                "confidence": confidence,
                "bbox": [0.1, 0.2, 0.3, 0.4],
                "timestamp": now_ts,
            }
        ],
        "timestamp": now_ts,
    }


def test_create_incident_and_read_it_back():
    incident_id = "incident-create-read"
    with client.websocket_connect("/detections/alert") as ws:
        create_response = client.post("/incidents", json=_incident_payload(incident_id))
        assert create_response.status_code == 201

        body = create_response.json()
        assert body["incident_id"] == incident_id
        assert body["decision"] == "drone"
        assert body["has_drone"] is True
        assert body["stream_name"] == "fusion"
        assert body["primary_frame_url"] == "s3://detections/drone/frame_001.jpg"

        websocket_body = json.loads(ws.receive_text())
        assert websocket_body == {
            "incident_id": incident_id,
            "decision": "drone",
            "fused_confidence": 0.83,
            "confidence_band": "high",
            "gating_reason": "rgb",
            "timestamp": body["source_timestamp"],
            "per_modality_scores": {"rgb": 0.83, "thermal": 0.0},
            "latency_ms": 20.5,
            "media": body["media"],
            "objects": body["objects"],
        }

    get_response = client.get(f"/incidents/{incident_id}")
    assert get_response.status_code == 200

    fetched = get_response.json()
    assert fetched["incident_id"] == incident_id
    assert fetched["decision"] == "drone"
    assert fetched["is_confirmed"] is True


def test_list_incidents_supports_filtering():
    incident_id = "incident-list-filter"
    client.post("/incidents", json=_incident_payload(incident_id, decision="none", confidence=0.42))

    response = client.get("/incidents", params={"decision": "none", "stream_name": "fusion"})
    assert response.status_code == 200

    incidents = response.json()
    assert isinstance(incidents, list)
    assert any(item["incident_id"] == incident_id for item in incidents)


def test_get_missing_incident_returns_404():
    response = client.get("/incidents/does-not-exist")
    assert response.status_code == 404
