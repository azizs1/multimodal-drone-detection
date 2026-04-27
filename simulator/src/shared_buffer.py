"""Thread-safe shared buffer for simulator frames."""

import threading


class SharedBuffer:
    """Thread-safe buffer for storing synchronized RGB and thermal frames."""

    def __init__(self):
        self.lock = threading.Lock()
        self.frame_data = None

    def update(self, timestamp, rgb, thermal):
        """Update buffer with new synchronized frames."""
        with self.lock:
            self.frame_data = {"timestamp": timestamp, "rgb": rgb, "thermal": thermal}

    def get(self):
        """Get latest frame data (thread-safe)."""
        with self.lock:
            return self.frame_data


# Singleton instance used across the simulator
buffer = SharedBuffer()
