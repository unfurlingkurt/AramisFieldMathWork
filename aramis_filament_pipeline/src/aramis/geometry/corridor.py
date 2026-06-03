"""Mediant corridors and the Farey medoid.

A corridor is the finite set of Stern-Brocot mediants generated between two endpoint
ratios. It is the native search space (the "spine") on which a filament's central
object is located. The Farey medoid is the corridor member minimizing total tension
to the observed samples — a medoid, not a centroid.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Tuple

from .metric import DEFAULT_METRIC, RatioMetric
from .ratio import Ratio


def corridor_candidates(a: Ratio, b: Ratio, depth: int = 8) -> List[Ratio]:
    """Recursive mediant insertion between endpoint ratios ``a`` and ``b``.

    This is NOT linear interpolation; at each level a mediant is inserted between
    every adjacent pair. Returns ordered, de-duplicated candidates.
    """
    current: List[Ratio] = [a, b]
    for _ in range(depth):
        nxt: List[Ratio] = []
        for left, right in zip(current[:-1], current[1:]):
            nxt.append(left)
            nxt.append(left.mediant(right))
        nxt.append(current[-1])
        current = nxt

    seen = set()
    out: List[Ratio] = []
    for r in current:
        if r not in seen:
            out.append(r)
            seen.add(r)
    return out


@lru_cache(maxsize=None)
def _axis_corridor_cached(depth: int) -> Tuple[Ratio, ...]:
    full = corridor_candidates(Ratio(0, 1), Ratio(1, 0), depth=depth)
    return tuple(full[1:-1])


def axis_corridor(depth: int = 8) -> List[Ratio]:
    """The native axis corridor: Stern-Brocot rationals spanning a filament axis.

    Built between the seeds ``0:1`` (one endpoint) and ``1:0`` (the other). Member
    ``p:q`` sits at axis fraction ``p/(p+q)``; depth-2 already yields the 1/3, 1/2,
    2/3 thirds structure noted in ``RATIOSPACE_FINDINGS_SUMMARY.md``. The two seed
    endpoints (axis fractions 0 and 1, the filament tips) are excluded — a central
    object lives strictly between them. Cached, since the axis corridor depends only
    on ``depth`` and is queried once per measurement.
    """
    return list(_axis_corridor_cached(depth))


def farey_medoid(
    candidates: Iterable[Ratio],
    samples: Sequence[Ratio],
    weights: Optional[Sequence[float]] = None,
    metric: RatioMetric = DEFAULT_METRIC,
) -> Tuple[Ratio, float]:
    """Select the candidate minimizing total (optionally weighted) tension to samples.

    Returns ``(medoid, score)``. Ties break toward lower CF-length then smaller
    ``p + q`` (the simplest native address).
    """
    cand_list = list(candidates)
    if not cand_list:
        raise ValueError("No candidates supplied.")
    if not samples:
        raise ValueError("No samples supplied.")
    if weights is None:
        weights = [1.0] * len(samples)
    if len(weights) != len(samples):
        raise ValueError("weights and samples must have equal length.")

    def score(r: Ratio) -> float:
        return float(sum(w * metric(r, s) for s, w in zip(samples, weights)))

    best = min(cand_list, key=lambda r: (score(r), r.cf_length(), r.p + r.q))
    return best, score(best)
