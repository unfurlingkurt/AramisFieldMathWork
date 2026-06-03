"""Force-balance point — the conventional mass-weighted center."""

from __future__ import annotations

from ..data.schema import Filament
from ..geometry.metric import DEFAULT_METRIC, RatioMetric
from ..quantize.scale import DEFAULT_MASS_SCALE, ScaleSpec
from .base import LocatedObject


class ForceBalancePoint:
    """Center of mass along the axis: ``t = m2 / (m1 + m2)`` from endpoint 1.

    The standard physical estimate: the balance point sits proportionally closer to
    the heavier endpoint. Continuous in the masses (unlike the discrete medoid).
    """

    name = "force_balance"

    def locate(
        self,
        filament: Filament,
        spec: ScaleSpec = DEFAULT_MASS_SCALE,
        metric: RatioMetric = DEFAULT_METRIC,
    ) -> LocatedObject:
        m1, m2 = filament.mass1, filament.mass2
        total = m1 + m2
        t = 0.5 if total <= 0 else m2 / total
        return LocatedObject(system_name=self.name, t=float(t), score=0.0)
