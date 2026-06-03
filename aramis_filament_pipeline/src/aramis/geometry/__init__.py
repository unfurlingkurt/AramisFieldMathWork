"""Native RatioSpace geometry — the framework's single source of truth."""

from .corridor import axis_corridor, corridor_candidates, farey_medoid
from .metric import (
    DEFAULT_METRIC,
    RatioMetric,
    axiom_report,
    tension_additive,
    tension_multiplicative,
)
from .ratio import Ratio

__all__ = [
    "Ratio",
    "RatioMetric",
    "DEFAULT_METRIC",
    "tension_additive",
    "tension_multiplicative",
    "axiom_report",
    "corridor_candidates",
    "axis_corridor",
    "farey_medoid",
]
