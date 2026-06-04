#!/usr/bin/env python3
"""Native test: do galaxy positions along Tempel filaments lock onto low-tension
Farey depths (high φ-coherence), or do they look like generic reals (Gauss–Kuzmin)?

Method (all native; no Euclidean distance metric, no Σ-tension, no means/z-scores):
  - group member galaxies by fil_id (cat_table_a3.txt);
  - for each filament with >= min_gal galaxies, define the axis as the principal
    direction of its member galaxies and project them to a position t in [0,1]
    (projection is unavoidable to place a 3D galaxy on the 1D filament — it is NOT
    used as a distance);
  - take the continued fraction of each t (its Stern-Brocot address) and pool the
    partial quotients;
  - φ-coherence = density of small quotients (a_i <= 2); the framework predicts an
    excess over the matched uniform control AND a deficit of high quotients (a_i>10,
    the 'high-tension walls').

The honest baseline is the *uniform-random control* under the same finite CF
truncation, not the asymptotic Gauss–Kuzmin value (which finite truncation biases).

Data: data/tempel_bisous/cat_table_a3.txt (from dr8_filaments.zip; gitignored).
"""

from __future__ import annotations

import argparse
import collections
import sys

import numpy as np

from aramis.geometry.native import GAUSS_KUZMIN_LE2, continued_fraction_of_float

A3_COLS = ["id", "nrich", "redshift", "ra", "dec", "distcor", "mag_u", "mag_g",
           "mag_r", "mag_i", "mag_z", "lumr", "w", "edgedist", "fil_dist",
           "fil_id", "fil_idpts"]


def _pool_quotients(t_values: np.ndarray, n_terms: int) -> np.ndarray:
    qs = []
    for t in t_values:
        if 0.0 < t < 1.0:
            qs.extend(continued_fraction_of_float(float(t), n_terms)[1:])  # drop a0
    return np.asarray(qs)


def filament_positions(a3, min_gal: int) -> np.ndarray:
    ra = np.radians(a3["ra"].values)
    dec = np.radians(a3["dec"].values)
    d = a3["distcor"].values
    xyz = np.column_stack([d * np.cos(dec) * np.cos(ra),
                           d * np.cos(dec) * np.sin(ra),
                           d * np.sin(dec)])
    groups = collections.defaultdict(list)
    for i, f in enumerate(a3["fil_id"].values):
        if f > 0:
            groups[f].append(i)
    t_all = []
    for idx in groups.values():
        if len(idx) < min_gal:
            continue
        c = xyz[idx] - xyz[idx].mean(0)
        _, vec = np.linalg.eigh(c.T @ c)
        proj = c @ vec[:, -1]
        lo, hi = proj.min(), proj.max()
        if hi - lo < 1e-9:
            continue
        t_all.extend(((proj - lo) / (hi - lo)).tolist())
    return np.asarray(t_all)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default="data/tempel_bisous/cat_table_a3.txt")
    ap.add_argument("--min-gal", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    import pandas as pd
    a3 = pd.read_csv(args.path, sep=r"\s+", comment="#", header=None, names=A3_COLS)
    t_obs = filament_positions(a3, args.min_gal)
    t_unif = np.random.default_rng(args.seed).random(t_obs.size)

    print(f"galaxies projected: {t_obs.size}")
    print(f"asymptotic Gauss-Kuzmin P(a<=2) = {GAUSS_KUZMIN_LE2:.4f} (finite-term biased)")
    print(f"{'terms':>5} | {'obs a<=2':>9} {'unif a<=2':>9} | {'obs a>10':>9} {'unif a>10':>9}")
    for n in (4, 6, 10):
        qo, qu = _pool_quotients(t_obs, n), _pool_quotients(t_unif, n)
        print(f"{n:>5} | {(qo<=2).mean():>9.4f} {(qu<=2).mean():>9.4f} | "
              f"{(qo>10).mean():>9.4f} {(qu>10).mean():>9.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
