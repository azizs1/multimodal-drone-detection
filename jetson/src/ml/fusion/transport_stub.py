"""Transport layer stub for fused outputs.

This module wires fusion decisions to:
1) FastAPI ingest endpoint
2) Optional window aggregation before side-effects
3) Backend incident POST
4) Optional ZMQ publisher
"""

from __future__ import annotations

import base64
import json
import os
import threading
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
from .schemas import FusedDecision, MediaRef, ModalityPrediction
from .window_aggregator import WindowAggregator

DEFAULT_BACKEND_INCIDENT_ENDPOINT = "http://127.0.0.1:8000/incidents"


def build_router(fusion_engine: FusionEngine) -> APIRouter:
    if APIRouter is None:
        raise RuntimeError("FastAPI not installed in this environment")

    router = APIRouter(prefix="/fusion", tags=["fusion"])
    aggregator: WindowAggregator | None = None
    stop_event = threading.Event()

    if fusion_engine.config.window.enabled:
        aggregator = WindowAggregator(
            window_width_seconds=fusion_engine.config.window.window_width_seconds
        )

        def _flush_loop() -> None:
            interval = max(fusion_engine.config.window.flush_interval_seconds, 0.1)
            while not stop_event.wait(interval):
                for winner, winner_ctx in aggregator.flush():
                    winner_predictions = winner_ctx if isinstance(winner_ctx, list) else []
                    _emit_winner(winner, winner_predictions)

        threading.Thread(target=_flush_loop, daemon=True).start()

    @router.post("/ingest", response_model=FusedDecision | None)
    def ingest(predictions: list[ModalityPrediction]):
        """HTTP ingest endpoint for modality predictions; returns fused decision."""
        fused = fusion_engine.fuse(predictions)
        if fused is None:
            return None

        if aggregator is None:
            threading.Thread(target=_emit_winner, args=(fused, predictions), daemon=True).start()
            return fused

        emitted = aggregator.feed(fused, predictions)
        if not emitted:
            return None

        for winner, winner_ctx in emitted:
            winner_predictions = winner_ctx if isinstance(winner_ctx, list) else predictions
            threading.Thread(
                target=_emit_winner,
                args=(winner, winner_predictions),
                daemon=True,
            ).start()

        return emitted[-1][0]

    @router.on_event("shutdown")
    def _on_shutdown() -> None:
        stop_event.set()
        if aggregator is None:
            return
        for winner, winner_ctx in aggregator.flush():
            winner_predictions = winner_ctx if isinstance(winner_ctx, list) else []
            _emit_winner(winner, winner_predictions)

    return router


def _emit_winner(winner: FusedDecision, predictions: list[ModalityPrediction]) -> None:
    """Attach media refs and post fused winner to backend."""
    _attach_media_urls_from_predictions(fused=winner, predictions=predictions)
    _post_to_backend_incidents(winner)


def _build_backend_incident_payload(fused: FusedDecision) -> dict:
    """Build backend payload from fused decision.

    Keeps per-object bbox for overlay rendering.
    Removes heavy raw frame blob from evidence meta.
    """
    if not fused.timestamp or fused.timestamp == 0:
        fused.timestamp = time.time()

    fused_dict = fused.model_dump()
    fused_dict["evidence"] = {}
    for modality, pred in fused.evidence.items():
        if pred is None:
            fused_dict["evidence"][modality] = None
            continue
        pred_dict = pred.model_dump()
        pred_dict.setdefault("meta", {}).pop("frame_jpeg_b64", None)
        fused_dict["evidence"][modality] = pred_dict

    fused_dict["objects"] = [obj.model_dump() for obj in fused.objects]
    fused_dict["media"] = {
        modality: (ref.model_dump() if ref else None) for modality, ref in fused.media.items()
    }
    fused_dict["timestamp"] = fused.timestamp
    return fused_dict


def _post_to_backend_incidents(fused: FusedDecision) -> None:
    """POST fused decision to backend incidents endpoint."""
    backend_endpoint = os.getenv("BACKEND_INCIDENT_ENDPOINT", DEFAULT_BACKEND_INCIDENT_ENDPOINT)
    fused_payload = _build_backend_incident_payload(fused)

    req = request.Request(
        backend_endpoint,
        data=json.dumps(fused_payload).encode("utf-8"),
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


def _attach_media_urls_from_predictions(
    fused: FusedDecision,
    predictions: list[ModalityPrediction],
) -> None:
    """Attach media refs from prediction metadata to fused.media.

    Priority:
    1) `meta.frame_uri` if available
    2) validate `meta.frame_jpeg_b64` is decodable (no upload in this branch)
    """
    for modality in ("rgb", "thermal"):
        frame_uri = _first_frame_uri(predictions, modality)
        if frame_uri:
            media_ref = fused.media.get(modality)
            if media_ref is None:
                fused.media[modality] = MediaRef(frame_uri=frame_uri)
            else:
                media_ref.frame_uri = frame_uri
            continue

        b64_payload = _first_frame_payload(predictions, modality)
        if not b64_payload:
            continue
        if _decode_b64_image(b64_payload) is None:
            continue
        # Keep extensible: upload to object storage can be added later.


def _first_frame_uri(predictions: list[ModalityPrediction], modality: str) -> str | None:
    for pred in predictions:
        if pred.modality != modality:
            continue
        frame_uri = pred.meta.get("frame_uri")
        if frame_uri:
            return frame_uri
    return None


def _first_frame_payload(predictions: list[ModalityPrediction], modality: str) -> str | None:
    for pred in predictions:
        if pred.modality != modality:
            continue
        payload = pred.meta.get("frame_jpeg_b64")
        if payload:
            return payload
    return None


def _decode_b64_image(payload: str) -> bytes | None:
    try:
        return base64.b64decode(payload)
    except Exception:
        return None


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
