"""Asynchronous UDP MPEG-TS frame publishers for inference outputs."""

from __future__ import annotations

import os
import queue
import threading
from contextlib import suppress

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

_GST_INITIALIZED = False


def _ensure_gst_initialized() -> None:
    global _GST_INITIALIZED
    if _GST_INITIALIZED:
        return
    Gst.init(None)
    _GST_INITIALIZED = True


class GstUdpPublisher:
    """Publish BGR frames to UDP MPEG-TS using GStreamer appsrc."""

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        fps: int,
        host: str,
        port: int,
        bitrate_kbps: int,
    ):
        _ensure_gst_initialized()
        self.name = name
        self.width = int(width)
        self.height = int(height)
        self.fps = max(1, int(fps))
        self.host = host
        self.port = int(port)
        self.bitrate_kbps = max(256, int(bitrate_kbps))

        self._queue: queue.Queue = queue.Queue(maxsize=1)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._running = False
        self._frame_index = 0

        pipeline_desc = (
            f"appsrc name=src is-live=true block=false format=time "
            f"caps=video/x-raw,format=BGR,width={self.width},height={self.height},framerate={self.fps}/1 ! "
            "queue leaky=downstream max-size-buffers=1 ! "
            "videoconvert ! "
            f"x264enc tune=zerolatency bitrate={self.bitrate_kbps} speed-preset=ultrafast "
            "key-int-max=30 insert-vui=true byte-stream=true aud=true ! "
            "mpegtsmux alignment=7 ! "
            f"udpsink host={self.host} port={self.port} sync=false async=false qos=false"
        )
        self._pipeline = Gst.parse_launch(pipeline_desc)
        self._appsrc = self._pipeline.get_by_name("src")

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._pipeline.set_state(Gst.State.PLAYING)
        self._thread.start()

    def publish(self, frame) -> None:
        if not self._running:
            self.start()

        if self._queue.full():
            with suppress(queue.Empty):
                _ = self._queue.get_nowait()

        with suppress(queue.Full):
            self._queue.put_nowait(frame)

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        with suppress(queue.Full):
            self._queue.put_nowait(None)
        self._thread.join(timeout=2)
        with suppress(Exception):
            self._appsrc.emit("end-of-stream")
        self._pipeline.set_state(Gst.State.NULL)

    def _worker(self) -> None:
        while self._running:
            try:
                frame = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if frame is None:
                continue

            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                try:
                    import cv2
                except ImportError:
                    continue
                frame = cv2.resize(frame, (self.width, self.height))

            if not frame.flags["C_CONTIGUOUS"]:
                frame = frame.copy(order="C")

            buffer = Gst.Buffer.new_allocate(None, frame.nbytes, None)
            buffer.fill(0, frame.tobytes())

            duration = Gst.util_uint64_scale_int(1, Gst.SECOND, self.fps)
            pts = self._frame_index * duration
            buffer.pts = pts
            buffer.dts = pts
            buffer.duration = duration
            self._frame_index += 1

            ret = self._appsrc.emit("push-buffer", buffer)
            if ret != Gst.FlowReturn.OK:
                print(f"{self.name} push-buffer failed: {ret}")


def build_publishers(rgb_shape, thermal_shape, fps: int):
    """Create RGB and thermal UDP MPEG-TS publishers from environment settings."""
    stream_fps = max(1, int(os.getenv("INFERENCE_STREAM_FPS", str(fps))))
    host = os.getenv("INFERENCE_STREAM_UDP_HOST", "127.0.0.1")

    rgb_height, rgb_width = rgb_shape[:2]
    thermal_height, thermal_width = thermal_shape[:2]

    rgb_width = int(os.getenv("INFERENCE_VISUAL_OUT_WIDTH", str(rgb_width)))
    rgb_height = int(os.getenv("INFERENCE_VISUAL_OUT_HEIGHT", str(rgb_height)))
    thermal_width = int(os.getenv("INFERENCE_THERMAL_OUT_WIDTH", str(thermal_width)))
    thermal_height = int(os.getenv("INFERENCE_THERMAL_OUT_HEIGHT", str(thermal_height)))

    rgb_port = int(os.getenv("INFERENCE_VISUAL_UDP_PORT", "6000"))
    thermal_port = int(os.getenv("INFERENCE_THERMAL_UDP_PORT", "6002"))
    rgb_bitrate = int(os.getenv("INFERENCE_VISUAL_BITRATE_KBPS", "4000"))
    thermal_bitrate = int(os.getenv("INFERENCE_THERMAL_BITRATE_KBPS", "2000"))

    rgb_publisher = GstUdpPublisher(
        name="visual-fused",
        width=rgb_width,
        height=rgb_height,
        fps=stream_fps,
        host=host,
        port=rgb_port,
        bitrate_kbps=rgb_bitrate,
    )
    thermal_publisher = GstUdpPublisher(
        name="thermal-fused",
        width=thermal_width,
        height=thermal_height,
        fps=stream_fps,
        host=host,
        port=thermal_port,
        bitrate_kbps=thermal_bitrate,
    )
    return rgb_publisher, thermal_publisher
