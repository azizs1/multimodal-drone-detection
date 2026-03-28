"""Helpers for drawing detection overlays on simulator frames."""

from __future__ import annotations

from typing import Any

import cv2

_PALETTE = [
    (0, 255, 0),
    (255, 180, 0),
    (0, 200, 255),
    (255, 80, 80),
    (160, 120, 255),
    (255, 255, 0),
]


def _color_for_class(class_id: int) -> tuple[int, int, int]:
    return _PALETTE[class_id % len(_PALETTE)]


def annotate_frame(frame, detections: list[dict[str, Any]]):
    """Draw detection boxes and labels on a copy of frame."""
    output = frame.copy()
    if not detections:
        return output

    height, width = output.shape[:2]
    thickness = max(1, int(min(height, width) * 0.002))
    font_scale = max(0.35, min(height, width) / 700.0)

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        class_id = int(det["class_id"])
        label = str(det["label"])
        confidence = float(det["confidence"])
        color = _color_for_class(class_id)

        cv2.rectangle(output, (x1, y1), (x2, y2), color, thickness)

        caption = f"{label} {confidence:.2f}"
        (text_width, text_height), baseline = cv2.getTextSize(
            caption, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )

        label_y = y1 - 8
        if label_y - text_height - baseline < 0:
            label_y = y1 + text_height + 8

        top_left = (x1, label_y - text_height - baseline)
        bottom_right = (x1 + text_width + 6, label_y + baseline)
        cv2.rectangle(output, top_left, bottom_right, color, -1)
        cv2.putText(
            output,
            caption,
            (x1 + 3, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (20, 20, 20),
            max(1, thickness - 1),
            cv2.LINE_AA,
        )

    return output
