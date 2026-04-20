"""Inference runtime scaffold that loads offline-trained models and forwards predictions."""

from __future__ import annotations

import json
import os
import time
import zmq
import cv2
import numpy as np
from contextlib import suppress
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread
from urllib import error, request

from .adapters import adapt_yolo_results

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RGB_MODEL_PATH = REPO_ROOT / "offline_ml/weights/visual_no_augmentation_best.pt"
DEFAULT_THERMAL_MODEL_PATH = REPO_ROOT / "offline_ml/weights/thermal_no_augmentation_best.pt"
DEFAULT_FUSION_ENDPOINT = "http://127.0.0.1:8050/fusion/ingest"
DEFAULT_BACKEND_INCIDENT_ENDPOINT = "http://127.0.0.1:8000/incidents"
DEFAULT_RGB_VIDEO_PATH = REPO_ROOT / "simulator/videos/visible.mp4"
DEFAULT_THERMAL_VIDEO_PATH = REPO_ROOT / "simulator/videos/infrared.mp4"
DEFAULT_FRAME_PAIR_TOLERANCE_MS = 100.0
DEFAULT_BACKEND_POST_QUEUE_SIZE = 256


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


def _post_to_backend_incidents(backend_endpoint: str, fused_decision: dict) -> None:
    req = request.Request(
        backend_endpoint,
        data=json.dumps(fused_decision).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=2) as resp:
            print(f"backend incident status={resp.status}")
    except error.HTTPError as exc:
        body = ""
        if exc.fp is not None:
            body = exc.fp.read().decode("utf-8", errors="replace")
        print(f"backend incident post failed: status={exc.code} body={body}")
    except error.URLError as exc:
        print(f"backend incident post failed: {exc}")


class BackendIncidentPublisher:
    def __init__(self, backend_endpoint: str, queue_size: int):
        self.backend_endpoint = backend_endpoint
        self._queue: Queue[dict] = Queue(maxsize=queue_size)
        self._stop_event = Event()
        self._worker = Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._worker.join(timeout=3)

    def publish(self, fused_decision: dict) -> None:
        try:
            self._queue.put_nowait(fused_decision)
        except Full:
            with suppress(Empty):
                _ = self._queue.get_nowait()
            try:
                self._queue.put_nowait(fused_decision)
            except Full:
                print("backend publish queue full; dropping fused decision")

    def _run(self) -> None:
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                payload = self._queue.get(timeout=0.2)
            except Empty:
                continue
            _post_to_backend_incidents(
                backend_endpoint=self.backend_endpoint,
                fused_decision=payload,
            )


def _within_pair_tolerance(rgb_ts: float, thermal_ts: float, tolerance_ms: float) -> bool:
    return abs(rgb_ts - thermal_ts) * 1000.0 <= tolerance_ms


def _infer_and_send(
    rgb_model,
    thermal_model,
    rgb_frame,
    thermal_frame,
    fusion_endpoint: str,
    backend_publisher: BackendIncidentPublisher | None,
    pair_tolerance_ms: float,
    frame_index: int,
) -> None:
    rgb_ts = time.time()
    rgb_result = rgb_model(rgb_frame, verbose=False)[0]
    thermal_ts = time.time()
    thermal_result = thermal_model(thermal_frame, verbose=False)[0]

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

    frame_id = f"frame-{frame_index:06d}"
    for pred in rgb_predictions + thermal_predictions:
        pred.meta["frame_id"] = frame_id

    payload = [pred.model_dump() for pred in rgb_predictions + thermal_predictions]
    if payload:
        fused_decision = _post_to_fusion(fusion_endpoint=fusion_endpoint, payload=payload)
        if fused_decision and backend_publisher is not None:
            backend_publisher.publish(fused_decision)


def _iter_video_frames(rgb_video_path: Path, thermal_video_path: Path):
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("opencv-python is required for video-frame inference mode.") from exc

    rgb_cap = cv2.VideoCapture(str(rgb_video_path))
    thermal_cap = cv2.VideoCapture(str(thermal_video_path))
    if not rgb_cap.isOpened():
        raise FileNotFoundError(f"RGB video not found or unreadable: {rgb_video_path}")
    if not thermal_cap.isOpened():
        raise FileNotFoundError(f"Thermal video not found or unreadable: {thermal_video_path}")

    try:
        while True:
            ok_rgb, rgb_frame = rgb_cap.read()
            ok_thermal, thermal_frame = thermal_cap.read()
            if not ok_rgb or not ok_thermal:
                break
            yield rgb_frame, thermal_frame
    finally:
        rgb_cap.release()
        thermal_cap.release()


def main() -> int:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("ipc:///tmp/frames_bus")
    socket.setsockopt(zmq.SUBSCRIBE, b"rgb")
    socket.setsockopt(zmq.SUBSCRIBE, b"thermal")
    current_frames = {"rgb": None, "thermal": None}

    fusion_endpoint = os.getenv("FUSION_ENDPOINT", DEFAULT_FUSION_ENDPOINT)
    backend_incident_endpoint = os.getenv(
        "BACKEND_INCIDENT_ENDPOINT", DEFAULT_BACKEND_INCIDENT_ENDPOINT
    )
    backend_post_queue_size = int(
        os.getenv("BACKEND_POST_QUEUE_SIZE", str(DEFAULT_BACKEND_POST_QUEUE_SIZE))
    )
    pair_tolerance_ms = float(
        os.getenv("FRAME_PAIR_TOLERANCE_MS", str(DEFAULT_FRAME_PAIR_TOLERANCE_MS))
    )
    source_mode = os.getenv("INFERENCE_SOURCE", "idle").lower()
    print("ml.inference starting")
    print(f"fusion endpoint: {fusion_endpoint}")
    print(f"backend incidents endpoint: {backend_incident_endpoint}")
    print(f"backend post queue size: {backend_post_queue_size}")
    print(f"frame pair tolerance (ms): {pair_tolerance_ms}")
    print(f"inference source mode: {source_mode}")

    rgb_model, thermal_model = _load_models()
    print("loaded RGB and thermal models")
    print(f"rgb classes: {getattr(rgb_model, 'names', {})}")
    print(f"thermal classes: {getattr(thermal_model, 'names', {})}")
    backend_publisher: BackendIncidentPublisher | None = None
    if backend_incident_endpoint:
        backend_publisher = BackendIncidentPublisher(
            backend_endpoint=backend_incident_endpoint,
            queue_size=backend_post_queue_size,
        )
        backend_publisher.start()

    try:
        if source_mode == "videos":
            rgb_video_path = Path(os.getenv("RGB_VIDEO_PATH", str(DEFAULT_RGB_VIDEO_PATH)))
            thermal_video_path = Path(
                os.getenv("THERMAL_VIDEO_PATH", str(DEFAULT_THERMAL_VIDEO_PATH))
            )
            max_frames = int(os.getenv("MAX_FRAMES", "0"))
            print(f"rgb video path: {rgb_video_path}")
            print(f"thermal video path: {thermal_video_path}")
            if max_frames > 0:
                print(f"max frames: {max_frames}")
            frame_count = 0
            for rgb_frame, thermal_frame in _iter_video_frames(rgb_video_path, thermal_video_path):
                frame_count += 1
                _infer_and_send(
                    rgb_model=rgb_model,
                    thermal_model=thermal_model,
                    rgb_frame=rgb_frame,
                    thermal_frame=thermal_frame,
                    fusion_endpoint=fusion_endpoint,
                    backend_publisher=backend_publisher,
                    pair_tolerance_ms=pair_tolerance_ms,
                    frame_index=frame_count,
                )
                if max_frames > 0 and frame_count >= max_frames:
                    break
            print(f"video inference finished, processed {frame_count} frame pairs")
            return 0

        print("waiting for frame source integration (sensor ingestion -> inference bridge)")

        while True:
            # multipart: [topic, meta_json, raw_bytes]
            topic, meta_raw, frame_raw = socket.recv_multipart()

            modality = topic.decode("utf-8")
            meta = json.loads(meta_raw.decode("utf-8"))

            frame = np.frombuffer(frame_raw, dtype=np.uint8)
            frame = frame.reshape((meta["height"], meta["width"], meta["channels"]))

            print(f"[{modality}] frame received: shape={frame.shape}")

            current_frames[modality] = frame

            if current_frames["rgb"] is not None and current_frames["thermal"] is not None:
                print("both frames ready")

                # preview = cv2.resize(current_frames["rgb"], (320, 240))
                # cv2.imshow(f"inference_rgb", preview)
                # cv2.waitKey(1)

                # preview = cv2.resize(current_frames["thermal"], (320, 240))
                # cv2.imshow(f"inference_thermal", preview)
                # cv2.waitKey(1)

                _infer_and_send(rgb_model, thermal_model, current_frames["rgb"], current_frames["thermal"], fusion_endpoint)
                current_frames = {"rgb": None, "thermal": None}

    except KeyboardInterrupt:
        print("ml.inference stopped")
        return 0
    finally:
        if backend_publisher is not None:
            backend_publisher.stop()


if __name__ == "__main__":
    raise SystemExit(main())
