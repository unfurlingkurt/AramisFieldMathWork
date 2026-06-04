"""Edge relations as native ratios, and their continued-fraction structure.

A relation between connected nodes is a dimensionless ratio with no imposed scale.
Its continued-fraction partial quotients are its native address; the φ-coherence of
a population of relations (density of small quotients) is compared to the
Gauss–Kuzmin law and to rewired nulls.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Sequence, Tuple

from ..geometry.native import continued_fraction_of_float
from ..geometry.ratio import Ratio


def consecutive_difference_ratios(sequence: Sequence[float]) -> List[float]:
    """Ratios of consecutive differences ``|Δ_k| / |Δ_{k+1}|`` along an ordered sequence.

    Scale-free and purely local (no origin, no mean). Degenerate steps (a zero
    difference) are skipped. This isolates the *internal structure* the linear view
    discards when it converts the sequence to positions.
    """
    diffs = [sequence[k + 1] - sequence[k] for k in range(len(sequence) - 1)]
    out: List[float] = []
    for k in range(len(diffs) - 1):
        a, b = abs(diffs[k]), abs(diffs[k + 1])
        if a > 1e-12 and b > 1e-12:
            out.append(a / b)
    return out


def pairwise_ratios(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Element-wise dimensionless ratios ``a_i / b_i`` (e.g. luminosity ratios)."""
    out: List[float] = []
    for x, y in zip(a, b):
        if y not in (0, 0.0) and x > 0 and y > 0:
            out.append(x / y if x >= y else y / x)  # orient >= 1 (relation magnitude)
    return out


def encode_ratio(x: float, max_denominator: int = 10_000) -> Ratio:
    """Exact ratio from a positive float via its continued-fraction convergent.

    Uses the Stern-Brocot path of ``x`` (Fraction.limit_denominator is the convergent
    of the CF), not an imposed ``round(x*scale)``.
    """
    f = Fraction(x).limit_denominator(max_denominator)
    return Ratio(f.numerator, f.denominator)


def phi_coherence_of_floats(
    values: Sequence[float], n_terms: int = 6
) -> Tuple[float, int]:
    """Pooled density of partial quotients ``a_i <= 2`` over many relation-values.

    Returns ``(phi_coherence, n_quotients)``. The integer part a0 is dropped.
    """
    qs: List[int] = []
    for v in values:
        if v > 0:
            qs.extend(continued_fraction_of_float(float(v), n_terms)[1:])
    if not qs:
        return float("nan"), 0
    return sum(1 for a in qs if a <= 2) / len(qs), len(qs)


def high_tension_fraction(values: Sequence[float], n_terms: int = 6,
                          wall: int = 10) -> float:
    """Density of large partial quotients ``a_i > wall`` (the 'high-tension walls')."""
    qs: List[int] = []
    for v in values:
        if v > 0:
            qs.extend(continued_fraction_of_float(float(v), n_terms)[1:])
    if not qs:
        return float("nan")
    return sum(1 for a in qs if a > wall) / len(qs)
