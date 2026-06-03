"""The MeasurementSystem abstraction.

Each system answers the same question on identical inputs — *where along the
filament axis is the central object?* — so Euclidean midpoint, force-balance, and
Farey medoid are directly comparable. The located position is reported as an axis
fraction ``t in [0, 1]`` from endpoint 1, which is the quantity compared against the
observed emission peak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..data.schema import Filament
from ..geometry.metric import DEFAULT_METRIC, RatioMetric
from ..quantize.scale import DEFAULT_MASS_SCALE, ScaleSpec


@dataclass(frozen=True)
class LocatedObject:
    """The located central object for one filament under one measurement system."""

    system_name: str
    t: float                 # axis fraction from endpoint 1, in [0, 1]
    score: float = 0.0       # lower = better fit to samples (0 if not score-based)
    extra: dict = field(default_factory=dict)


@runtime_checkable
class MeasurementSystem(Protocol):
    """A way to locate a filament's central object from endpoints + samples."""

    name: str

    def locate(
        self,
        filament: Filament,
        spec: ScaleSpec = DEFAULT_MASS_SCALE,
        metric: RatioMetric = DEFAULT_METRIC,
    ) -> LocatedObject:
        ...
