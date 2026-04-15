"""Inference runtime scaffold that loads offline-trained models and forwards predictions."""

from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path
from urllib import error, request

from frame_pair_transport import DEFAULT_FRAME_SUB_CONNECT_ENDPOINT

from .adapters import adapt_yolo_results
from .zmq_bridge import run_one_zmq_inference

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RGB_MODEL_PATH = REPO_ROOT / "offline_ml/weights/visual_no_augmentation_best.pt"
DEFAULT_THERMAL_MODEL_PATH = REPO_ROOT / "offline_ml/weights/thermal_no_augmentation_best.pt"
DEFAULT_FUSION_ENDPOINT = "http://fusion:8050/fusion/ingest"
DEFAULT_ZMQ_FRAME_CONNECT_ENDPOINT = DEFAULT_FRAME_SUB_CONNECT_ENDPOINT
DEFAULT_SAVE_CONF_THRESHOLD = 0.75


def _annotate_frame(frame, predictions):
    """Render prediction boxes and labels on a BGR frame."""
    try:
        import cv2
    except ImportError:
        return frame

    annotated = frame.copy()
    for pred in predictions:
        x1, y1, x2, y2 = (int(v) for v in pred.bbox)
        label = f"{pred.class_id} {pred.confidence:.2f}"
        color = (0, 255, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated,
            label,
            (x1, max(16, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    return annotated


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


def _infer_and_send(
    rgb_model,
    thermal_model,
    rgb_frame,
    thermal_frame,
    fusion_endpoint: str,
    save_conf_threshold: float,
    publishers=None,
    storage=None,
) -> None:
    timestamp = time.time()

    rgb_result = rgb_model(rgb_frame, verbose=False)[0]
    thermal_result = thermal_model(thermal_frame, verbose=False)[0]

    rgb_predictions = adapt_yolo_results(
        modality="rgb",
        timestamp=timestamp,
        result=rgb_result,
        sensor_id="rgb_cam0",
    )
    thermal_predictions = adapt_yolo_results(
        modality="thermal",
        timestamp=timestamp,
        result=thermal_result,
        sensor_id="thermal_cam0",
        class_aliases={"0": "drone"},
    )

    rgb_annotated = _annotate_frame(rgb_frame, rgb_predictions)
    thermal_annotated = _annotate_frame(thermal_frame, thermal_predictions)

    all_predictions = rgb_predictions + thermal_predictions
    drone_predictions = [pred for pred in all_predictions if pred.class_id == "drone"]
    max_drone_conf = max((pred.confidence for pred in drone_predictions), default=0.0)
    should_upload = bool(drone_predictions) and max_drone_conf >= save_conf_threshold

    if not drone_predictions:
        print("storage upload skipped: no drone detections in current frame")
    elif not should_upload:
        print(
            "storage upload skipped: drone confidence below threshold "
            f"max_conf={max_drone_conf:.3f} threshold={save_conf_threshold:.3f}"
        )

    if should_upload and storage is None:
        print(
            "storage upload skipped: storage unavailable "
            f"max_conf={max_drone_conf:.3f} threshold={save_conf_threshold:.3f}"
        )

    if should_upload and storage is not None:
        try:
            uploaded = storage.upload_detection_images(
                timestamp=timestamp,
                rgb_frame=rgb_annotated,
                thermal_frame=thermal_annotated,
            )
            print(
                "storage upload attempted "
                f"max_conf={max_drone_conf:.3f} threshold={save_conf_threshold:.3f} "
                f"rgb_url={uploaded.rgb is not None} thermal_url={uploaded.thermal is not None}"
            )
            for pred in rgb_predictions:
                if uploaded.rgb:
                    pred.meta["frame_uri"] = uploaded.rgb
            for pred in thermal_predictions:
                if uploaded.thermal:
                    pred.meta["frame_uri"] = uploaded.thermal
        except Exception as exc:  # pragma: no cover - runtime resilience
            print(f"storage upload failed: {exc!r}")
            print(traceback.format_exc())

    payload = [pred.model_dump() for pred in rgb_predictions + thermal_predictions]
    if publishers is not None:
        rgb_publisher, thermal_publisher = publishers
        rgb_publisher.publish(rgb_annotated)
        thermal_publisher.publish(thermal_annotated)

    if payload:
        _post_to_fusion(fusion_endpoint=fusion_endpoint, payload=payload)


def main() -> int:
    fusion_endpoint = os.getenv("FUSION_ENDPOINT", DEFAULT_FUSION_ENDPOINT)
    print("ml.inference starting")
    print(f"fusion endpoint: {fusion_endpoint}")
    print("inference source mode: zmq")
    print("rtsp publishing enabled: True")

    rgb_model, thermal_model = _load_models()
    print("loaded RGB and thermal models")
    print(f"rgb classes: {getattr(rgb_model, 'names', {})}")
    print(f"thermal classes: {getattr(thermal_model, 'names', {})}")

    save_conf_threshold = float(
        os.getenv("INFERENCE_SAVE_CONF_THRESHOLD", str(DEFAULT_SAVE_CONF_THRESHOLD))
    )
    print(f"image save confidence threshold: {save_conf_threshold}")

    from .frame_publisher import build_publishers

    publishers = None
    storage = None

    upload_enabled = os.getenv("INFERENCE_UPLOAD_ENABLED", "true").lower() == "true"
    if upload_enabled:
        try:
            from .storage import RustFSStorage

            storage = RustFSStorage.from_env()
            try:
                storage.ensure_bucket_public()
                print(f"RustFS bucket ready: {storage.bucket}")
            except Exception as exc:
                print(f"RustFS bootstrap warning (continuing uploads): {exc!r}")
                print(traceback.format_exc())
        except Exception as exc:  # pragma: no cover - runtime resilience
            print(f"RustFS storage disabled due to error: {exc!r}")
            print(traceback.format_exc())
            storage = None

    connect_endpoint = os.getenv("ZMQ_FRAME_CONNECT_ENDPOINT", DEFAULT_ZMQ_FRAME_CONNECT_ENDPOINT)
    print(f"ZeroMQ frame connect endpoint: {connect_endpoint}")

    def _infer_with_optional_publish(**kwargs):
        nonlocal publishers
        if publishers is None:
            publishers = build_publishers(
                rgb_shape=kwargs["rgb_frame"].shape,
                thermal_shape=kwargs["thermal_frame"].shape,
                fps=30,
            )
        _infer_and_send(
            **kwargs,
            save_conf_threshold=save_conf_threshold,
            publishers=publishers,
            storage=storage,
        )

    try:
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
