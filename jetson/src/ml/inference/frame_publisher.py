"""Asynchronous RTSP frame publishers for inference outputs."""

from __future__ import annotations

import os
import queue
import threading
from contextlib import suppress


class AvStreamPublisher:
    """Publish BGR frames to an RTSP endpoint using PyAV."""

    def __init__(self, name: str, width: int, height: int, fps: int, stream_url: str):
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

    def _open_writer(self):
        if self._container is not None and self._stream is not None:
            return
        if self._writer_init_failed:
            return

        try:
            import av
        except ImportError as exc:  # pragma: no cover - runtime dependency
            raise RuntimeError("PyAV is required for RTSP publishing.") from exc

        try:
            self._container = av.open(
                self.stream_url,
                mode="w",
                format="rtsp",
                options={
                    "rtsp_transport": os.getenv(
                        "INFERENCE_RTSP_TRANSPORT", os.getenv("SIM_RTSP_TRANSPORT", "tcp")
                    ),
                    "muxdelay": "0",
                    "muxpreload": "0",
                },
            )
            self._stream = self._container.add_stream("libx264", rate=self.fps)
            self._stream.width = self.width
            self._stream.height = self.height
            self._stream.pix_fmt = "yuv420p"

            keyint = max(
                1,
                int(
                    os.getenv(
                        "INFERENCE_X264_KEYINT",
                        os.getenv("SIM_X264_KEYINT", str(self.fps)),
                    )
                ),
            )
            self._stream.options = {
                "preset": os.getenv(
                    "INFERENCE_X264_PRESET", os.getenv("SIM_X264_PRESET", "ultrafast")
                ),
                "tune": os.getenv("INFERENCE_X264_TUNE", os.getenv("SIM_X264_TUNE", "zerolatency")),
                "crf": os.getenv("INFERENCE_X264_CRF", os.getenv("SIM_X264_CRF", "28")),
                "x264-params": (
                    f"keyint={keyint}:min-keyint={keyint}:scenecut=0:"
                    f"vbv-maxrate={os.getenv('INFERENCE_X264_MAXRATE', os.getenv('SIM_X264_MAXRATE', '2000'))}:"
                    f"vbv-bufsize={os.getenv('INFERENCE_X264_BUFSIZE', os.getenv('SIM_X264_BUFSIZE', '2000'))}"
                ),
            }
        except Exception:
            self._writer_init_failed = True
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
            with suppress(queue.Empty):
                self._queue.get_nowait()

        with suppress(queue.Full):
            self._queue.put_nowait(frame)

    def stop(self):
        if not self._running:
            return

        self._running = False
        with suppress(queue.Full):
            self._queue.put_nowait(None)

        self._thread.join(timeout=2)
        self._close_writer()

    def _flush_encoder(self):
        if self._stream is None or self._container is None:
            return
        with suppress(Exception):
            for packet in self._stream.encode(None):
                self._container.mux(packet)

    def _worker(self):
        while self._running:
            try:
                frame = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if frame is None:
                continue

            try:
                import av
                import cv2
            except ImportError as exc:  # pragma: no cover - runtime dependency
                raise RuntimeError("PyAV and OpenCV are required for RTSP publishing.") from exc

            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))

            self._open_writer()
            if self._container is None or self._stream is None:
                continue

            try:
                av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
                for packet in self._stream.encode(av_frame):
                    self._container.mux(packet)
            except Exception:
                self._flush_encoder()
                self._close_writer()

        self._flush_encoder()


def build_publishers(rgb_shape, thermal_shape, fps: int):
    """Create RGB and thermal RTSP publishers from environment settings."""
    host = os.getenv("INFERENCE_STREAM_HOST", os.getenv("SIM_STREAM_HOST", "mediamtx"))
    stream_fps = max(1, int(os.getenv("INFERENCE_STREAM_FPS", str(fps))))

    rgb_height, rgb_width = rgb_shape[:2]
    thermal_height, thermal_width = thermal_shape[:2]

    rgb_width = int(os.getenv("INFERENCE_VISUAL_OUT_WIDTH", str(rgb_width)))
    rgb_height = int(os.getenv("INFERENCE_VISUAL_OUT_HEIGHT", str(rgb_height)))
    thermal_width = int(os.getenv("INFERENCE_THERMAL_OUT_WIDTH", str(thermal_width)))
    thermal_height = int(os.getenv("INFERENCE_THERMAL_OUT_HEIGHT", str(thermal_height)))

    visual_url = os.getenv(
        "INFERENCE_VISUAL_RTSP_URL",
        os.getenv("SIM_VISUAL_RTSP_URL", f"rtsp://{host}:8554/visual"),
    )
    thermal_url = os.getenv(
        "INFERENCE_THERMAL_RTSP_URL",
        os.getenv("SIM_THERMAL_RTSP_URL", f"rtsp://{host}:8554/thermal"),
    )

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
