"""Projections from linear/observational quantities into native ratio space."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from ..geometry.ratio import Ratio
from .scale import ScaleSpec


def mass_to_ratio(mass: float, spec: ScaleSpec) -> Ratio:
    """A single mass proxy as a native ratio ``n:denom``."""
    return spec.quantize(mass)


def pair_mass_ratio(m1: float, m2: float, spec: ScaleSpec) -> Ratio:
    """Endpoint mass asymmetry as the native ratio ``M1:M2``.

    This is the corridor-defining quantity: a 1:1 pair is symmetric, an 8:1 pair is
    strongly skewed and should pull the medoid off the Euclidean midpoint.
    """
    n1 = spec.quantize_int(m1)
    n2 = spec.quantize_int(m2)
    return Ratio(n1, n2)


def axis_anchors(mass_ratio: Ratio) -> Tuple[Ratio, Ratio]:
    """Corridor anchors for a filament from its endpoint mass ratio.

    For the minimal model the anchors are ``M1:(M1+M2)`` and ``M2:(M1+M2)`` — the two
    mass-weighted attractors. Their axis fractions bracket the mass-balance region.
    """
    total = mass_ratio.p + mass_ratio.q
    left = Ratio(mass_ratio.p, total)
    right = Ratio(mass_ratio.q, total)
    return left, right


def fraction_to_ratio(s: float, denom: int = 1000, floor: int = 1) -> Ratio:
    """Map an axis fraction ``s in (0, 1)`` to a ratio with that axis fraction.

    Inverse of :meth:`Ratio.axis_fraction`: ``s -> round(s*denom):round((1-s)*denom)``.
    Clipped so both components are >= ``floor``.
    """
    s = min(max(s, 0.0), 1.0)
    p = max(floor, int(round(s * denom)))
    q = max(floor, int(round((1.0 - s) * denom)))
    return Ratio(p, q)


def fractions_to_samples(
    fractions: Iterable[float], denom: int = 1000
) -> List[Ratio]:
    """Convert observed axis fractions (e.g. emission-peak positions) to ratios."""
    return [fraction_to_ratio(s, denom=denom) for s in fractions]
