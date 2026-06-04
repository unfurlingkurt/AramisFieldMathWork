"""The observed web graph.

Nodes are galaxies; edges are the catalogue's own connectivity — membership in a
filament (``fil_id``) and ordering along the spine (``fil_idpts``). No edge is ever
created from a Euclidean distance we compute.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np


def ordered_filaments(
    fil_id: Sequence[int],
    fil_idpts: Sequence[int],
    values: Dict[str, np.ndarray],
    min_len: int = 10,
) -> List[Dict[str, np.ndarray]]:
    """Group galaxies by filament and order each along the spine by ``fil_idpts``.

    Returns, per filament with at least ``min_len`` members, a dict mapping each name
    in ``values`` to the ordered array for that filament. The ordering is the
    observed spine sequence — not a Euclidean projection.
    """
    fil_id = np.asarray(fil_id)
    fil_idpts = np.asarray(fil_idpts)
    groups: Dict[int, List[int]] = {}
    for i, f in enumerate(fil_id):
        if f > 0:
            groups.setdefault(int(f), []).append(i)

    out: List[Dict[str, np.ndarray]] = []
    for idx in groups.values():
        if len(idx) < min_len:
            continue
        idx = np.array(idx)
        order = idx[np.argsort(fil_idpts[idx], kind="stable")]
        out.append({name: arr[order] for name, arr in values.items()})
    return out
