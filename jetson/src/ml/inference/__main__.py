"""Inference runtime scaffold that loads offline-trained models and forwards predictions."""

from __future__ import annotations

import json
import os
import time
import zmq
from pathlib import Path
from urllib import error, request

from .adapters import adapt_yolo_results

REPO_ROOT = Path(__file__).resolve().parents[4]

# NOTE: for TensorRT, let's use .engine files in order to have the GPU perform this processing
DEFAULT_RGB_MODEL_PATH = (
    REPO_ROOT / "offline_ml/runs/visual_no_augmentation_baseline/weights/best.pt"
)
DEFAULT_THERMAL_MODEL_PATH = (
    REPO_ROOT / "offline_ml/runs/thermal_no_augmentation_baseline/weights/best.pt"
)
DEFAULT_FUSION_ENDPOINT = "http://127.0.0.1:8050/fusion/ingest"


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


def _post_to_fusion(fusion_endpoint: str, payload: list[dict]) -> None:
    req = request.Request(
        fusion_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=2) as resp:
            print(f"fusion response status={resp.status}")
    except error.URLError as exc:
        print(f"fusion post failed: {exc}")


def _infer_and_send(
    rgb_model,
    thermal_model,
    rgb_frame,
    thermal_frame,
    fusion_endpoint: str,
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

    payload = [pred.model_dump() for pred in rgb_predictions + thermal_predictions]
    if payload:
        _post_to_fusion(fusion_endpoint=fusion_endpoint, payload=payload)


def main() -> int:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("ipc:///tmp/frames_bus")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    current_frames = {"rgb": None, "thermal": None}

    fusion_endpoint = os.getenv("FUSION_ENDPOINT", DEFAULT_FUSION_ENDPOINT)
    print("ml.inference starting")
    print(f"fusion endpoint: {fusion_endpoint}")

    rgb_model, thermal_model = _load_models()
    print("loaded RGB and thermal models")
    print(f"rgb classes: {getattr(rgb_model, 'names', {})}")
    print(f"thermal classes: {getattr(thermal_model, 'names', {})}")
    print("waiting for frame source integration (sensor ingestion -> inference bridge)")

    try:
        while True:
            # blocking until we get frame data
            frames = socket.recv_pyobj()

            modality = frames["modality"]
            current_frames[modality] = frames["frame"]
            ts = frames["timestamp"]
            
            rgb_frame = frames["rgb"]
            th_frame = frames["thermal"]

            if rgb_frame is not None and th_frame is not None:
                _infer_and_send(rgb_model, thermal_model, rgb_frame, th_frame, fusion_endpoint)
                current_frames = {"rgb": None, "thermal": None}

    except KeyboardInterrupt:
        print("ml.inference stopped")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
