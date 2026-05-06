"""Unit tests for WindowAggregator.

Run with: python -m pytest jetson/src/ml/fusion/test_window_aggregator.py -v
"""

from __future__ import annotations

import threading
import uuid

import pytest

from .schemas import FusedDecision
from .window_aggregator import WindowAggregator


def _make_decision(
    timestamp: float,
    fused_confidence: float,
    decision: str = "drone",
) -> FusedDecision:
    return FusedDecision(
        incident_id=str(uuid.uuid4()),
        has_drone=(decision == "drone"),
        fused_confidence=fused_confidence,
        confidence_band=(
            "high" if fused_confidence >= 0.8 else "medium" if fused_confidence >= 0.6 else "low"
        ),
        decision=decision,
        evidence={"rgb": None, "thermal": None},
        per_modality_scores={"rgb": fused_confidence, "thermal": fused_confidence},
        thresholds={"alert": 0.75, "hold": 0.55},
        gating_reason="rgb",
        latency_ms=5.0,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------


def test_same_window_highest_confidence_wins():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.1, 0.90))
    agg.feed(_make_decision(1776.9, 0.75))
    emitted = agg.feed(_make_decision(1777.1, 0.80))  # new window triggers eviction
    assert len(emitted) == 1
    winner, _ = emitted[0]
    assert winner.fused_confidence == 0.90


def test_same_window_lower_confidence_arrives_first():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.1, 0.75))
    agg.feed(_make_decision(1776.8, 0.90))
    emitted = agg.feed(_make_decision(1777.1, 0.50))
    assert len(emitted) == 1
    winner, _ = emitted[0]
    assert winner.fused_confidence == 0.90


def test_different_windows_emit_separately():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.0, 0.80))
    emitted_1 = agg.feed(_make_decision(1777.2, 0.70))
    assert len(emitted_1) == 1
    assert emitted_1[0][0].fused_confidence == 0.80

    emitted_2 = agg.feed(_make_decision(1778.1, 0.60))
    assert len(emitted_2) == 1
    assert emitted_2[0][0].fused_confidence == 0.70


def test_flush_emits_open_bucket():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.5, 0.85))
    result = agg.flush()
    assert len(result) == 1
    winner, _ = result[0]
    assert winner.fused_confidence == 0.85


def test_flush_clears_state():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.5, 0.85))
    agg.flush()
    assert agg.flush() == []
    assert agg.open_bucket_count == 0


def test_flush_then_refeed_re_inserts():
    agg = WindowAggregator(window_width_seconds=1.0)
    d = _make_decision(1776.5, 0.85)
    agg.feed(d)
    agg.flush()
    agg.feed(d)
    assert agg.open_bucket_count == 1


def test_three_second_window_groups_correctly():
    agg = WindowAggregator(window_width_seconds=3.0)
    agg.feed(_make_decision(1776.0, 0.80))  # bucket 592
    agg.feed(_make_decision(1778.9, 0.90))  # bucket 592 (same)
    emitted = agg.feed(_make_decision(1779.0, 0.70))  # bucket 593 → evicts 592
    assert len(emitted) == 1
    assert emitted[0][0].fused_confidence == 0.90


def test_gap_larger_than_one_window_only_nonempty_buckets_emitted():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.1, 0.80))  # bucket 1776
    # skip 1777, 1778, 1779 — no detections
    emitted = agg.feed(_make_decision(1780.5, 0.70))  # bucket 1780 → evicts 1776 only
    assert len(emitted) == 1
    assert emitted[0][0].fused_confidence == 0.80


# ---------------------------------------------------------------------------
# Context passthrough (enables deferred image upload)
# ---------------------------------------------------------------------------


def test_context_travels_with_winner():
    """The context passed with the highest-confidence decision is returned on emission."""
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.1, 0.75), context=["low-conf-preds"])
    agg.feed(_make_decision(1776.8, 0.90), context=["high-conf-preds"])
    emitted = agg.feed(_make_decision(1777.1, 0.50), context=["next-window-preds"])
    assert len(emitted) == 1
    winner, ctx = emitted[0]
    assert winner.fused_confidence == 0.90
    assert ctx == ["high-conf-preds"]


def test_context_none_by_default():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.0, 0.85))
    winner, ctx = agg.flush()[0]
    assert ctx is None


def test_flush_returns_winner_context():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.0, 0.85), context="my-preds")
    result = agg.flush()
    _, ctx = result[0]
    assert ctx == "my-preds"


# ---------------------------------------------------------------------------
# Mixed decision types
# ---------------------------------------------------------------------------


def test_none_and_drone_in_same_window_keeps_highest_confidence():
    agg = WindowAggregator(window_width_seconds=1.0)
    agg.feed(_make_decision(1776.1, 0.40, decision="none"))
    agg.feed(_make_decision(1776.8, 0.85, decision="drone"))
    emitted = agg.feed(_make_decision(1777.1, 0.50, decision="drone"))
    assert len(emitted) == 1
    assert emitted[0][0].fused_confidence == 0.85


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_invalid_window_width_raises():
    with pytest.raises(ValueError):
        WindowAggregator(window_width_seconds=0)

    with pytest.raises(ValueError):
        WindowAggregator(window_width_seconds=-1.0)


def test_empty_aggregator_flush_returns_empty():
    agg = WindowAggregator()
    assert agg.flush() == []


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


def test_concurrent_writes_keep_max_confidence():
    agg = WindowAggregator(window_width_seconds=10.0)  # one big window for all threads
    base_ts = 1776.0
    confidences = [i / 100.0 for i in range(1, 21)]  # 0.01 to 0.20
    expected_max = max(confidences)

    threads = [
        threading.Thread(target=agg.feed, args=(_make_decision(base_ts + i * 0.01, c),))
        for i, c in enumerate(confidences)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    result = agg.flush()
    assert len(result) == 1
    winner, _ = result[0]
    assert abs(winner.fused_confidence - expected_max) < 1e-9
