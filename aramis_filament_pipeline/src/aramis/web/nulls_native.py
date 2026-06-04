"""Native nulls: relational rewiring and the Gauss–Kuzmin reference.

The question is whether the *observed* connectivity/ordering is special. The native
null breaks that structure while preserving the node set — by shuffling the order of
nodes within each filament (Stage A/B), or by degree-preserving edge rewiring
(Stage C). It is never a Gaussian.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np


def shuffle_within(sequence: Sequence[float], rng: np.random.Generator) -> np.ndarray:
    """Randomize the order of values within one filament (breaks spine adjacency).

    Preserves the exact multiset of values per filament; destroys only the observed
    ordering — isolating whether the web's ordering carries the structure.
    """
    arr = np.array(sequence, dtype=float)
    perm = rng.permutation(arr.size)
    return arr[perm]
