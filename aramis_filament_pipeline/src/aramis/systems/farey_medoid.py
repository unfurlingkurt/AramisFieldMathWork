"""Farey medoid — the native RatioSpace estimate ('medoid = object')."""

from __future__ import annotations

from ..data.schema import Filament
from ..geometry.corridor import axis_corridor, farey_medoid
from ..geometry.metric import DEFAULT_METRIC, RatioMetric
from ..quantize.project import fraction_to_ratio
from ..quantize.scale import DEFAULT_MASS_SCALE, ScaleSpec
from .base import LocatedObject


class FareyMedoid:
    """Locates the center at the corridor member minimizing total tension to samples.

    The native axis corridor is the Stern-Brocot rationals spanning the filament
    axis. Emission samples (axis fractions weighted by intensity) are projected to
    ratios and the medoid is the corridor member with least summed continued-fraction
    tension. The result is reported as that member's axis fraction.
    """

    name = "farey_medoid"

    def __init__(self, depth: int = 6, sample_denom: int = 1000) -> None:
        self.depth = depth
        self.sample_denom = sample_denom

    def locate(
        self,
        filament: Filament,
        spec: ScaleSpec = DEFAULT_MASS_SCALE,
        metric: RatioMetric = DEFAULT_METRIC,
    ) -> LocatedObject:
        candidates = axis_corridor(depth=self.depth)

        if not filament.samples:
            # No emission samples (Stage 1, catalog geometry only): make the native
            # *mass* prediction — snap the center-of-mass fraction to the nearest
            # Farey node. This is the discrete analogue of the force-balance point
            # and is a genuinely distinct, testable prediction.
            m1, m2 = filament.mass1, filament.mass2
            total = m1 + m2
            t_com = 0.5 if total <= 0 else m2 / total
            snapped = min(
                candidates,
                key=lambda r: (abs(r.axis_fraction() - t_com), r.cf_length()),
            )
            return LocatedObject(
                system_name=self.name, t=snapped.axis_fraction(), score=0.0,
                extra={"fallback": "mass_snap", "medoid_ratio": str(snapped),
                       "com_fraction": round(t_com, 6)},
            )
        sample_ratios = [
            fraction_to_ratio(s.s, denom=self.sample_denom) for s in filament.samples
        ]
        weights = [s.intensity for s in filament.samples]
        medoid, score = farey_medoid(candidates, sample_ratios, weights, metric=metric)
        return LocatedObject(
            system_name=self.name,
            t=medoid.axis_fraction(),
            score=score,
            extra={"medoid_ratio": str(medoid), "corridor_size": len(candidates)},
        )
