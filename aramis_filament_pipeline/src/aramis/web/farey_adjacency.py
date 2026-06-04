"""Farey adjacency — the framework's own ``|ad - bc| = 1`` neighbor relation.

Two reduced ratios p1:q1 and p2:q2 are Stern-Brocot (Farey) neighbors iff their
determinant |p1*q2 - p2*q1| = 1 — i.e. one is reachable from the other by a single
mediant step. This is the native test of whether a sequence of relations *walks the
tree* (adjacent steps) rather than jumping around it.
"""

from __future__ import annotations

from ..geometry.ratio import Ratio


def farey_determinant(r1: Ratio, r2: Ratio) -> int:
    """``|p1*q2 - p2*q1|`` — 1 iff the two ratios are Farey neighbors."""
    return abs(r1.p * r2.q - r2.p * r1.q)


def are_farey_neighbors(r1: Ratio, r2: Ratio) -> bool:
    return farey_determinant(r1, r2) == 1
