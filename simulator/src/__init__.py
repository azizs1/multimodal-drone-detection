"""Simulator package for video ingestion and frame transport."""

import logging

# Configure logging with timestamps, level, logger name, and message.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
