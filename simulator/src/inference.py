#!/usr/bin/env python3
"""Inference and publishing loop for the stream-simulator pipeline.

This module consumes synchronized RGB/thermal frames from the shared buffer,
runs YOLO models, annotates results, and publishes frames to RTSP outputs.

Important behavior:
- only processes frames when buffer timestamp changes
- records per-stage timing diagnostics (inference, annotation, publish)
"""

import logging
import os
import time
from pathlib import Path

from ultralytics import YOLO

from . import buffer
from .frame_annotator import annotate_frame
from .frame_publisher import build_publishers

logger = logging.getLogger(__name__)


def load_models():
    """Load your ML models here."""
    simulator_root = Path(__file__).resolve().parent.parent
    rgb_model = YOLO(str(simulator_root / "models" / "visual_model.pt"))
    thermal_model = YOLO(str(simulator_root / "models" / "thermal_model.pt"))
    return rgb_model, thermal_model


def _extract_detections(results, frame_shape):
    """Convert YOLO detections into a normalized metadata payload."""
    detections = []
    boxes = getattr(results, "boxes", None)
    if boxes is None:
        return detections

    names = getattr(results, "names", {})
    height, width = frame_shape[:2]

    for detection in boxes:
        x1, y1, x2, y2 = detection.xyxy[0].tolist()
        x1 = max(0, min(int(x1), width - 1))
        y1 = max(0, min(int(y1), height - 1))
        x2 = max(0, min(int(x2), width - 1))
        y2 = max(0, min(int(y2), height - 1))

        class_id = int(detection.cls[0]) if detection.cls is not None else -1
        confidence = float(detection.conf[0]) if detection.conf is not None else 0.0
        label = names.get(class_id, str(class_id)) if isinstance(names, dict) else str(class_id)

        detections.append({
            "bbox": (x1, y1, x2, y2),
            "class_id": class_id,
            "label": label,
            "confidence": confidence,
        })

    return detections


def run_inference():
    """Run the continuous inference loop until interrupted.

    Timing logs are emitted to help identify pipeline bottlenecks.
    """
    print("\n" + "=" * 60)
    print("SIMULATOR INFERENCE")
    print("=" * 60)

    # Load models
    rgb_model, thermal_model = load_models()

    # Metrics
    frame_count = 0
    start_time = time.time()
    rgb_publisher = None
    thermal_publisher = None
    last_processed_timestamp = None  # Track last processed frame to avoid duplicates

    # Diagnostics
    inference_times = []  # Track inference time per frame
    annotate_times = []  # Track annotation time per frame
    publish_times = []  # Track publishing time per frame

    print("Waiting for frames from video ingestion...\n")

    try:
        while True:
            # Get latest frame pair from buffer
            frame_data = buffer.get()

            if frame_data and frame_data.get("timestamp") != last_processed_timestamp:
                # Only process if timestamp has changed (new frame arrived)
                frame_process_start = time.time()
                last_processed_timestamp = frame_data.get("timestamp")
                frame_count += 1
                rgb = frame_data["rgb"]
                thermal = frame_data["thermal"]

                # Time inference
                infer_start = time.time()
                rgb_results = rgb_model(rgb, verbose=False)[0]
                thermal_results = thermal_model(thermal, verbose=False)[0]
                infer_duration = time.time() - infer_start
                inference_times.append(infer_duration)
                if infer_duration > 0.1:  # >100ms is slow
                    logger.warning(f"Slow inference: {infer_duration * 1000:.1f}ms")

                rgb_detections = _extract_detections(rgb_results, rgb.shape)
                thermal_detections = _extract_detections(thermal_results, thermal.shape)

                # Time annotation
                annot_start = time.time()
                rgb_annotated = annotate_frame(rgb, rgb_detections)
                thermal_annotated = annotate_frame(thermal, thermal_detections)
                annot_duration = time.time() - annot_start
                annotate_times.append(annot_duration)

                if rgb_publisher is None or thermal_publisher is None:
                    from .video_ingestion import PLAYBACK_FPS

                    rgb_publisher, thermal_publisher = build_publishers(
                        rgb_shape=rgb_annotated.shape,
                        thermal_shape=thermal_annotated.shape,
                        fps=PLAYBACK_FPS,
                    )
                    print(
                        "Started stream publishers "
                        f"(mode={os.getenv('SIM_STREAM_MODE', 'rtsp')}, "
                        f"host={os.getenv('SIM_STREAM_HOST', 'mediamtx')})"
                    )

                # Time publishing
                pub_start = time.time()
                rgb_publisher.publish(rgb_annotated)
                thermal_publisher.publish(thermal_annotated)
                pub_duration = time.time() - pub_start
                publish_times.append(pub_duration)

                frame_process_duration = time.time() - frame_process_start
                if frame_process_duration > 0.15:  # >150ms is slow
                    infer_ms = infer_duration * 1000
                    annot_ms = annot_duration * 1000
                    pub_ms = pub_duration * 1000
                    logger.warning(
                        f"Slow frame processing: {frame_process_duration * 1000:.1f}ms "
                        f"(infer={infer_ms:.1f}ms, "
                        f"annot={annot_ms:.1f}ms, pub={pub_ms:.1f}ms)"
                    )

                # Print frame info and log diagnostics
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0

                if frame_count % 30 == 0:
                    print(f"Frame {frame_count:5d} | Elapsed: {elapsed:6.1f}s | FPS: {fps:5.1f}")
                    print(f"  RGB shape: {rgb.shape} | Thermal shape: {thermal.shape}")
                    print(
                        f"  Detections - RGB: {len(rgb_detections):2d}, "
                        f"Thermal: {len(thermal_detections):2d}"
                    )
                    if rgb_publisher and thermal_publisher:
                        rgb_stats = rgb_publisher.stats()
                        thermal_stats = thermal_publisher.stats()
                        print(
                            "  Publish stats - "
                            f"RGB sent={rgb_stats['published']} dropped={rgb_stats['dropped']} | "
                            "Thermal sent="
                            f"{thermal_stats['published']} "
                            f"dropped={thermal_stats['dropped']}"
                        )

                    # Log timing diagnostics
                    if inference_times:
                        avg_infer = sum(inference_times) / len(inference_times) * 1000
                        max_infer = max(inference_times) * 1000
                        logger.info(f"Inference: avg={avg_infer:.1f}ms, max={max_infer:.1f}ms")
                    if annotate_times:
                        avg_annot = sum(annotate_times) / len(annotate_times) * 1000
                        logger.info(f"Annotation: avg={avg_annot:.1f}ms")
                    if publish_times:
                        avg_pub = sum(publish_times) / len(publish_times) * 1000
                        logger.info(f"Publishing: avg={avg_pub:.1f}ms")

                    inference_times.clear()
                    annotate_times.clear()
                    publish_times.clear()

            time.sleep(0.01)  # Prevent busy waiting

    except KeyboardInterrupt:
        print("\n\nShutdown requested")
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\nProcessed {frame_count} frames in {elapsed:.1f}s ({fps:.1f} FPS)")
    finally:
        if rgb_publisher:
            rgb_publisher.stop()
        if thermal_publisher:
            thermal_publisher.stop()
