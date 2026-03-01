"""Config for fusion engine (Sprint 1 design)."""

from dataclasses import dataclass, field


@dataclass
class DebounceConfig:
    consecutive_required: int = 2
    window_ms: int = 1000


@dataclass
class FusionConfig:
    weights: dict[str, float] = field(
        default_factory=lambda: {"rgb": 0.6, "thermal": 0.4}
    )
    alert_threshold: float = 0.75
    hold_threshold: float = 0.55
    per_modality_gates: dict[str, float] = field(
        default_factory=lambda: {"rgb": 0.45, "thermal": 0.35}
    )
    eo_ir_required: bool = False  # set True to require thermal confirmation when available
    debounce: DebounceConfig = field(default_factory=DebounceConfig)
    topics: dict[str, str] = field(
        default_factory=lambda: {
            "rgb": "inference.rgb",
            "thermal": "inference.thermal",
            "fused": "fusion.alert",
        }
    )
    buffer_size: int = 256  # ring buffer for recent predictions


DEFAULT_CONFIG = FusionConfig()
