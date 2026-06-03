"""Turn a raw intensity profile into clean, positive emission weights.

Map values can be negative (background-subtracted maps) or carry a baseline. The
Farey medoid weights samples by intensity, so weights must be non-negative. This
module subtracts a background estimate and floors at zero, leaving the emission
*excess* along the axis as the weight.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from ..data.schema import Sample


def clean_profile(
    samples: Sequence[Sample],
    background: str = "median",
    floor: float = 0.0,
) -> List[Sample]:
    """Background-subtract and floor sample intensities to non-negative weights."""
    if not samples:
        return []
    vals = np.array([s.intensity for s in samples], dtype=float)
    finite = vals[np.isfinite(vals)]
    if finite.size == 0:
        base = 0.0
    elif background == "median":
        base = float(np.median(finite))
    elif background == "min":
        base = float(np.min(finite))
    else:
        base = 0.0
    out: List[Sample] = []
    for s in samples:
        w = s.intensity - base
        if not np.isfinite(w):
            w = floor
        out.append(Sample(s=s.s, intensity=max(floor, w), ra=s.ra, dec=s.dec))
    return out


def has_signal(samples: Sequence[Sample], min_total: float = 0.0) -> bool:
    """True if cleaned samples carry positive total weight (usable for a medoid)."""
    return sum(s.intensity for s in samples) > min_total
