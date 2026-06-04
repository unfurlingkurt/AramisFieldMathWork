#!/usr/bin/env python3
"""Stage B — luminosity ratios between web-adjacent galaxies (Q1, what binds the web).

For spine-adjacent galaxies the native relation is the luminosity ratio L_i:L_j
(oriented >= 1; scale-free; real range ~1-7). We test whether the φ-coherence of
these relations for REAL adjacency exceeds the shuffled-order null (and the
Gauss–Kuzmin neighborhood). A positive result would say the web preferentially
connects galaxies in simple luminosity-ratio relationships.

Data: data/tempel_bisous/cat_table_a3.txt (gitignored).
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from aramis.geometry.native import GAUSS_KUZMIN_LE2
from aramis.web.graph import ordered_filaments
from aramis.web.nulls_native import shuffle_within
from aramis.web.relations import (
    high_tension_fraction,
    pairwise_ratios,
    phi_coherence_of_floats,
)

A3_COLS = ["id", "nrich", "redshift", "ra", "dec", "distcor", "mag_u", "mag_g",
           "mag_r", "mag_i", "mag_z", "lumr", "w", "edgedist", "fil_dist",
           "fil_id", "fil_idpts"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default="data/tempel_bisous/cat_table_a3.txt")
    ap.add_argument("--min-len", type=int, default=10)
    ap.add_argument("--n-terms", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    import pandas as pd
    a3 = pd.read_csv(args.path, sep=r"\s+", comment="#", header=None, names=A3_COLS)
    fils = ordered_filaments(
        a3["fil_id"].values, a3["fil_idpts"].values,
        {"lum": a3["lumr"].values}, min_len=args.min_len,
    )
    rng = np.random.default_rng(args.seed)

    real_rel, null_rel = [], []
    for f in fils:
        lum = f["lum"]
        real_rel.extend(pairwise_ratios(lum[:-1], lum[1:]))
        s = shuffle_within(lum, rng)
        null_rel.extend(pairwise_ratios(s[:-1], s[1:]))

    real_phi, nq = phi_coherence_of_floats(real_rel, args.n_terms)
    null_phi, _ = phi_coherence_of_floats(null_rel, args.n_terms)
    print(f"filaments: {len(fils)}   relations (real): {len(real_rel)}   quotients: {nq}")
    print(f"Gauss-Kuzmin P(a<=2) (asymptotic): {GAUSS_KUZMIN_LE2:.4f}")
    print(f"phi-coherence  real adjacency : {real_phi:.4f}")
    print(f"phi-coherence  shuffled null  : {null_phi:.4f}")
    print(f"high-tension (a>10)  real     : {high_tension_fraction(real_rel, args.n_terms):.4f}")
    print(f"high-tension (a>10)  shuffled : {high_tension_fraction(null_rel, args.n_terms):.4f}")
    delta = real_phi - null_phi
    verdict = ("CONFIRM (real > shuffled)" if delta > 0.003
               else "REFUTE / non-detection (real ~ shuffled)")
    print(f"\nΔφ (real - shuffled) = {delta:+.4f}   => {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
