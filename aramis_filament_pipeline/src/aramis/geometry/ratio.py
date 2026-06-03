"""Native RatioSpace geometry: the exact ratio type.

This is the single source of truth for the framework's native geometry. It is a
*superset* of the two pre-existing pieces in this repository:

  * ``phi_domain_analysis/core/discrete_sb_simulator.py`` :: ``Rational`` — exact
    Fraction-backed rational with ``mediant`` and ``to_continued_fraction``.
  * The collaborator ("GPT") starter ``Ratio`` — exact integer pair ``p:q`` with the
    ``compose`` (``⊗``) rule and a ``q == 0`` infinity anchor.

``Ratio`` here is consistency-tested against the canonical ``Rational`` (see
``tests/geometry/test_canonical_bridge.py``) so the two never silently diverge.

Conventions
-----------
* A ratio is stored reduced (``gcd`` removed). The denominator ``q`` is kept
  non-negative; any sign lives on ``p``. Differences may be negative.
* ``q == 0`` is the legal *infinity anchor* ``1:0`` (used as a Stern-Brocot seed).
* ``0:0`` is undefined and rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import Tuple


@dataclass(frozen=True)
class Ratio:
    """An exact ratio ``p:q`` in native (reduced) form.

    ``q == 0`` denotes the infinity anchor ``1:0``. ``0:0`` is rejected.
    """

    p: int
    q: int

    def __post_init__(self) -> None:
        if self.p == 0 and self.q == 0:
            raise ValueError("0:0 is undefined.")
        if self.q == 0:
            # Canonical infinity anchor.
            object.__setattr__(self, "p", 1)
            object.__setattr__(self, "q", 0)
            return
        # Keep denominator positive; carry sign on the numerator.
        p, q = self.p, self.q
        if q < 0:
            p, q = -p, -q
        g = gcd(abs(p), q)
        if g > 1:
            p, q = p // g, q // g
        object.__setattr__(self, "p", p)
        object.__setattr__(self, "q", q)

    # ----- constructors -------------------------------------------------
    @classmethod
    def from_fraction(cls, f: Fraction) -> "Ratio":
        return cls(f.numerator, f.denominator)

    @classmethod
    def infinity(cls) -> "Ratio":
        return cls(1, 0)

    def is_infinite(self) -> bool:
        return self.q == 0

    # ----- exact arithmetic (via Fraction, finite only) -----------------
    def _as_fraction(self) -> Fraction:
        if self.is_infinite():
            raise ZeroDivisionError("Cannot treat the infinity anchor as a Fraction.")
        return Fraction(self.p, self.q)

    def __add__(self, other: "Ratio") -> "Ratio":
        return Ratio.from_fraction(self._as_fraction() + other._as_fraction())

    def __sub__(self, other: "Ratio") -> "Ratio":
        return Ratio.from_fraction(self._as_fraction() - other._as_fraction())

    def __abs__(self) -> "Ratio":
        return Ratio(abs(self.p), self.q)

    # ----- native Stern-Brocot operations -------------------------------
    def mediant(self, other: "Ratio") -> "Ratio":
        """Mediant ``(p1+p2):(q1+q2)`` — the fundamental Stern-Brocot step.

        NOT addition, NOT averaging. Matches the canonical ``Rational.mediant``.
        """
        return Ratio(self.p + other.p, self.q + other.q)

    def compose(self, other: "Ratio") -> "Ratio":
        """The ``⊗`` ratio operation: ``(a:b) ⊗ (c:d) = (a·d):(b·c)``.

        This is the *quotient* ``(a/b) ÷ (c/d)`` expressed as a ratio. It has a right
        identity ``1:1`` (``a ⊗ 1:1 == a``) but, being division, is neither
        commutative nor associative. It is an algebraic operation feeding the
        multiplicative tension, NOT the distance itself — see
        :mod:`aramis.geometry.metric`.
        """
        return Ratio(self.p * other.q, self.q * other.p)

    def cf(self, max_terms: int = 64) -> Tuple[int, ...]:
        """Continued-fraction terms of ``p/q``.

        Matches ``Rational.to_continued_fraction``. For the infinity anchor returns
        an empty tuple (its CF is conceptually unbounded).
        """
        if self.is_infinite():
            return tuple()
        n, d = self.p, self.q
        terms = []
        for _ in range(max_terms):
            if d == 0:
                break
            a = n // d
            terms.append(a)
            n, d = d, n - a * d
        return tuple(terms)

    def cf_length(self) -> int:
        """Number of continued-fraction terms (raw 'complexity').

        Note: ``cf_length`` of ``0:1`` and of ``1:1`` are both 1. This is why the
        metric in :mod:`aramis.geometry.metric` normalizes self-distance to 0.
        """
        return len(self.cf())

    # ----- projection (reporting / plotting only) -----------------------
    def as_float(self) -> float:
        """Float projection ``p/q``. For reporting and comparison only."""
        if self.is_infinite():
            return float("inf")
        return self.p / self.q

    def axis_fraction(self) -> float:
        """Position in ``(0, 1)`` as ``p/(p+q)`` — a Stern-Brocot axis coordinate.

        Maps the ratio onto a normalized filament axis (0 at one endpoint, 1 at the
        other). ``1:0`` -> 1.0, ``0:1`` -> 0.0, ``1:1`` -> 0.5.
        """
        if self.is_infinite():
            return 1.0
        denom = self.p + self.q
        return self.p / denom if denom else 0.0

    # ----- ordering / hashing -------------------------------------------
    def __lt__(self, other: "Ratio") -> bool:
        if self.is_infinite():
            return False
        if other.is_infinite():
            return True
        return self.p * other.q < other.p * self.q

    def __le__(self, other: "Ratio") -> bool:
        return self == other or self < other

    def __str__(self) -> str:
        return f"{self.p}:{self.q}"
