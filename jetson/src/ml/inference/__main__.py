"""Inference runtime scaffold that loads offline-trained models and forwards predictions."""

from __future__ import annotations

import json
import os
import time
import traceback
from contextlib import suppress
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event, Thread
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
DEFAULT_FRAME_PAIR_TOLERANCE_MS = 100.0
DEFAULT_BACKEND_POST_QUEUE_SIZE = 256


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
    save_conf_threshold: float,
    publishers=None,
    storage=None,
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

    frame_id = f"frame-{frame_index:06d}"
    for pred in rgb_predictions + thermal_predictions:
        pred.meta["frame_id"] = frame_id

    payload = [pred.model_dump() for pred in rgb_predictions + thermal_predictions]
    if publishers is not None:
        rgb_publisher, thermal_publisher = publishers
        rgb_publisher.publish(rgb_annotated)
        thermal_publisher.publish(thermal_annotated)

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
