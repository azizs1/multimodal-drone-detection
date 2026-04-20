"""
Video ingestion for simulator - reads video files and populates shared buffer.

This can be run standalone or imported as a module for use in your inference code.

Example usage:
    # Standalone
    python -m src.video_ingestion

    # In your inference code
    from src.video_ingestion import start_ingestion
    import threading

    # Start ingestion in background thread
    thread = threading.Thread(target=start_ingestion, daemon=True)
    thread.start()

    # Your inference code here
    from src import buffer
    while True:
        frame_data = buffer.get()
        if frame_data:
            # Process frames...
"""

import logging
import os
import threading
import time
from pathlib import Path

import cv2

from . import buffer

logger = logging.getLogger(__name__)

# Default video paths - can be overridden by environment variables
DEFAULT_RGB_VIDEO = "videos/visible.mp4"
DEFAULT_THERMAL_VIDEO = "videos/infrared.mp4"

RGB_VIDEO_PATH = os.getenv("RGB_VIDEO_PATH", DEFAULT_RGB_VIDEO)
THERMAL_VIDEO_PATH = os.getenv("THERMAL_VIDEO_PATH", DEFAULT_THERMAL_VIDEO)
PLAYBACK_FPS = int(os.getenv("PLAYBACK_FPS", 30))
LOOP_VIDEO = os.getenv("LOOP_VIDEO", "true").lower() == "true"

# Target dimensions (matching jetson expectations)
RGB_TARGET_WIDTH = int(os.getenv("RGB_WIDTH", 1280))
RGB_TARGET_HEIGHT = int(os.getenv("RGB_HEIGHT", 720))
THERMAL_TARGET_WIDTH = int(os.getenv("THERMAL_WIDTH", 160))
THERMAL_TARGET_HEIGHT = int(os.getenv("THERMAL_HEIGHT", 120))


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
    """Main ingestion function that can be called from other modules."""
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
    print()

    try:
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
                    logger.info(f"Reached end at frame {frame_count}, looping...")
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

            # Update shared buffer with timestamp (microseconds)
            timestamp = int(time.time() * 1_000_000)
            buffer.update(timestamp, rgb_frame, thermal_frame)

            frame_count += 1

            # Print progress
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                print(
                    f"Frame {frame_count:6d} | "
                    f"Elapsed: {elapsed:6.1f}s | "
                    f"FPS: {fps:5.1f} | "
                    f"Buffer updated"
                )

            # Log slow frame reads
            if read_duration > 0.005:  # >5ms for frame read
                logger.warning(f"Slow frame read: {read_duration * 1000:.1f}ms")

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
                        f"Ingestion lag: frame processing took {elapsed_in_loop * 1000:.1f}ms "
                        f"(expected {frame_delay * 1000:.1f}ms)"
                    )

            # Log lag stats periodically
            now = time.time()
            if now - last_lag_report > 10.0:
                logger.info(
                    f"Ingestion stats: "
                    f"max_frame_read={max_frame_read_time * 1000:.1f}ms, "
                    f"max_sleep={max_sleep_time * 1000:.1f}ms"
                )
                max_frame_read_time = 0
                max_sleep_time = 0
                last_lag_report = now

    except KeyboardInterrupt:
        print()
        print("Video ingestion stopped by user")
    finally:
        rgb_cap.release()
        thermal_cap.release()
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
    """Entry point for module execution.

    Starts inference in the background and ingestion in the foreground.
    """
    # Import here to avoid circular imports
    try:
        from .inference import run_inference

        # Start inference in background thread
        inference_thread = threading.Thread(target=run_inference, daemon=True)
        inference_thread.start()

        # Give inference time to initialize
        time.sleep(0.5)
    except ImportError as exc:
        print(f"Warning: failed to import inference module ({exc}), running ingestion only")

    # Run ingestion in main thread
    start_ingestion()


if __name__ == "__main__":
    main()
