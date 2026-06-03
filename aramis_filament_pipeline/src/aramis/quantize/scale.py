"""ScaleSpec: the documented, reproducible LINEAR -> NATIVE projection.

This module is the literal implementation of "ingesting linear data and considering
it across the different measurement systems." Every observational quantity (mass,
position, intensity) becomes an exact :class:`~aramis.geometry.ratio.Ratio` through a
named ``ScaleSpec`` whose choices (kind, unit, reference, denominator) are explicit
and carried in run metadata, so any result is reproducible from the spec alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Literal

from ..geometry.ratio import Ratio

ScaleKind = Literal["linear", "loglinear"]


@dataclass(frozen=True)
class ScaleSpec:
    """A reproducible map from a positive physical value to a native ratio address.

    Parameters
    ----------
    name : a stable identifier written into output headers (e.g. ``mass_log_d1000``).
    kind : ``"linear"`` quantizes ``value / ref``; ``"loglinear"`` quantizes
        ``log10(value / ref) `` shifted to stay positive.
    unit : documented physical unit of ``value`` (free text, e.g. ``"Msun"``).
    denom : quantization denominator; larger -> finer addresses / deeper SB depth.
    ref : reference scale; ``value == ref`` maps near the unit address.
    floor : minimum integer numerator (keeps ratios strictly positive).
    log_offset : additive shift (in dex) for ``loglinear`` so addresses stay >= floor.
    provenance : free text recording *why* this spec was chosen (reproducibility).
    """

    name: str
    kind: ScaleKind = "linear"
    unit: str = "dimensionless"
    denom: int = 1000
    ref: float = 1.0
    floor: int = 1
    log_offset: float = 6.0
    provenance: str = ""

    def quantize_int(self, value: float) -> int:
        """Map a positive value to a positive integer address component."""
        if value is None or not math.isfinite(value) or value <= 0:
            return self.floor
        if self.kind == "linear":
            scaled = (value / self.ref) * self.denom
        else:  # loglinear
            scaled = (math.log10(value / self.ref) + self.log_offset) * self.denom
        return max(self.floor, int(round(scaled)))

    def quantize(self, value: float) -> Ratio:
        """Map a positive value to a ratio ``n:denom`` (a point on a unit interval)."""
        return Ratio(self.quantize_int(value), self.denom)

    def inverse(self, r: Ratio) -> float:
        """Approximate physical value of a ratio (reporting only)."""
        frac = r.as_float()
        if self.kind == "linear":
            return frac * self.ref
        return self.ref * (10.0 ** (frac - self.log_offset))

    def to_metadata(self) -> Dict[str, object]:
        """Serializable record for output headers and run configs."""
        return {
            "scale_name": self.name,
            "scale_kind": self.kind,
            "scale_unit": self.unit,
            "scale_denom": self.denom,
            "scale_ref": self.ref,
            "scale_floor": self.floor,
            "scale_log_offset": self.log_offset,
            "scale_provenance": self.provenance,
        }


# A sensible default for mass-proxy quantization. Documented, overridable per run.
DEFAULT_MASS_SCALE = ScaleSpec(
    name="mass_linear_d1000",
    kind="linear",
    unit="mass_proxy",
    denom=1000,
    ref=1.0,
    provenance=(
        "Stage-0 default. Linear quantization of mass proxy at denominator 1000; "
        "ratios are compared via continued-fraction tension, so only relative "
        "mass asymmetry matters. Revisit ref/denom when real catalog masses load."
    ),
)
