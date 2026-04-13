"""ZeroMQ frame-pair transport helpers for simulator and Jetson inference."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

FRAME_TOPIC = b"frame-pair"
DEFAULT_FRAME_PUB_BIND_ENDPOINT = "tcp://*:5560"
DEFAULT_FRAME_SUB_CONNECT_ENDPOINT = "tcp://127.0.0.1:5560"


def _frame_spec(frame: np.ndarray) -> dict[str, Any]:
    contiguous = np.ascontiguousarray(frame)
    return {
        "shape": list(contiguous.shape),
        "dtype": str(contiguous.dtype),
        "nbytes": int(contiguous.nbytes),
    }


def encode_frame_pair(
    timestamp: float, rgb_frame: np.ndarray, thermal_frame: np.ndarray
) -> list[bytes]:
    rgb = np.ascontiguousarray(rgb_frame)
    thermal = np.ascontiguousarray(thermal_frame)
    metadata = {
        "timestamp": timestamp,
        "rgb": _frame_spec(rgb),
        "thermal": _frame_spec(thermal),
    }
    return [
        FRAME_TOPIC,
        json.dumps(metadata, separators=(",", ":")).encode("utf-8"),
        rgb.tobytes(),
        thermal.tobytes(),
    ]


def _rebuild_frame(frame_bytes: bytes, spec: dict[str, Any]) -> np.ndarray:
    dtype = np.dtype(spec["dtype"])
    shape = tuple(int(value) for value in spec["shape"])
    frame = np.frombuffer(frame_bytes, dtype=dtype)
    expected_size = int(np.prod(shape))
    if frame.size != expected_size:
        raise ValueError(
            f"frame payload has {frame.size} elements but metadata expects {expected_size}"
        )
    return frame.reshape(shape).copy()


def decode_frame_pair(
    parts: list[bytes] | tuple[bytes, ...],
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    if len(parts) != 4:
        raise ValueError(f"expected 4 multipart frames, received {len(parts)}")

    topic, metadata_bytes, rgb_bytes, thermal_bytes = parts
    if topic != FRAME_TOPIC:
        raise ValueError(f"unexpected topic {topic!r}")

    metadata = json.loads(metadata_bytes.decode("utf-8"))
    rgb = _rebuild_frame(rgb_bytes, metadata["rgb"])
    thermal = _rebuild_frame(thermal_bytes, metadata["thermal"])
    return metadata, rgb, thermal
