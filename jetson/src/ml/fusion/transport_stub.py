"""Transport layer stub for fused outputs.

This is a design-time scaffold for Sprint 1. It shows how the fusion engine will expose
results via FastAPI and ZeroMQ. Real wiring will happen once modality workers are in place.
"""
from __future__ import annotations

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


def build_router(fusion_engine: FusionEngine) -> APIRouter:
    if APIRouter is None:
        raise RuntimeError("FastAPI not installed in this environment")

    router = APIRouter(prefix="/fusion", tags=["fusion"])

    @router.post("/ingest", response_model=FusedDecision | None)
    def ingest(predictions: list[ModalityPrediction]):
        """HTTP ingest endpoint for modality predictions; returns fused decision."""
        return fusion_engine.fuse(predictions)

    return router


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
