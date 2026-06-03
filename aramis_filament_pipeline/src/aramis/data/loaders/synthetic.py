"""Synthetic filament generator — the zero-data Stage-0 enabler.

Each synthetic filament plants a *known* true center ``t*`` along its axis, biased
toward a low-depth Farey node determined by the endpoint mass ratio rather than the
Euclidean midpoint (0.5). Emission samples are drawn as a peak around ``t*``.

This lets the full pipeline (and the null-test battery) run end-to-end with no
network or astronomy dependencies, and lets the test suite assert that the Farey
medoid *recovers the planted signal* better than the Euclidean midpoint — proving
the machinery is correct before any real data is introduced.
"""

from __future__ import annotations

from typing import List

import numpy as np

from ..schema import Endpoint, Filament, Sample


def _planted_center(m1: float, m2: float) -> float:
    """A planted true center biased by mass asymmetry toward a Farey node.

    Symmetric pairs plant at 1/2; skewed pairs plant toward the heavier endpoint,
    landing near the depth-2 thirds (1/3, 2/3) the framework predicts.
    """
    total = m1 + m2
    if total <= 0:
        return 0.5
    # Center of mass fraction from endpoint 1, nudged toward the nearest simple node.
    com = m2 / total
    # Quantize toward thirds/halves to emulate a discrete (Farey) attractor.
    nodes = np.array([1 / 3, 1 / 2, 2 / 3, 1 / 4, 3 / 4])
    return float(nodes[np.argmin(np.abs(nodes - com))])


def make_synthetic(
    n: int = 60,
    seed: int = 0,
    n_samples: int = 25,
    peak_sigma: float = 0.06,
    mass_ratio_max: float = 8.0,
    symmetric: bool = False,
) -> List[Filament]:
    """Generate ``n`` synthetic filaments with planted Farey-node centers.

    Parameters
    ----------
    symmetric : if True, force equal masses (planted center 0.5) — the control case
        where every measurement system should agree.
    """
    rng = np.random.default_rng(seed)
    filaments: List[Filament] = []
    for i in range(n):
        if symmetric:
            m1 = m2 = 1.0
        else:
            m1 = 1.0
            m2 = float(rng.uniform(1.0, mass_ratio_max))
            if rng.random() < 0.5:
                m1, m2 = m2, m1
        t_star = _planted_center(m1, m2)

        # Sky geometry is incidental at Stage 0; keep it plausible.
        ra1 = float(rng.uniform(0, 360))
        dec1 = float(rng.uniform(-60, 60))
        ra2 = ra1 + float(rng.uniform(0.5, 3.0))
        dec2 = dec1 + float(rng.uniform(-1.0, 1.0))
        z = float(rng.uniform(0.05, 0.5))

        ep1 = Endpoint(id=f"{i}_a", ra=ra1, dec=dec1, z=z, mass_proxy=m1)
        ep2 = Endpoint(id=f"{i}_b", ra=ra2, dec=dec2, z=z, mass_proxy=m2)

        positions = np.clip(rng.normal(t_star, peak_sigma, size=n_samples), 0.01, 0.99)
        intensities = np.exp(-0.5 * ((positions - t_star) / peak_sigma) ** 2) + 0.05
        samples = [
            Sample(s=float(p), intensity=float(w))
            for p, w in zip(positions, intensities)
        ]

        filaments.append(
            Filament(
                id=f"syn_{i}",
                ep1=ep1,
                ep2=ep2,
                samples=samples,
                meta={"planted_center": t_star, "synthetic": True},
            )
        )
    return filaments
