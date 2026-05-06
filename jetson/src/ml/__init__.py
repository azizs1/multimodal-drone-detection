"""ML package namespace for inference and fusion modules."""
from .fusion.config import DEFAULT_CONFIG, FusionConfig, WindowConfig
from .fusion.fusion_core import FusionEngine
from .fusion.schemas import FusedDecision, ModalityPrediction
from .fusion.window_aggregator import WindowAggregator

__all__ = [
    "FusionConfig",
    "WindowConfig",
    "DEFAULT_CONFIG",
    "FusionEngine",
    "ModalityPrediction",
    "FusedDecision",
    "WindowAggregator",
]
