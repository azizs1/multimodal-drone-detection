"""Inference runtime scaffold that loads offline-trained models and forwards predictions."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from urllib import error, request

from frame_pair_transport import DEFAULT_FRAME_SUB_CONNECT_ENDPOINT

from .adapters import adapt_yolo_results
from .frame_publisher import build_publishers
from .zmq_bridge import run_ipc_zmq_loop, run_one_zmq_inference

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RGB_MODEL_PATH = REPO_ROOT / "offline_ml/weights/visual_no_augmentation_best.pt"
DEFAULT_THERMAL_MODEL_PATH = REPO_ROOT / "offline_ml/weights/thermal_no_augmentation_best.pt"
DEFAULT_FUSION_ENDPOINT = "http://fusion:8050/fusion/ingest"
DEFAULT_ZMQ_FRAME_CONNECT_ENDPOINT = DEFAULT_FRAME_SUB_CONNECT_ENDPOINT
DEFAULT_FRAME_PAIR_TOLERANCE_MS = 100.0
DEFAULT_RGB_MODEL_CONF = 0.15
DEFAULT_THERMAL_MODEL_CONF = 0.15


def _annotate_frame(frame, yolo_result):
    """Render native Ultralytics YOLO annotations on a frame."""
    try:
        plotted = yolo_result.plot()
        return plotted if plotted is not None else frame
    except Exception:
        return frame


def _encode_jpeg_b64(frame) -> str | None:
    try:
        import cv2
    except ImportError:
        return None

    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return None
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def _load_models():
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "ultralytics is required for ml.inference runtime. "
            "Install it in the Jetson environment before running."
        ) from exc

    rgb_path = Path(os.getenv("RGB_MODEL_PATH", str(DEFAULT_RGB_MODEL_PATH)))
    thermal_path = Path(os.getenv("THERMAL_MODEL_PATH", str(DEFAULT_THERMAL_MODEL_PATH)))

    if not rgb_path.exists():
        raise FileNotFoundError(f"RGB model not found: {rgb_path}")
    if not thermal_path.exists():
        raise FileNotFoundError(f"Thermal model not found: {thermal_path}")

    rgb_model = YOLO(str(rgb_path))
    thermal_model = YOLO(str(thermal_path))
    return rgb_model, thermal_model


def _post_to_fusion(fusion_endpoint: str, payload: list[dict]) -> dict | None:
    req = request.Request(
        fusion_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=2) as resp:
            raw = resp.read().decode("utf-8")
            print(f"fusion response status={resp.status}")
            if raw:
                print(f"fusion response body={raw}")
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return None
    except error.URLError as exc:
        print(f"fusion post failed: {exc}")
    return None


def _within_pair_tolerance(rgb_ts: float, thermal_ts: float, tolerance_ms: float) -> bool:
    return abs(rgb_ts - thermal_ts) * 1000.0 <= tolerance_ms


def _infer_and_send(
    rgb_model,
    thermal_model,
    rgb_frame,
    thermal_frame,
    fusion_endpoint: str,
    pair_tolerance_ms: float,
    frame_index: int,
    rgb_model_conf: float,
    thermal_model_conf: float,
    source_timestamp: float | None = None,
    publishers=None,
) -> None:
    timestamp = source_timestamp if source_timestamp is not None else time.time()
    rgb_ts = timestamp
    rgb_result = rgb_model(rgb_frame, conf=rgb_model_conf, verbose=False)[0]
    thermal_ts = timestamp
    thermal_result = thermal_model(thermal_frame, conf=thermal_model_conf, verbose=False)[0]

    if not _within_pair_tolerance(
        rgb_ts=rgb_ts, thermal_ts=thermal_ts, tolerance_ms=pair_tolerance_ms
    ):
        print(
            "skipping unpaired frame: "
            f"rgb_ts={rgb_ts:.6f} thermal_ts={thermal_ts:.6f} "
            f"tolerance_ms={pair_tolerance_ms}"
        )
        return

    rgb_predictions = adapt_yolo_results(
        modality="rgb",
        timestamp=rgb_ts,
        result=rgb_result,
        sensor_id="rgb_cam0",
    )
    thermal_predictions = adapt_yolo_results(
        modality="thermal",
        timestamp=thermal_ts,
        result=thermal_result,
        sensor_id="thermal_cam0",
        class_aliases={"0": "drone"},
    )

    rgb_annotated = _annotate_frame(rgb_frame, rgb_result)
    thermal_annotated = _annotate_frame(thermal_frame, thermal_result)

    frame_id = f"frame-{frame_index:06d}"
    rgb_jpeg_b64 = _encode_jpeg_b64(rgb_annotated)
    thermal_jpeg_b64 = _encode_jpeg_b64(thermal_annotated)

    for pred in rgb_predictions + thermal_predictions:
        pred.meta["frame_id"] = frame_id
        if pred.modality == "rgb" and rgb_jpeg_b64:
            pred.meta["frame_jpeg_b64"] = rgb_jpeg_b64
        if pred.modality == "thermal" and thermal_jpeg_b64:
            pred.meta["frame_jpeg_b64"] = thermal_jpeg_b64

    payload = [pred.model_dump() for pred in rgb_predictions + thermal_predictions]
    if publishers is not None:
        rgb_publisher, thermal_publisher = publishers
        rgb_publisher.publish(rgb_annotated)
        thermal_publisher.publish(thermal_annotated)

    if payload:
        _post_to_fusion(fusion_endpoint=fusion_endpoint, payload=payload)


def main() -> int:
    fusion_endpoint = os.getenv("FUSION_ENDPOINT", DEFAULT_FUSION_ENDPOINT)
    pair_tolerance_ms = float(
        os.getenv("FRAME_PAIR_TOLERANCE_MS", str(DEFAULT_FRAME_PAIR_TOLERANCE_MS))
    )
    rgb_model_conf = float(os.getenv("INFERENCE_RGB_MODEL_CONF", str(DEFAULT_RGB_MODEL_CONF)))
    thermal_model_conf = float(
        os.getenv("INFERENCE_THERMAL_MODEL_CONF", str(DEFAULT_THERMAL_MODEL_CONF))
    )
    connect_endpoint = os.getenv("ZMQ_FRAME_CONNECT_ENDPOINT", DEFAULT_ZMQ_FRAME_CONNECT_ENDPOINT)
    print("ml.inference starting")
    print(f"fusion endpoint: {fusion_endpoint}")
    print(f"frame pair tolerance (ms): {pair_tolerance_ms}")
    print(f"rgb model conf threshold: {rgb_model_conf}")
    print(f"thermal model conf threshold: {thermal_model_conf}")
    print(f"zmq frame connect endpoint: {connect_endpoint}")

    rgb_model, thermal_model = _load_models()
    print("loaded RGB and thermal models")
    print(f"rgb classes: {getattr(rgb_model, 'names', {})}")
    print(f"thermal classes: {getattr(thermal_model, 'names', {})}")
    publishers = None

    def _infer_with_optional_publish(rgb_model, thermal_model, rgb_frame, thermal_frame, **kwargs):
        nonlocal publishers
        if publishers is None:
            publishers = build_publishers(
                rgb_shape=rgb_frame.shape,
                thermal_shape=thermal_frame.shape,
                fps=int(os.getenv("INFERENCE_STREAM_FPS", "20")),
            )
            publishers[0].start()
            publishers[1].start()

        source_timestamp = None
        metadata = kwargs.get("metadata")
        if isinstance(metadata, dict):
            raw_ts = metadata.get("timestamp")
            try:
                source_timestamp = float(raw_ts) if raw_ts is not None else None
            except (TypeError, ValueError):
                source_timestamp = None

        frame_index = int(time.time() * 1000)
        _infer_and_send(
            rgb_model=rgb_model,
            thermal_model=thermal_model,
            rgb_frame=rgb_frame,
            thermal_frame=thermal_frame,
            fusion_endpoint=kwargs.get("fusion_endpoint", fusion_endpoint),
            pair_tolerance_ms=pair_tolerance_ms,
            frame_index=frame_index,
            rgb_model_conf=rgb_model_conf,
            thermal_model_conf=thermal_model_conf,
            source_timestamp=source_timestamp,
            publishers=publishers,
        )

    try:
        if connect_endpoint.startswith("ipc://"):
            print(f"ZMQ mode: IPC per-frame (ingest_gi) endpoint={connect_endpoint}")
            run_ipc_zmq_loop(
                _infer_with_optional_publish,
                rgb_model=rgb_model,
                thermal_model=thermal_model,
                fusion_endpoint=fusion_endpoint,
                connect_endpoint=connect_endpoint,
            )
        else:
            print(f"ZMQ mode: TCP frame-pair (simulator) endpoint={connect_endpoint}")
            while True:
                try:
                    run_one_zmq_inference(
                        _infer_with_optional_publish,
                        rgb_model=rgb_model,
                        thermal_model=thermal_model,
                        fusion_endpoint=fusion_endpoint,
                        connect_endpoint=connect_endpoint,
                    )
                except Exception as exc:  # pragma: no cover - runtime resilience
                    print(f"inference loop error: {exc}")
                    time.sleep(0.25)
    finally:
        if publishers is not None:
            publishers[0].stop()
            publishers[1].stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
