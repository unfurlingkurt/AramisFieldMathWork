#!/usr/bin/env python3
"""
Ratio-Space Core Utilities — Crystallization Anchor Framework

At Farey depth 12, the RatioSpace graph undergoes a topological phase
transition: it becomes a Triple Torus (genus 3). This creates exactly
three independent self-referential loops — three crystallization anchors:

    Octave  (1:2) — Loop via divisor 6  (6:12 → 1:2)
    Fifth   (2:3) — Loop via divisor 4  (8:12 → 2:3)
    Fourth  (3:4) — Loop via divisor 3  (9:12 → 3:4)

These are NOT arbitrary boundaries. They are geometrically forced by the
triple torus topology. The spectral gap at depth 12 creates the first
stable crystallization platform.

MEASUREMENT: All distances are CF tension (hyperbolic), computed as the
length of the continued fraction of the COMPOSITION of Z with the
inverse of the anchor:

    tension_to_anchor(Z, p/q) = len(CF(Z · q/p))

When Z = p/q exactly: composition = 1, CF(1) = [1], tension = 1 (minimum).

Classification: nearest anchor by minimum CF tension. The three basins
of attraction correspond to the three independent loops of the triple torus.
"""

import numpy as np
from typing import List, Tuple, Dict

PHI = (1 + np.sqrt(5)) / 2

# ============================================================
# Crystallization Anchors — Depth 12 Triple Torus
# ============================================================

ANCHORS = {
    'octave': (1, 2),   # 1:2 — Loop via divisor 6 (6:12 → 1:2)
    'fifth':  (2, 3),   # 2:3 — Loop via divisor 4 (8:12 → 2:3)
    'fourth': (3, 4),   # 3:4 — Loop via divisor 3 (9:12 → 3:4)
}

ANCHOR_VALUES = {name: num / den for name, (num, den) in ANCHORS.items()}

CRYSTALLIZATION_DEPTH = 12


# ============================================================
# Continued Fraction Primitives
# ============================================================

def continued_fraction(x, max_terms=20, large_quotient_cutoff=1000):
    """
    Compute continued fraction expansion of a positive real number.

    x = a_0 + 1/(a_1 + 1/(a_2 + ...))

    Returns list [a_0, a_1, a_2, ...].
    Length = Farey depth = hyperbolic distance from origin.

    A partial quotient > large_quotient_cutoff signals that x is very
    close to the rational convergent at that point. Subsequent terms
    are floating point noise, not geometric signal. We include the
    large quotient and stop.
    """
    if x < 0:
        return continued_fraction(-x, max_terms, large_quotient_cutoff)
    cf = []
    for _ in range(max_terms):
        a = int(np.floor(x))
        cf.append(a)
        # Large quotient = "almost rational" — stop after including it
        if a > large_quotient_cutoff and len(cf) > 1:
            break
        frac = x - a
        if frac < 1e-10:
            break
        x = 1.0 / frac
        if x > 1e12:
            break
    return cf


def cf_to_value(cf):
    """Reconstruct value from continued fraction."""
    if not cf:
        return 0.0
    val = float(cf[-1])
    for a in reversed(cf[:-1]):
        if val == 0:
            return float('inf')
        val = a + 1.0 / val
    return val


def farey_depth(x, max_depth=20):
    """
    Farey depth = length of continued fraction.

    = number of mediant operations to reach x from seeds 0/1, 1/0.
    """
    if x <= 0 or not np.isfinite(x):
        return 0
    return len(continued_fraction(x, max_terms=max_depth))


# ============================================================
# Tension — Hyperbolic Distance via CF
# ============================================================

def tension(x, y, max_terms=20):
    """
    Tension (hyperbolic distance) between two ratios.

    Tension = Farey depth of their ratio.
    Short CF = close in hyperbolic space = low tension.
    Long CF = far in hyperbolic space = high tension.
    """
    if x <= 0 or y <= 0 or not np.isfinite(x) or not np.isfinite(y):
        return max_terms
    ratio = x / y if y > x else y / x
    if ratio < 1e-10:
        return max_terms
    return farey_depth(ratio, max_depth=max_terms)


def tension_to_anchor(Z, anchor_num, anchor_den, max_terms=20):
    """
    CF tension from Z to a crystallization anchor p/q.

    Computed as: len(CF(Z * q/p))

    This is the composition of Z with the inverse of the anchor.
    When Z = p/q exactly:
        composition = (p/q) * (q/p) = 1
        CF(1) = [1], tension = 1 (minimum)

    Higher tension = further from anchor in hyperbolic space.
    """
    if Z <= 0 or not np.isfinite(Z):
        return max_terms
    if anchor_num <= 0:
        return max_terms

    comp = Z * anchor_den / anchor_num
    if comp <= 0 or not np.isfinite(comp):
        return max_terms

    return len(continued_fraction(comp, max_terms))


# ============================================================
# Anchor Classification — Triple Torus Basins
# ============================================================

def classify_by_anchor(Z, max_terms=20):
    """
    Classify Z by nearest crystallization anchor (minimum CF tension).

    Returns (anchor_name_or_'transitional', tensions_dict).

    If all three anchors have the same tension, the value is
    'transitional' — equidistant from all anchors, not crystallized
    at any loop of the triple torus.

    The three basins of attraction correspond to the three independent
    loops of the depth-12 triple torus:
        octave (1:2) — temporal dominance
        fifth  (2:3) — balanced/propagating
        fourth (3:4) — spatial dominance
    """
    if Z <= 0 or not np.isfinite(Z):
        return 'transitional', {n: max_terms for n in ANCHORS}

    tensions = {}
    for name, (num, den) in ANCHORS.items():
        tensions[name] = tension_to_anchor(Z, num, den, max_terms)

    t_vals = sorted(tensions.values())
    # Crystallized: minimum tension is strictly less than the next
    if t_vals[0] < t_vals[1]:
        nearest = min(tensions, key=tensions.get)
        return nearest, tensions
    else:
        # All anchors tied — transitional (pre-crystallized)
        return 'transitional', tensions


def classify_array_by_anchor(Z_array, max_terms=20, n_samples=5000):
    """
    Classify an array of impedance values by nearest crystallization anchor.

    Separates crystallized values (one anchor clearly closest) from
    transitional values (equidistant from all anchors).

    Returns dict with fractions in each basin + transitional fraction.
    """
    Z_flat = np.asarray(Z_array).flatten()
    Z_flat = Z_flat[np.isfinite(Z_flat) & (Z_flat > 0)]

    if len(Z_flat) == 0:
        return {
            'octave': 0, 'fifth': 0, 'fourth': 0,
            'transitional': 0, 'total': 0, 'mean_tensions': {},
        }

    # Sample if too large
    if len(Z_flat) > n_samples:
        rng = np.random.default_rng(0)
        Z_sample = rng.choice(Z_flat, n_samples, replace=False)
    else:
        Z_sample = Z_flat

    counts = {'octave': 0, 'fifth': 0, 'fourth': 0, 'transitional': 0}
    tension_sums = {'octave': 0.0, 'fifth': 0.0, 'fourth': 0.0}
    tension_counts = {'octave': 0, 'fifth': 0, 'fourth': 0}

    for z in Z_sample:
        nearest, tensions = classify_by_anchor(z, max_terms)
        counts[nearest] += 1
        for name, t in tensions.items():
            if name in tension_sums:
                tension_sums[name] += t
                tension_counts[name] += 1

    n = len(Z_sample)
    mean_tensions = {}
    for name in ANCHORS:
        if tension_counts[name] > 0:
            mean_tensions[name] = tension_sums[name] / tension_counts[name]
        else:
            mean_tensions[name] = max_terms

    n_crystallized = counts['octave'] + counts['fifth'] + counts['fourth']
    crystallized_frac = n_crystallized / n if n > 0 else 0

    return {
        'octave': counts['octave'] / n,
        'fifth': counts['fifth'] / n,
        'fourth': counts['fourth'] / n,
        'transitional': counts['transitional'] / n,
        'total': n,
        'crystallized_fraction': crystallized_frac,
        'mean_tensions': mean_tensions,
        'anchors': {n: f'{num}/{den}' for n, (num, den) in ANCHORS.items()},
        'note': 'Depth-12 triple torus crystallization anchors',
    }


def anchor_tension_profile(Z_array, max_terms=20, n_samples=3000):
    """
    Compute full tension profile to each anchor for an array of Z values.

    Returns per-anchor arrays of tensions for distribution analysis.
    """
    Z_flat = np.asarray(Z_array).flatten()
    Z_flat = Z_flat[np.isfinite(Z_flat) & (Z_flat > 0)]

    if len(Z_flat) > n_samples:
        rng = np.random.default_rng(0)
        Z_flat = rng.choice(Z_flat, n_samples, replace=False)

    profiles = {name: [] for name in ANCHORS}

    for z in Z_flat:
        for name, (num, den) in ANCHORS.items():
            t = tension_to_anchor(z, num, den, max_terms)
            profiles[name].append(t)

    return {name: np.array(vals) for name, vals in profiles.items()}


# ============================================================
# Anchor Clustering Strength
# ============================================================

def anchor_clustering_strength(values, max_terms=20, n_samples=2000):
    """
    Measure how strongly values cluster at the three crystallization anchors.

    Compare observed mean tension-to-nearest-anchor vs random baseline
    drawn from the same range.

    Clustering > 1 means values prefer anchor positions.
    """
    values = np.asarray(values).flatten()
    values = values[np.isfinite(values) & (values > 0) & (values < 50)]

    if len(values) < 10:
        return 1.0, 0.0, 0.0

    if len(values) > n_samples:
        rng0 = np.random.default_rng(0)
        values = rng0.choice(values, n_samples, replace=False)

    v_min = np.min(values)
    v_max = np.max(values)

    def min_anchor_tension(z):
        """Minimum tension to any of the three anchors."""
        return min(
            tension_to_anchor(z, num, den, max_terms)
            for num, den in ANCHORS.values()
        )

    # Observed minimum tensions
    obs_tensions = [min_anchor_tension(v) for v in values]

    # Random baseline: uniform over same range
    rng = np.random.default_rng(42)
    random_vals = rng.uniform(v_min, v_max, len(values))
    rand_tensions = [min_anchor_tension(v) for v in random_vals]

    mean_obs = np.mean(obs_tensions)
    mean_rand = np.mean(rand_tensions)

    # Clustering = ratio of random tension to observed tension
    # > 1 means observed values are closer to anchors than random
    clustering = mean_rand / (mean_obs + 1e-10)

    return clustering, mean_obs, mean_rand


# ============================================================
# Stern-Brocot Tree Utilities
# ============================================================

def nearest_sb_ratio(x, max_depth=10):
    """
    Find nearest Stern-Brocot ratio by navigating the tree.

    Returns (numerator, denominator, depth).
    """
    if x <= 0 or not np.isfinite(x):
        return (0, 1, 0)

    a, b = 0, 1   # Left bound = 0/1
    c, d = 1, 0   # Right bound = 1/0

    best = (1, 1, 1)
    best_dist = abs(x - 1.0)

    for depth in range(1, max_depth + 1):
        m_num = a + c
        m_den = b + d
        if m_den == 0:
            break
        m_val = m_num / m_den

        dist = abs(x - m_val)
        if dist < best_dist:
            best_dist = dist
            best = (m_num, m_den, depth)

        if dist < 1e-10:
            return (m_num, m_den, depth)
        elif x < m_val:
            c, d = m_num, m_den
        else:
            a, b = m_num, m_den

    return best


def generate_sb_ratios(max_depth=8):
    """
    Generate all Stern-Brocot ratios up to given depth.

    Returns list of (value, numerator, denominator, depth).
    """
    ratios = []

    def gen(a, b, c, d, depth):
        if depth > max_depth:
            return
        m_num, m_den = a + c, b + d
        if m_den > 0:
            ratios.append((m_num / m_den, m_num, m_den, depth))
        gen(a, b, m_num, m_den, depth + 1)
        gen(m_num, m_den, c, d, depth + 1)

    gen(0, 1, 1, 0, 1)
    ratios.sort(key=lambda r: r[0])
    return ratios


def sb_clustering_strength(values, max_depth=8, n_samples=2000):
    """
    Measure how strongly values cluster at SB ratios.

    Fair comparison: random baseline uses the SAME range as observed data.
    Clustering > 1 means values prefer SB ratios.
    """
    values = np.asarray(values).flatten()
    values = values[np.isfinite(values) & (values > 0) & (values < 50)]

    if len(values) < 10:
        return 1.0, 0.0, 0.0

    if len(values) > n_samples:
        rng0 = np.random.default_rng(0)
        values = rng0.choice(values, n_samples, replace=False)

    v_min = np.min(values)
    v_max = np.max(values)

    obs_dists = []
    for v in values:
        num, den, depth = nearest_sb_ratio(v, max_depth)
        if den > 0:
            obs_dists.append(abs(v - num / den))

    rng = np.random.default_rng(42)
    random_vals = rng.uniform(v_min, v_max, len(values))
    rand_dists = []
    for v in random_vals:
        num, den, depth = nearest_sb_ratio(v, max_depth)
        if den > 0:
            rand_dists.append(abs(v - num / den))

    mean_obs = np.mean(obs_dists) if obs_dists else 1.0
    mean_rand = np.mean(rand_dists) if rand_dists else 1.0

    return mean_rand / (mean_obs + 1e-10), mean_obs, mean_rand


# ============================================================
# Phi-Harmonic Ratios
# ============================================================

def phi_harmonic_ratios(n=6):
    """
    Generate phi-harmonic ratios: {phi^-n, ..., phi^-1, phi^0, phi^1, ..., phi^n}.

    These are the discrete gear ratios of the system.
    """
    return [PHI**k for k in range(-n, n + 1)]


# ============================================================
# Legacy Compatibility (kept for gradient_geodesic.py)
# ============================================================

def classify_farey(Z):
    """Classify by nearest crystallization anchor (replaces flat Farey)."""
    name, _ = classify_by_anchor(Z)
    return name


def classify_farey_array(Z_array):
    """Classify array by crystallization anchors (replaces flat Farey)."""
    return classify_array_by_anchor(Z_array)
