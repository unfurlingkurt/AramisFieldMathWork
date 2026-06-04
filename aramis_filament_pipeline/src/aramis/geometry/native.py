"""Native RatioSpace operations — the corrected, non-linear core.

Per the framework directive, the following linear operations are forbidden and are
NOT used here: Euclidean difference ``|a-b|`` as distance, ``argmin``/gradient
optimization, ``sum`` of tensions, uniform spacing, and Gaussian/mean/z-score
statistics. The legal operations are:

  * composition  ``a ⊗ b = (a.p*b.q):(a.q*b.p)``        (Ratio.compose)
  * mediant      ``a ⊕ b = (a.p+b.p):(a.q+b.q)``        (Ratio.mediant)
  * tension      ``T(a,b) = cf_length(a ⊗ b)``           (native distance)

Aggregation of many samples is the **mediant fold** (constraint survival, not
optimization). The null is **Gauss–Kuzmin**; the statistic is **φ-coherence** (the
density of small partial quotients).
"""

from __future__ import annotations

import math
from typing import List, Sequence

from .ratio import Ratio

# Gauss–Kuzmin probability that a continued-fraction partial quotient is <= 2:
#   P(a=1)+P(a=2) = log2(4/3)+log2(9/8) = log2(3/2)
GAUSS_KUZMIN_LE2 = math.log2(3 / 2)  # = 0.584962...


def native_tension(a: Ratio, b: Ratio) -> int:
    """Native distance: continued-fraction length of the composition ``a ⊗ b``."""
    return a.compose(b).cf_length()


def mediant_fold(ratios: Sequence[Ratio]) -> Ratio:
    """Combine samples by successive mediant — the native 'center of gravity'.

    NOT an average and NOT an argmin: the fold is order-dependent crystallization by
    mediant composition, ``(((r1 ⊕ r2) ⊕ r3) ⊕ …)``.
    """
    if not ratios:
        raise ValueError("mediant_fold requires at least one ratio.")
    acc = ratios[0]
    for r in ratios[1:]:
        acc = acc.mediant(r)
    return acc


def continued_fraction_of_float(x: float, n_terms: int = 12) -> List[int]:
    """Partial quotients of a real ``x`` in (0,1] — the native address of a position.

    Uses the standard CF algorithm directly on the float; reliable for the first
    several terms (where double precision holds), which is where the φ-coherence
    signal lives. No scale/denominator is imposed.
    """
    terms: List[int] = []
    if x <= 0:
        return terms
    for _ in range(n_terms):
        a = math.floor(x)
        terms.append(a)
        frac = x - a
        if frac < 1e-12:
            break
        x = 1.0 / frac
    return terms


def phi_coherence(partial_quotients: Sequence[int], drop_integer_part: bool = True) -> float:
    """Density of small partial quotients (a_i <= 2) — compare to GAUSS_KUZMIN_LE2.

    ``drop_integer_part`` skips a0 (the integer part), which carries no positional
    information for x in (0,1) where a0 = 0.
    """
    qs = list(partial_quotients)
    if drop_integer_part and qs:
        qs = qs[1:]
    if not qs:
        return float("nan")
    return sum(1 for a in qs if a <= 2) / len(qs)


def fibonacci_indices(count: int, start: int = 0) -> List[int]:
    """φ-spaced sample indices: start + {0,1,2,3,5,8,13,21,...} (Fibonacci offsets).

    Native (non-uniform) sampling along an axis; uniform linear steps are forbidden.
    """
    fibs = [0, 1, 2, 3]
    while len(fibs) < count:
        fibs.append(fibs[-1] + fibs[-2])
    return [start + f for f in fibs[:count]]
