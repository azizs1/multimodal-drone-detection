"""Video ingestion for simulator - reads video files and publishes frame pairs over ZeroMQ."""

import logging
import os
import time
from pathlib import Path

import cv2

from frame_pair_transport import DEFAULT_FRAME_PUB_BIND_ENDPOINT, encode_frame_pair

logger = logging.getLogger(__name__)

# Default video paths - can be overridden by environment variables
DEFAULT_RGB_VIDEO = "videos/drone_visual.mp4"
DEFAULT_THERMAL_VIDEO = "videos/drone_thermal.mp4"

RGB_VIDEO_PATH = os.getenv("RGB_VIDEO_PATH", DEFAULT_RGB_VIDEO)
THERMAL_VIDEO_PATH = os.getenv("THERMAL_VIDEO_PATH", DEFAULT_THERMAL_VIDEO)
PLAYBACK_FPS = int(os.getenv("PLAYBACK_FPS", "30"))
LOOP_VIDEO = os.getenv("LOOP_VIDEO", "true").lower() == "true"
ZMQ_FRAME_BIND_ENDPOINT = os.getenv("ZMQ_FRAME_BIND_ENDPOINT", DEFAULT_FRAME_PUB_BIND_ENDPOINT)
SIM_STREAM_MODE = os.getenv("SIM_STREAM_MODE", "rtsp").lower()

# Target dimensions (matching jetson expectations)
RGB_TARGET_WIDTH = int(os.getenv("RGB_WIDTH", "1280"))
RGB_TARGET_HEIGHT = int(os.getenv("RGB_HEIGHT", "720"))
THERMAL_TARGET_WIDTH = int(os.getenv("THERMAL_WIDTH", "160"))
THERMAL_TARGET_HEIGHT = int(os.getenv("THERMAL_HEIGHT", "120"))


def resize_frame(frame, target_width, target_height):
    """Resize frame to match expected dimensions."""
    if frame.shape[1] != target_width or frame.shape[0] != target_height:
        return cv2.resize(frame, (target_width, target_height))
    return frame


def ensure_bgr(frame):
    """Ensure frame is in BGR format (3 channels)."""
    if len(frame.shape) == 2 or frame.shape[2] == 1:  # Grayscale
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    return frame


def start_ingestion():
    """Main ingestion function that publishes synchronized frames over ZeroMQ."""
    try:
        import zmq
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("pyzmq is required for simulator frame publishing.") from exc

    # Resolve video paths relative to simulator root
    script_dir = Path(__file__).parent.parent
    rgb_video_path = script_dir / RGB_VIDEO_PATH
    thermal_video_path = script_dir / THERMAL_VIDEO_PATH

    if not rgb_video_path.exists():
        raise FileNotFoundError(f"RGB video not found: {rgb_video_path}")
    if not thermal_video_path.exists():
        raise FileNotFoundError(f"Thermal video not found: {thermal_video_path}")

    print("=" * 60)
    print("SIMULATOR VIDEO INGESTION")
    print("=" * 60)
    print(f"RGB video:     {rgb_video_path}")
    print(f"Thermal video: {thermal_video_path}")
    print(f"Target FPS:    {PLAYBACK_FPS}")
    print(f"RGB size:      {RGB_TARGET_WIDTH}x{RGB_TARGET_HEIGHT}")
    print(f"Thermal size:  {THERMAL_TARGET_WIDTH}x{THERMAL_TARGET_HEIGHT}")
    print(f"Loop mode:     {LOOP_VIDEO}")
    print("=" * 60)

    # Open video captures
    rgb_cap = cv2.VideoCapture(str(rgb_video_path))
    thermal_cap = cv2.VideoCapture(str(thermal_video_path))

    if not rgb_cap.isOpened():
        raise RuntimeError(f"Failed to open RGB video: {rgb_video_path}")
    if not thermal_cap.isOpened():
        raise RuntimeError(f"Failed to open thermal video: {thermal_video_path}")

    context = None
    pub_socket = None
    publishers = None

    # Get video properties
    rgb_fps = rgb_cap.get(cv2.CAP_PROP_FPS)
    thermal_fps = thermal_cap.get(cv2.CAP_PROP_FPS)
    rgb_frame_count = int(rgb_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    thermal_frame_count = int(thermal_cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"RGB video:     {rgb_fps:.1f} FPS, {rgb_frame_count} frames")
    print(f"Thermal video: {thermal_fps:.1f} FPS, {thermal_frame_count} frames")
    print("=" * 60)

    # Calculate frame delay for playback rate control
    frame_delay = 1.0 / PLAYBACK_FPS if PLAYBACK_FPS > 0 else 0

    frame_count = 0
    start_time = time.time()
    last_lag_report = time.time()
    max_frame_read_time = 0
    max_sleep_time = 0

    print("Starting video ingestion... Press Ctrl+C to stop")
    print(f"ZeroMQ publish endpoint: {ZMQ_FRAME_BIND_ENDPOINT}")
    print(f"RTSP publish enabled: {SIM_STREAM_MODE == 'rtsp'}")
    print()

    try:
        context = zmq.Context()
        pub_socket = context.socket(zmq.PUB)
        pub_socket.setsockopt(zmq.LINGER, 0)
        pub_socket.bind(ZMQ_FRAME_BIND_ENDPOINT)

        while True:
            loop_start = time.time()

            # Read frames from both videos with timing
            read_start = time.time()
            rgb_ret, rgb_frame = rgb_cap.read()
            thermal_ret, thermal_frame = thermal_cap.read()
            read_duration = time.time() - read_start
            max_frame_read_time = max(max_frame_read_time, read_duration)

            # Check if we've reached the end of either video
            if not rgb_ret or not thermal_ret:
                if LOOP_VIDEO:
                    logger.info("Reached end at frame %s, looping...", frame_count)
                    rgb_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    thermal_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print(f"Reached end at frame {frame_count}, stopping.")
                    break

            # Resize frames to target dimensions
            rgb_frame = resize_frame(rgb_frame, RGB_TARGET_WIDTH, RGB_TARGET_HEIGHT)
            thermal_frame = resize_frame(thermal_frame, THERMAL_TARGET_WIDTH, THERMAL_TARGET_HEIGHT)

            # Ensure BGR format
            rgb_frame = ensure_bgr(rgb_frame)
            thermal_frame = ensure_bgr(thermal_frame)

            # Publish the synchronized frame pair over ZeroMQ.
            timestamp = time.time()
            pub_socket.send_multipart(encode_frame_pair(timestamp, rgb_frame, thermal_frame))

            if SIM_STREAM_MODE == "rtsp":
                if publishers is None:
                    from src.frame_publisher import build_publishers

                    publishers = build_publishers(
                        rgb_shape=rgb_frame.shape,
                        thermal_shape=thermal_frame.shape,
                        fps=PLAYBACK_FPS,
                    )
                    print("Started RTSP publishers for visual and thermal streams")

                rgb_publisher, thermal_publisher = publishers
                rgb_publisher.publish(rgb_frame)
                thermal_publisher.publish(thermal_frame)

            frame_count += 1

            # Print progress
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                print(
                    f"Frame {frame_count:6d} | "
                    f"Elapsed: {elapsed:6.1f}s | "
                    f"FPS: {fps:5.1f} | "
                    f"ZeroMQ frame-pair published"
                )

            # Log slow frame reads
            if read_duration > 0.005:  # >5ms for frame read
                logger.warning("Slow frame read: %.1fms", read_duration * 1000)

            # Maintain playback rate
            if frame_delay > 0:
                elapsed_in_loop = time.time() - loop_start
                sleep_time = max(0, frame_delay - elapsed_in_loop)
                max_sleep_time = max(max_sleep_time, sleep_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif elapsed_in_loop > frame_delay * 1.5:
                    # If we're running behind, log it
                    logger.warning(
                        "Ingestion lag: frame processing took %.1fms (expected %.1fms)",
                        elapsed_in_loop * 1000,
                        frame_delay * 1000,
                    )

            # Log lag stats periodically
            now = time.time()
            if now - last_lag_report > 10.0:
                logger.info(
                    "Ingestion stats: max_frame_read=%.1fms, max_sleep=%.1fms",
                    max_frame_read_time * 1000,
                    max_sleep_time * 1000,
                )
                max_frame_read_time = 0
                max_sleep_time = 0
                last_lag_report = now

    except KeyboardInterrupt:
        print()
        print("Video ingestion stopped by user")
    finally:
        if publishers is not None:
            publishers[0].stop()
            publishers[1].stop()
        rgb_cap.release()
        thermal_cap.release()
        if pub_socket is not None:
            pub_socket.close()
        if context is not None:
            context.term()
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total frames:  {frame_count}")
        print(f"Total time:    {elapsed:.1f}s")
        print(f"Average FPS:   {avg_fps:.1f}")
        print("=" * 60)


def main():
    """Entry point for module execution."""
    start_ingestion()


if __name__ == "__main__":
    main()
