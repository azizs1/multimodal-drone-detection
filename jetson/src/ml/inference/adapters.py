"""Adapters that normalize model outputs for fusion ingestion."""

from __future__ import annotations

from typing import Any

from ..fusion.schemas import ModalityPrediction


def _resolve_class_name(
    class_idx: int,
    names: dict[int, str] | list[str] | None,
    class_aliases: dict[str, str] | None = None,
) -> str:
    if isinstance(names, dict):
        class_name = names.get(class_idx, str(class_idx))
    elif isinstance(names, list) and 0 <= class_idx < len(names):
        class_name = names[class_idx]
    else:
        class_name = str(class_idx)

    if class_aliases:
        return class_aliases.get(class_name, class_name)
    return class_name


def adapt_yolo_results(
    modality: str,
    timestamp: float,
    result: Any,
    sensor_id: str,
    class_aliases: dict[str, str] | None = None,
) -> list[ModalityPrediction]:
    """Convert one Ultralytics result object into fusion contract predictions.

    Expected `result` fields:
    - result.names: dict[int, str] | list[str]
    - result.boxes.xyxy: iterable[iterable[float]]
    - result.boxes.conf: iterable[float]
    - result.boxes.cls: iterable[float]
    """

    names = getattr(result, "names", None)
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    xyxy = getattr(boxes, "xyxy", [])
    conf = getattr(boxes, "conf", [])
    cls = getattr(boxes, "cls", [])

    predictions: list[ModalityPrediction] = []
    for idx, raw_box in enumerate(xyxy):
        bbox = tuple(float(x) for x in raw_box)
        class_idx = int(float(cls[idx]))
        class_id = _resolve_class_name(class_idx, names, class_aliases=class_aliases)
        confidence = float(conf[idx])

        predictions.append(
            ModalityPrediction(
                modality=modality,
                timestamp=timestamp,
                bbox=bbox,
                class_id=class_id,
                confidence=confidence,
                meta={"sensor_id": sensor_id},
            )
        )

    return predictions
