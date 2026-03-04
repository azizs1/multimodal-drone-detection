import threading


class SharedBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame_data = None

    def update(self, timestamp, rgb, thermal):
        with self.lock:
            self.frame_data = {
                "timestamp": timestamp,
                "rgb": rgb,
                "thermal": thermal
            }

    def get(self):
        with self.lock:
            return self.frame_data

# this singleton is what gets used in ingest_gi.py
buffer = SharedBuffer()
