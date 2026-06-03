"""Euclidean midpoint — the 'centroid = projection shadow' baseline."""

from __future__ import annotations

from ..data.schema import Filament
from ..geometry.metric import DEFAULT_METRIC, RatioMetric
from ..quantize.scale import DEFAULT_MASS_SCALE, ScaleSpec
from .base import LocatedObject


class EuclideanMidpoint:
    """Locates the center at the geometric midpoint of the axis (``t = 0.5``).

    Mass- and emission-blind by construction; the null hypothesis the framework
    argues against.
    """

    name = "euclidean_midpoint"

    def locate(
        self,
        filament: Filament,
        spec: ScaleSpec = DEFAULT_MASS_SCALE,
        metric: RatioMetric = DEFAULT_METRIC,
    ) -> LocatedObject:
        return LocatedObject(system_name=self.name, t=0.5, score=0.0)
