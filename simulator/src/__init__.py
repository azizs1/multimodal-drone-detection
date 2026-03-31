"""Simulator package for reading video files and populating shared buffer."""

import logging

from .shared_buffer import buffer

__all__ = ["buffer"]

# Configure logging with timestamps, level, logger name, and message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
