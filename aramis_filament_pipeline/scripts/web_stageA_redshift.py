#!/usr/bin/env python3
"""Stage A — redshift difference-ratios as native relations.

Within each observed filament, galaxies are ordered along the spine (by fil_idpts,
observed — not Euclidean). The native relation is the ratio of consecutive redshift
differences |Δz_k|/|Δz_{k+1}| (scale-free, local; the peculiar-velocity structure the
linear view 'corrects away'). We compare the φ-coherence of these relations for the
REAL spine ordering against (i) the same redshifts in SHUFFLED order within each
filament (the native rewiring null) and (ii) the Gauss–Kuzmin neighborhood.

CONFIRM: real ordering gives higher φ-coherence (simpler relations) than shuffled.
REFUTE: real ≈ shuffled — the web's ordering carries no extra ratio structure.

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
    consecutive_difference_ratios,
    high_tension_fraction,
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
        {"z": a3["redshift"].values}, min_len=args.min_len,
    )
    rng = np.random.default_rng(args.seed)

    real_rel, null_rel = [], []
    for f in fils:
        real_rel.extend(consecutive_difference_ratios(f["z"]))
        null_rel.extend(consecutive_difference_ratios(shuffle_within(f["z"], rng)))

    real_phi, nq = phi_coherence_of_floats(real_rel, args.n_terms)
    null_phi, _ = phi_coherence_of_floats(null_rel, args.n_terms)
    real_wall = high_tension_fraction(real_rel, args.n_terms)
    null_wall = high_tension_fraction(null_rel, args.n_terms)

    print(f"filaments: {len(fils)}   relations (real): {len(real_rel)}   quotients: {nq}")
    print(f"Gauss-Kuzmin P(a<=2) (asymptotic): {GAUSS_KUZMIN_LE2:.4f}")
    print(f"phi-coherence  real ordering : {real_phi:.4f}")
    print(f"phi-coherence  shuffled null : {null_phi:.4f}")
    print(f"high-tension (a>10)  real    : {real_wall:.4f}")
    print(f"high-tension (a>10)  shuffled: {null_wall:.4f}")
    delta = real_phi - null_phi
    verdict = ("CONFIRM (real > shuffled)" if delta > 0.003
               else "REFUTE / non-detection (real ~ shuffled)")
    print(f"\nΔφ (real - shuffled) = {delta:+.4f}   => {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
