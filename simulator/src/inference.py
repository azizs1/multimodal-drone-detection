#!/usr/bin/env python3
"""
Inference template for drone detection.

This is a template showing how to use the shared buffer from video ingestion.
You can run this as-is (it will poll frames), or modify it with your own ML models.

Usage:
    # Approach 1: Run directly (video ingestion starts in background)
    python -m src.run_inference

    # Approach 2: Modify this file with your models and logic
    # (Add your model loading and inference code in the TODOs below)

    # Approach 3: Use as reference for your own script
"""

import os
import time

from ultralytics import YOLO

from src import buffer
from src.frame_annotator import annotate_frame
from src.frame_publisher import build_publishers


def load_models():
    """Load your ML models here."""
    rgb_model = YOLO("models/visual_model.pt")
    thermal_model = YOLO("models/thermal_model.pt")
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

        detections.append(
            {
                "bbox": (x1, y1, x2, y2),
                "class_id": class_id,
                "label": label,
                "confidence": confidence,
            }
        )

    return detections


def run_inference():
    """Main inference loop."""
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

    print("Waiting for frames from video ingestion...\n")

    try:
        while True:
            # Get latest frame pair from buffer
            frame_data = buffer.get()

            if frame_data:
                frame_count += 1
                rgb = frame_data["rgb"]
                thermal = frame_data["thermal"]

                rgb_results = rgb_model(rgb, verbose=False)[0]
                thermal_results = thermal_model(thermal, verbose=False)[0]

                rgb_detections = _extract_detections(rgb_results, rgb.shape)
                thermal_detections = _extract_detections(thermal_results, thermal.shape)

                rgb_annotated = annotate_frame(rgb, rgb_detections)
                thermal_annotated = annotate_frame(thermal, thermal_detections)

                if rgb_publisher is None or thermal_publisher is None:
                    from src.video_ingestion import PLAYBACK_FPS

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

                rgb_publisher.publish(rgb_annotated)
                thermal_publisher.publish(thermal_annotated)

                # Print frame info
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
