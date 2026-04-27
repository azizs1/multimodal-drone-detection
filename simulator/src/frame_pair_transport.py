"""ZeroMQ frame-pair transport helpers for simulator publishing."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

FRAME_TOPIC = b"frame-pair"
DEFAULT_FRAME_PUB_BIND_ENDPOINT = "tcp://*:5560"


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
