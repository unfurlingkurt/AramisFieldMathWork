#!/usr/bin/env python3
"""Real-data check: do Tempel/Bisous luminosity-balance fractions cluster at Farey nodes?

Loads dr8_filaments.fits, computes the endpoint luminosity-balance fraction
lum2/(lum1+lum2) for every filament, and tests whether those fractions sit closer to
low-depth Farey nodes than a *matched smooth null* (a KDE resample of the same
marginal). Crucially it repeats the test EXCLUDING the spike at fraction 0.5, because
~32% of filaments have lum1==lum2 exactly and 1/2 is itself the lowest Farey node — a
confound that fakes clustering.

Honest result on the real catalogue (2026-06): the apparent clustering is entirely
the 0.5 pile-up; excluding it the signal is not significant (|z| < 2). The mass-only
test does not support the medoid hypothesis — the real test needs emission geometry
(Stage 2).

Usage:
    python scripts/analyze_stage1_farey.py data/tempel_bisous/dr8_filaments.fits
"""

from __future__ import annotations

import sys

import numpy as np

from aramis.data.loaders.tempel_bisous import load_dr8_fits
from aramis.geometry.corridor import axis_corridor


def _nearest_node_dist(x: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    return np.min(np.abs(x[:, None] - nodes[None, :]), axis=1)


def _null_z(frac: np.ndarray, nodes: np.ndarray, n: int = 200, seed: int = 0) -> float:
    from scipy.stats import gaussian_kde

    rng = np.random.default_rng(seed)
    kde = gaussian_kde(frac)
    lo = max(0.5, float(frac.min()))
    means = []
    for _ in range(n):
        s = np.clip(kde.resample(frac.size, seed=int(rng.integers(1 << 31)))[0], lo, 0.999)
        means.append(_nearest_node_dist(s, nodes).mean())
    means = np.array(means)
    return (_nearest_node_dist(frac, nodes).mean() - means.mean()) / means.std()


def main(argv=None) -> int:
    path = (argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else \
        "data/tempel_bisous/dr8_filaments.fits"
    fils = load_dr8_fits(path)
    frac = np.array([f.mass2 / (f.mass1 + f.mass2) for f in fils])
    nodes = np.array(sorted(r.axis_fraction() for r in axis_corridor(depth=6)))

    print(f"N filaments: {frac.size}")
    print(f"exactly 0.5 (lum1==lum2): {np.sum(frac == 0.5)} "
          f"({100 * np.mean(frac == 0.5):.1f}%)")
    print(f"all fractions  : z vs smooth null = {_null_z(frac, nodes):+.2f}")
    mask = np.abs(frac - 0.5) > 0.05
    print(f"excluding ~0.5 : z vs smooth null = {_null_z(frac[mask], nodes):+.2f} "
          f"(N={mask.sum()})")
    print("\nInterpretation: significance survives ONLY with the 0.5 pile-up included;"
          " it is a catalogue artifact, not Farey clustering of luminosity ratios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
