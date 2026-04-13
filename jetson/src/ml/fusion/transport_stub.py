"""Transport layer stub for fused outputs.

This is a design-time scaffold for Sprint 1. It shows how the fusion engine will expose
results via FastAPI and ZeroMQ. Real wiring will happen once modality workers are in place.
"""

from __future__ import annotations
import json
import os
import time
from urllib import error, request


try:
    from fastapi import APIRouter
except ImportError:  # lightweight fallback for design phase
    APIRouter = None  # type: ignore

try:
    import zmq
except ImportError:  # pragma: no cover - not required for design doc
    zmq = None  # type: ignore

from .fusion_core import FusionEngine
from .schemas import FusedDecision, ModalityPrediction
DEFAULT_BACKEND_INCIDENT_ENDPOINT = "http://backend:8000/incidents"



def build_router(fusion_engine: FusionEngine) -> APIRouter:
    if APIRouter is None:
        raise RuntimeError("FastAPI not installed in this environment")

    router = APIRouter(prefix="/fusion", tags=["fusion"])

    @router.post("/ingest", response_model=FusedDecision | None)
    def ingest(predictions: list[ModalityPrediction]):
        """HTTP ingest endpoint for modality predictions; returns fused decision."""
        """HTTP ingest endpoint for modality predictions; returns fused decision and posts to backend."""
        """HTTP ingest endpoint for modality predictions; aggregates RGB/thermal to fused decision and posts to backend."""
        """HTTP ingest endpoint for modality predictions; aggregates RGB/thermal detections and posts to backend."""
        """Ingest modality predictions, fuse them, and post to backend."""
        fused = fusion_engine.fuse(predictions)
        if fused:
            _post_to_backend_incidents(fused)
        return fused

    return router



def _post_to_backend_incidents(fused: FusedDecision) -> None:
    """POST fused decision to backend incidents endpoint."""
    backend_endpoint = os.getenv(
        "BACKEND_INCIDENT_ENDPOINT", DEFAULT_BACKEND_INCIDENT_ENDPOINT
    )

    # Ensure timestamp is set
    if not fused.timestamp or fused.timestamp == 0:
        fused.timestamp = time.time()

    # Convert to dict and adjust schema to match backend's FusedDecisionIngest
    fused_dict = fused.model_dump()
    fused_dict["evidence"] = {
        modality: (pred.model_dump() if pred else None)
        for modality, pred in fused.evidence.items()
    }
    fused_dict["objects"] = [obj.model_dump() for obj in fused.objects]
    fused_dict["media"] = {
        modality: (ref.model_dump() if ref else None)
        for modality, ref in fused.media.items()
    }
    fused_dict["timestamp"] = fused.timestamp

    req = request.Request(
        backend_endpoint,
        data=json.dumps(fused_dict).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as resp:
            print(f"backend incident status={resp.status}")
    except error.HTTPError as exc:
        body = ""
        if exc.fp is not None:
            body = exc.fp.read().decode("utf-8", errors="replace")
        print(f"backend incident post failed: status={exc.code} body={body}")
    except error.URLError as exc:
        print(f"backend incident post failed: {exc}")


def build_pub_socket(endpoint: str = "tcp://*:5557"):
    if zmq is None:
        raise RuntimeError("pyzmq not installed in this environment")
    ctx = zmq.Context.instance()
    sock = ctx.socket(zmq.PUB)
    sock.bind(endpoint)
    return sock


def publish_fused(sock, fused: FusedDecision):
    if sock is None or zmq is None or fused is None:
        return
    sock.send_json({"topic": "fusion.alert", "payload": fused.model_dump()})
