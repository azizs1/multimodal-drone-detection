"""Transport layer stub for fused outputs.

This is a design-time scaffold for Sprint 1. It shows how the fusion engine will expose
results via FastAPI and ZeroMQ. Real wiring will happen once modality workers are in place.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from typing import Any
from urllib import error, request

try:
    from fastapi import APIRouter
except ImportError:  # lightweight fallback for design phase
    APIRouter = None  # type: ignore

try:
    import zmq
except ImportError:  # pragma: no cover - not required for design doc
    zmq = None  # type: ignore

from ml.inference.storage import RustFSStorage

from .fusion_core import FusionEngine
from .schemas import FusedDecision, MediaRef, ModalityPrediction
from .window_aggregator import WindowAggregator

DEFAULT_BACKEND_INCIDENT_ENDPOINT = "http://backend:8000/incidents"

_STORAGE: RustFSStorage | None = None


def _emit_winner(winner: FusedDecision, predictions: list[ModalityPrediction]) -> None:
    """Upload the winner's frame image then POST to backend. Runs in a daemon thread."""
    _attach_media_urls_from_predictions(fused=winner, predictions=predictions)
    _post_to_backend_incidents(winner)


def _start_flush_thread(aggregator: WindowAggregator, interval: float) -> None:
    def _loop() -> None:
        while True:
            time.sleep(interval)
            for winner, predictions in aggregator.flush():
                threading.Thread(
                    target=_emit_winner, args=(winner, predictions or []), daemon=True
                ).start()

    threading.Thread(target=_loop, daemon=True, name="window-aggregator-flush").start()


def build_router(fusion_engine: FusionEngine) -> Any:
    if APIRouter is None:
        raise RuntimeError("FastAPI not installed in this environment")

    router = APIRouter(prefix="/fusion", tags=["fusion"])

    win_cfg = fusion_engine.config.window
    aggregator = WindowAggregator(
        window_width_seconds=win_cfg.window_width_seconds,
    )
    if win_cfg.enabled:
        _start_flush_thread(aggregator, win_cfg.flush_interval_seconds)

    @router.post("/ingest", response_model=FusedDecision | None)
    def ingest(predictions: list[ModalityPrediction]):
        """Ingest modality predictions, fuse them, and post to backend."""
        fused = fusion_engine.fuse(predictions)
        if fused:
            if win_cfg.enabled:
                # Upload and post only when the window's winner is emitted,
                # not on every frame — predictions travel with the candidate.
                ready = aggregator.feed(fused, context=predictions)
                print(
                    f"window decision={fused.decision} "
                    f"conf={fused.fused_confidence:.3f} "
                    f"buckets={aggregator.open_bucket_count} "
                    f"emitting={len(ready)}"
                )
                for winner, winner_preds in ready:
                    threading.Thread(
                        target=_emit_winner, args=(winner, winner_preds), daemon=True
                    ).start()
            else:
                _attach_media_urls_from_predictions(fused=fused, predictions=predictions)
                threading.Thread(
                    target=_post_to_backend_incidents, args=(fused,), daemon=True
                ).start()
        return fused

    return router


def _post_to_backend_incidents(fused: FusedDecision) -> None:
    """POST fused decision to backend incidents endpoint."""
    backend_endpoint = os.getenv("BACKEND_INCIDENT_ENDPOINT", DEFAULT_BACKEND_INCIDENT_ENDPOINT)

    # Ensure timestamp is set
    if not fused.timestamp or fused.timestamp == 0:
        fused.timestamp = time.time()

    # Convert to dict and adjust schema to match backend's FusedDecisionIngest
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

    print(
        "posting /incidents "
        f"endpoint={backend_endpoint} "
        f"timestamp={fused_dict['timestamp']} "
        f"objects={len(fused_dict['objects'])} "
        f"media={fused_dict['media']}"
    )

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


def _get_storage() -> RustFSStorage | None:
    global _STORAGE
    if _STORAGE is not None:
        return _STORAGE

    try:
        _STORAGE = RustFSStorage.from_env()
        _STORAGE.ensure_bucket_public()
    except Exception as exc:
        print(f"fusion storage unavailable: {exc!r}")
        _STORAGE = None

    return _STORAGE


def _attach_media_urls_from_predictions(
    fused: FusedDecision,
    predictions: list[ModalityPrediction],
) -> None:
    storage = _get_storage()
    if storage is None:
        return

    ts = fused.timestamp or time.time()
    for modality in ("rgb", "thermal"):
        b64_payload = _first_frame_payload(predictions, modality)
        if not b64_payload:
            continue

        jpeg_bytes = _decode_b64_image(b64_payload)
        if jpeg_bytes is None:
            continue

        try:
            url = storage.upload_detection_image_bytes(
                timestamp=ts,
                modality=modality,
                jpeg_bytes=jpeg_bytes,
            )
        except Exception as exc:
            print(f"fusion media upload failed modality={modality}: {exc!r}")
            continue
        if url:
            media_ref = fused.media.get(modality)
            if media_ref is None:
                fused.media[modality] = MediaRef(frame_uri=url)
            else:
                media_ref.frame_uri = url


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
