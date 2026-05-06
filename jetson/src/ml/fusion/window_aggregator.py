"""Temporal window aggregator for fused detection decisions.

Groups FusedDecision objects into fixed-width time windows and emits only
the highest-fused_confidence decision per window when the window closes.
"""

from __future__ import annotations

import math
import threading
from typing import Any

from .schemas import FusedDecision


class WindowAggregator:
    """Accumulates FusedDecision objects into non-overlapping time windows.

    Each decision may carry an opaque context (e.g. the raw ModalityPrediction
    list) that travels with the winner and is returned alongside it on emission,
    so callers can defer side-effects (image uploads, etc.) to window-close time.

    Args:
        window_width_seconds: Width of each time bucket in seconds.
    """

    def __init__(self, window_width_seconds: float = 1.0) -> None:
        if window_width_seconds <= 0:
            raise ValueError("window_width_seconds must be positive")
        self._window_width = window_width_seconds
        self._buckets: dict[int, tuple[FusedDecision, Any]] = {}
        self._lock = threading.Lock()

    def _bucket_key(self, timestamp: float) -> int:
        return int(math.floor(timestamp / self._window_width))

    def feed(self, decision: FusedDecision, context: Any = None) -> list[tuple[FusedDecision, Any]]:
        """Accept a decision. Returns (decision, context) pairs from now-closed windows.

        A window closes when a decision arrives with a strictly larger bucket key.
        The context of whichever candidate held the highest confidence is returned
        with the winner — lower-confidence candidates' contexts are discarded.
        """

        incoming_key = self._bucket_key(decision.timestamp)
        to_emit: list[tuple[FusedDecision, Any]] = []

        with self._lock:
            closed_keys = [k for k in self._buckets if k < incoming_key]
            for k in closed_keys:
                to_emit.append(self._buckets.pop(k))

            incumbent = self._buckets.get(incoming_key)
            if incumbent is None or decision.fused_confidence > incumbent[0].fused_confidence:
                self._buckets[incoming_key] = (decision, context)

        return to_emit

    def flush(self) -> list[tuple[FusedDecision, Any]]:
        """Emit all open buckets unconditionally.

        Used by the periodic flush thread and on shutdown to ensure the last
        window is emitted even if no newer detections arrive.
        """
        with self._lock:
            result = list(self._buckets.values())
            self._buckets.clear()
        return result

    @property
    def open_bucket_count(self) -> int:
        with self._lock:
            return len(self._buckets)