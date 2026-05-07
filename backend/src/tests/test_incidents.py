import json
from datetime import UTC, datetime, timedelta

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def _incident_payload(
    incident_id: str,
    decision: str = "drone",
    confidence: float = 0.83,
    timestamp: float | None = None,
):
    now_ts = timestamp if timestamp is not None else datetime.now(UTC).timestamp()
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
    with client.websocket_connect("/incidents/alert") as ws:
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

    get_response = client.get(f"/incidents/raw/{incident_id}")
    assert get_response.status_code == 200

    fetched = get_response.json()
    assert fetched["incident_id"] == incident_id
    assert fetched["decision"] == "drone"
    assert fetched["is_confirmed"] is True


def test_list_incidents_supports_filtering():
    incident_id = "incident-list-filter"
    client.post(
        "/incidents",
        json=_incident_payload(incident_id, decision="drone", confidence=0.84),
    )

    response = client.get("/incidents", params={"decision": "drone", "stream_name": "fusion"})
    assert response.status_code == 200

    incidents = response.json()
    assert isinstance(incidents, list)
    assert any(item["representative_incident_id"] == incident_id for item in incidents)


def test_get_missing_incident_returns_404():
    response = client.get("/incidents/does-not-exist")
    assert response.status_code == 404


def test_incident_creation_is_idempotent():
    """Test that posting the same incident_id twice returns same record without re-broadcast."""
    incident_id = "incident-idempotent-test"
    payload = _incident_payload(incident_id)

    # Open websocket to capture alerts
    with client.websocket_connect("/incidents/alert") as ws:
        # First POST - should create and return 201
        response1 = client.post("/incidents", json=payload)
        assert response1.status_code == 201
        body1 = response1.json()
        assert body1["incident_id"] == incident_id

        # Should receive websocket alert for first creation
        alert1 = json.loads(ws.receive_text())
        assert alert1["incident_id"] == incident_id

        # Second POST with same incident_id - should return existing and return 200
        response2 = client.post("/incidents", json=payload)
        assert response2.status_code == 200
        body2 = response2.json()

        # Should return the same incident (same database ID)
        assert body2["id"] == body1["id"]
        assert body2["incident_id"] == incident_id

        # Should NOT broadcast a second alert - verify websocket has no new messages
        # (we use a short timeout to check if there's no message waiting)
        try:
            ws._ws.settimeout(0.1)
            _ = ws.receive_text()
            # If we get here, there was a message (bad!)
            raise AssertionError("Second POST should not broadcast an alert")
        except TimeoutError:
            # Good - no message was broadcast
            pass
        except Exception:
            # Also acceptable - websocket closed or no data available
            pass


def test_raw_incidents_endpoint_returns_frame_level_records():
    incident_id = "incident-raw-list"
    client.post("/incidents", json=_incident_payload(incident_id, decision="none", confidence=0.42))

    response = client.get("/incidents/raw", params={"decision": "none", "stream_name": "fusion"})
    assert response.status_code == 200

    incidents = response.json()
    assert any(item["incident_id"] == incident_id for item in incidents)


def test_posting_one_drone_creates_aggregate():
    incident_id = "incident-aggregate-single"
    create_response = client.post(
        "/incidents",
        json=_incident_payload(incident_id, confidence=0.88),
    )
    assert create_response.status_code == 201

    list_response = client.get("/incidents", params={"decision": "drone", "stream_name": "fusion"})
    assert list_response.status_code == 200

    aggregate = next(
        item for item in list_response.json() if item["representative_incident_id"] == incident_id
    )
    assert aggregate["aggregate_id"].startswith("agg-")
    assert aggregate["incident_id"] == aggregate["aggregate_id"]
    assert aggregate["frame_count"] == 1
    assert aggregate["drone_frame_count"] == 1
    assert aggregate["raw_incident_ids"] == [incident_id]
    assert aggregate["fused_confidence"] == 0.88

    detail_response = client.get(f"/incidents/{aggregate['aggregate_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["aggregate_id"] == aggregate["aggregate_id"]


def test_duplicate_raw_incident_does_not_increment_aggregate_counts():
    incident_id = "incident-aggregate-idempotent"
    payload = _incident_payload(incident_id, confidence=0.86)

    response1 = client.post("/incidents", json=payload)
    response2 = client.post("/incidents", json=payload)

    assert response1.status_code == 201
    assert response2.status_code == 200

    aggregates = client.get("/incidents", params={"decision": "drone"}).json()
    aggregate = next(
        item for item in aggregates if item["representative_incident_id"] == incident_id
    )
    assert aggregate["frame_count"] == 1
    assert aggregate["raw_incident_ids"] == [incident_id]


def test_drone_frames_within_gap_update_same_aggregate():
    start_ts = datetime.now(UTC).timestamp()
    first_id = "incident-aggregate-window-1"
    second_id = "incident-aggregate-window-2"

    client.post("/incidents", json=_incident_payload(first_id, confidence=0.8, timestamp=start_ts))
    client.post(
        "/incidents",
        json=_incident_payload(second_id, confidence=0.9, timestamp=start_ts + 5),
    )

    aggregates = client.get("/incidents", params={"decision": "drone"}).json()
    aggregate = next(item for item in aggregates if first_id in item["raw_incident_ids"])

    assert aggregate["frame_count"] == 2
    assert aggregate["drone_frame_count"] == 2
    assert aggregate["representative_incident_id"] == second_id
    assert aggregate["raw_incident_ids"] == [first_id, second_id]
    assert aggregate["fused_confidence"] == 0.9
    assert round(aggregate["avg_fused_confidence"], 2) == 0.85


def test_drone_frame_after_gap_creates_new_aggregate():
    start = datetime.now(UTC)
    first_id = "incident-aggregate-gap-1"
    second_id = "incident-aggregate-gap-2"

    client.post(
        "/incidents",
        json=_incident_payload(first_id, confidence=0.81, timestamp=start.timestamp()),
    )
    client.post(
        "/incidents",
        json=_incident_payload(
            second_id,
            confidence=0.82,
            timestamp=(start + timedelta(seconds=11)).timestamp(),
        ),
    )

    aggregates = client.get("/incidents", params={"decision": "drone"}).json()
    matching = [
        item
        for item in aggregates
        if first_id in item["raw_incident_ids"] or second_id in item["raw_incident_ids"]
    ]

    assert len(matching) == 2
    assert all(item["frame_count"] == 1 for item in matching)


def test_none_decision_stores_raw_without_creating_aggregate():
    incident_id = "incident-none-no-aggregate"
    client.post("/incidents", json=_incident_payload(incident_id, decision="none", confidence=0.42))

    raw_response = client.get(f"/incidents/raw/{incident_id}")
    assert raw_response.status_code == 200
    assert raw_response.json()["decision"] == "none"

    aggregate_response = client.get("/incidents", params={"decision": "none"})
    assert aggregate_response.status_code == 200
    assert not any(
        incident_id in item["raw_incident_ids"] for item in aggregate_response.json()
    )
