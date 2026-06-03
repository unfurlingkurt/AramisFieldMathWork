"""The native RatioSpace metric (tension).

The load-bearing decision of this whole package. There are two inequivalent
"tensions" in the prior material:

* **additive**  ``T_add(x, y) = cf_length(|x - y|)`` — used by the existing repo
  (``Rational.tension``) and by ``RATIOSPACE_FINDINGS_SUMMARY.md``.
* **multiplicative** ``T_mul(x, y) = cf_length(x ⊗ y)`` — the collaborator starter,
  where ``⊗`` is the quotient ratio.

Neither is a true metric *as originally written*: ``cf_length`` of ``0:1`` is 1 and
``cf_length`` of ``1:1`` is 1, so both give a self-"distance" of 1, not 0. Since a
medoid is an ``argmin`` of a sum, a constant offset is irrelevant to the selected
point — but it matters for the metric axioms. We therefore expose **normalized**
metrics (self-distance 0) as the public API, keep the raw ``cf_length`` available,
and pin the raw self-value with a regression test so the wart can never silently
return.

``tension_additive`` is the default; which metric maximizes medoid-vs-emission
alignment on real data is itself an open empirical question for the investigation.
"""

from __future__ import annotations

from typing import Callable, Iterable

from .ratio import Ratio

RatioMetric = Callable[[Ratio, Ratio], int]


# Tension assigned when comparing against the infinity anchor (1:0). Large but finite
# so medoid selection never crashes and never prefers a filament tip.
_INFINITE_TENSION = 1_000_000


def tension_additive(x: Ratio, y: Ratio) -> int:
    """Normalized additive tension: ``cf_length(|x - y|)`` with ``d(x, x) = 0``."""
    if x == y:
        return 0
    if x.is_infinite() or y.is_infinite():
        return _INFINITE_TENSION
    return (x - y).__abs__().cf_length()


def tension_multiplicative(x: Ratio, y: Ratio) -> int:
    """Normalized multiplicative tension: ``cf_length(x ⊗ y)`` with ``d(x, x) = 0``."""
    if x == y:
        return 0
    if x.is_infinite() or y.is_infinite():
        return _INFINITE_TENSION
    return x.compose(y).cf_length()


DEFAULT_METRIC: RatioMetric = tension_additive


def axiom_report(metric: RatioMetric, samples: Iterable[Ratio]) -> dict:
    """Probe metric axioms on a finite sample set.

    Returns a dict of booleans for identity, symmetry, non-negativity, and a
    (probabilistic) triangle-inequality check over triples drawn from ``samples``.
    """
    pts = list(samples)
    identity = all(metric(a, a) == 0 for a in pts)
    symmetry = all(metric(a, b) == metric(b, a) for a in pts for b in pts)
    non_negative = all(metric(a, b) >= 0 for a in pts for b in pts)
    triangle = True
    for a in pts:
        for b in pts:
            for c in pts:
                if metric(a, c) > metric(a, b) + metric(b, c):
                    triangle = False
                    break
            if not triangle:
                break
        if not triangle:
            break
    return {
        "identity": identity,
        "symmetry": symmetry,
        "non_negative": non_negative,
        "triangle": triangle,
        "n_samples": len(pts),
    }
