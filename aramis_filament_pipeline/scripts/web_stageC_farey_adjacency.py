#!/usr/bin/env python3
"""Stage C — does the web walk the Stern-Brocot tree? (Farey-neighbor axiom |ad-bc|=1)

Along each observed filament we form the sequence of luminosity-ratio relations between
spine-adjacent galaxies, encode each as an exact low-depth ratio (its continued-fraction
convergent), and ask whether *consecutive* relations are Farey neighbors
(|p_k q_{k+1} - p_{k+1} q_k| = 1) — i.e. whether the relation sequence advances by single
mediant steps. We compare the REAL spine ordering to the shuffled-order null at several
encoding depths.

CONFIRM: real ordering yields more Farey-adjacent steps (det==1, det<=3) than shuffled —
the web advances by mediant steps on the Stern-Brocot tree. REFUTE: real ~ shuffled.

Data: data/tempel_bisous/cat_table_a3.txt (gitignored).
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from aramis.web.farey_adjacency import farey_determinant
from aramis.web.graph import ordered_filaments
from aramis.web.nulls_native import shuffle_within
from aramis.web.relations import encode_ratio

A3_COLS = ["id", "nrich", "redshift", "ra", "dec", "distcor", "mag_u", "mag_g",
           "mag_r", "mag_i", "mag_z", "lumr", "w", "edgedist", "fil_dist",
           "fil_id", "fil_idpts"]


def _relation_ratios(lum: np.ndarray, depth: int):
    out = []
    for a, b in zip(lum[:-1], lum[1:]):
        if a > 0 and b > 0:
            out.append(encode_ratio(a / b if a >= b else b / a, depth))
    return out


def _dets(ratios):
    return [farey_determinant(ratios[k], ratios[k + 1]) for k in range(len(ratios) - 1)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default="data/tempel_bisous/cat_table_a3.txt")
    ap.add_argument("--min-len", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    import pandas as pd
    a3 = pd.read_csv(args.path, sep=r"\s+", comment="#", header=None, names=A3_COLS)
    fils = ordered_filaments(a3["fil_id"].values, a3["fil_idpts"].values,
                             {"lum": a3["lumr"].values}, min_len=args.min_len)
    rng = np.random.default_rng(args.seed)

    print(f"filaments: {len(fils)}")
    print(f"{'depth':>5} | {'real det=1':>11} {'shuf det=1':>11} | "
          f"{'real det<=3':>12} {'shuf det<=3':>12}")
    for depth in (16, 32, 64):
        real_d, null_d = [], []
        for f in fils:
            lum = f["lum"]
            real_d.extend(_dets(_relation_ratios(lum, depth)))
            null_d.extend(_dets(_relation_ratios(shuffle_within(lum, rng), depth)))
        real_d, null_d = np.array(real_d), np.array(null_d)
        if real_d.size == 0:
            continue
        print(f"{depth:>5} | {(real_d==1).mean():>11.4f} {(null_d==1).mean():>11.4f} | "
              f"{(real_d<=3).mean():>12.4f} {(null_d<=3).mean():>12.4f}")
    print("\nCONFIRM if real > shuffled (web advances by mediant steps); "
          "REFUTE if real ~ shuffled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
