"""Asynchronous RTSP frame publishers used by the stream-simulator.

Frames are encoded with libx264 via PyAV and pushed to MediaMTX. Each publisher
uses a single-item queue to prioritize the newest frame over stale frames.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from contextlib import suppress

import av
import cv2

logger = logging.getLogger(__name__)


class AvStreamPublisher:
    """Publish BGR frames to an RTSP endpoint using PyAV.

    The worker thread handles resize, encode, and mux operations. Diagnostic
    timing logs are emitted periodically to expose encode-side bottlenecks.
    """

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        fps: int,
        stream_url: str,
    ):
        self.name = name
        self.width = width
        self.height = height
        self.fps = max(1, int(fps))
        self.stream_url = stream_url

        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._running = False

        self._container = None
        self._stream = None
        self._writer_init_failed = False

        self.published_frames = 0
        self.dropped_frames = 0

        # Diagnostics
        self._frame_times = []  # Track encoding time per frame
        self._last_stats_report = time.time()

    def _open_writer(self):
        if self._container is not None and self._stream is not None:
            return

        if self._writer_init_failed:
            return

        try:
            self._container = av.open(
                self.stream_url,
                mode="w",
                format="rtsp",
                options={
                    "rtsp_transport": os.getenv("SIM_RTSP_TRANSPORT", "tcp"),
                    "muxdelay": "0",
                    "muxpreload": "0",
                },
            )
            self._stream = self._container.add_stream("libx264", rate=self.fps)
            self._stream.width = self.width
            self._stream.height = self.height
            self._stream.pix_fmt = "yuv420p"

            # Frequent keyframes make HLS segmenting and recovery much smoother.
            keyint = max(1, int(os.getenv("SIM_X264_KEYINT", str(self.fps))))
            self._stream.options = {
                "preset": os.getenv("SIM_X264_PRESET", "ultrafast"),
                "tune": os.getenv("SIM_X264_TUNE", "zerolatency"),
                "crf": os.getenv("SIM_X264_CRF", "28"),
                "x264-params": (
                    f"keyint={keyint}:min-keyint={keyint}:scenecut=0:"
                    f"vbv-maxrate={os.getenv('SIM_X264_MAXRATE', '2000')}:"
                    f"vbv-bufsize={os.getenv('SIM_X264_BUFSIZE', '2000')}"
                ),
            }
        except Exception as exc:
            self._writer_init_failed = True
            print(
                f"[{self.name}] failed to initialize PyAV RTSP writer for {self.stream_url}: {exc}"
            )
            self._close_writer()

    def _close_writer(self):
        if self._container is not None:
            with suppress(Exception):
                self._container.close()
        self._container = None
        self._stream = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread.start()

    def publish(self, frame):
        if not self._running:
            self.start()

        if self._queue.full():
            try:
                self._queue.get_nowait()
                self.dropped_frames += 1
            except queue.Empty:
                pass

        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            self.dropped_frames += 1

    def stop(self):
        if not self._running:
            return

        self._running = False
        with suppress(queue.Full):
            self._queue.put_nowait(None)

        self._thread.join(timeout=2)
        self._close_writer()

    def stats(self) -> dict[str, int]:
        return {"published": self.published_frames, "dropped": self.dropped_frames}

    def _log_stats(self):
        """Log diagnostic statistics."""
        now = time.time()
        self._last_stats_report = now

        avg_encode_ms = 0
        max_encode_ms = 0
        if self._frame_times:
            avg_encode_ms = (sum(self._frame_times) / len(self._frame_times)) * 1000
            max_encode_ms = max(self._frame_times) * 1000
            self._frame_times.clear()

        queue_size = self._queue.qsize()
        logger.info(
            f"[{self.name}] stats: published={self.published_frames}, "
            f"dropped={self.dropped_frames}, queue_size={queue_size}, "
            f"avg_encode={avg_encode_ms:.1f}ms, max_encode={max_encode_ms:.1f}ms"
        )

    def _encode_and_mux(self, frame):
        encode_start = time.time()
        av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
        packets_encoded = 0
        for packet in self._stream.encode(av_frame):
            self._container.mux(packet)
            packets_encoded += 1
        encode_duration = time.time() - encode_start
        self._frame_times.append(encode_duration)
        self.published_frames += 1

        # Log slow frames
        if encode_duration > 0.05:  # >50ms is slow
            logger.warning(
                f"[{self.name}] slow encode: {encode_duration * 1000:.1f}ms, "
                f"packets={packets_encoded}, queue_size={self._queue.qsize()}"
            )

    def _flush_encoder(self):
        if self._stream is None or self._container is None:
            return
        try:
            for packet in self._stream.encode(None):
                self._container.mux(packet)
        except Exception:
            pass

    def _worker(self):
        worker_start = time.time()
        logger.info(f"[{self.name}] worker thread started")
        while self._running:
            try:
                frame = self._queue.get(timeout=0.25)
            except queue.Empty:
                # Log stats periodically even during idle periods
                now = time.time()
                if now - self._last_stats_report > 5.0:
                    self._log_stats()
                continue

            if frame is None:
                continue

            resize_start = time.time()
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            resize_duration = time.time() - resize_start
            if resize_duration > 0.01:
                logger.warning(f"[{self.name}] slow resize: {resize_duration * 1000:.1f}ms")

            self._open_writer()
            if self._container is None or self._stream is None:
                self.dropped_frames += 1
                logger.error(f"[{self.name}] writer not available, dropping frame")
                continue

            try:
                self._encode_and_mux(frame)
            except Exception as exc:
                self.dropped_frames += 1
                logger.error(f"[{self.name}] publish error: {exc}")
                self._flush_encoder()
                self._close_writer()

            # Log stats periodically
            now = time.time()
            if now - self._last_stats_report > 5.0:
                self._log_stats()

        self._flush_encoder()
        logger.info(f"[{self.name}] worker thread stopped after {time.time() - worker_start:.1f}s")


def build_publishers(rgb_shape, thermal_shape, fps: int):
    """Create RGB and thermal RTSP publishers from environment settings."""
    host = os.getenv("SIM_STREAM_HOST", "mediamtx")
    stream_fps = max(1, int(os.getenv("SIM_STREAM_FPS", str(fps))))

    rgb_height, rgb_width = rgb_shape[:2]
    thermal_height, thermal_width = thermal_shape[:2]

    rgb_width = int(os.getenv("SIM_VISUAL_OUT_WIDTH", str(rgb_width)))
    rgb_height = int(os.getenv("SIM_VISUAL_OUT_HEIGHT", str(rgb_height)))
    thermal_width = int(os.getenv("SIM_THERMAL_OUT_WIDTH", str(thermal_width)))
    thermal_height = int(os.getenv("SIM_THERMAL_OUT_HEIGHT", str(thermal_height)))

    visual_url = os.getenv("SIM_VISUAL_RTSP_URL", f"rtsp://{host}:8554/visual")
    thermal_url = os.getenv("SIM_THERMAL_RTSP_URL", f"rtsp://{host}:8554/thermal")

    rgb_publisher = AvStreamPublisher(
        name="visual",
        width=rgb_width,
        height=rgb_height,
        fps=stream_fps,
        stream_url=visual_url,
    )

    thermal_publisher = AvStreamPublisher(
        name="thermal",
        width=thermal_width,
        height=thermal_height,
        fps=stream_fps,
        stream_url=thermal_url,
    )

    return rgb_publisher, thermal_publisher
