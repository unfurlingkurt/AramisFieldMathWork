"""Null / control transformations and the null-test battery.

The hypothesis is that a filament's emission center aligns with the native Farey
medoid better than with the Euclidean midpoint. A raw difference is not enough — it
must survive controls that break the structure it supposedly exploits:

* **shuffled masses** — permute mass proxies across the population; breaks any
  genuine mass->position link.
* **random sky pairs** — pair endpoints from unrelated filaments.
* **rotated axes** — perturb the sampling axis off the true filament.
* **same-mass controls** — equalize masses; mass-driven estimators must collapse to
  the midpoint, so any residual medoid advantage cannot come from mass asymmetry.

Each null is a pure ``list[Filament] -> list[Filament]`` transform, so the same
battery runs on synthetic or real catalogs.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, Dict, List, Sequence

import numpy as np

from ..data.schema import Endpoint, Filament, Sample
from ..systems.base import MeasurementSystem
from .bootstrap import bootstrap_ci, cohen_d, permutation_p_value

ObservedCenterFn = Callable[[Filament], float]


# ----- observed-center definitions --------------------------------------
def observed_center_planted(fil: Filament) -> float:
    """For synthetic data: the planted true center."""
    return float(fil.meta["planted_center"])


def observed_center_emission(fil: Filament) -> float:
    """Intensity-weighted emission peak along the axis (works on real data)."""
    if not fil.samples:
        return 0.5
    s = np.array([x.s for x in fil.samples])
    w = np.array([x.intensity for x in fil.samples])
    total = w.sum()
    return float(np.sum(s * w) / total) if total > 0 else 0.5


# ----- null transformations ----------------------------------------------
def null_shuffled_masses(filaments: Sequence[Filament], seed: int = 0) -> List[Filament]:
    rng = np.random.default_rng(seed)
    masses = np.array([f.mass1 for f in filaments] + [f.mass2 for f in filaments])
    rng.shuffle(masses)
    out = []
    for i, f in enumerate(filaments):
        m1, m2 = float(masses[2 * i]), float(masses[2 * i + 1])
        out.append(replace(f, ep1=replace(f.ep1, mass_proxy=m1),
                           ep2=replace(f.ep2, mass_proxy=m2)))
    return out


def null_random_sky_pairs(filaments: Sequence[Filament], seed: int = 0) -> List[Filament]:
    rng = np.random.default_rng(seed)
    ep2s = [f.ep2 for f in filaments]
    perm = rng.permutation(len(filaments))
    out = []
    for f, j in zip(filaments, perm):
        out.append(replace(f, ep2=ep2s[j]))
    return out


def null_rotated_axes(filaments: Sequence[Filament], seed: int = 0) -> List[Filament]:
    """Perturb the axis by scrambling sample positions away from the true peak."""
    rng = np.random.default_rng(seed)
    out = []
    for f in filaments:
        new_samples = [
            Sample(s=float(np.clip(rng.uniform(0.05, 0.95), 0, 1)),
                   intensity=x.intensity, ra=x.ra, dec=x.dec)
            for x in f.samples
        ]
        out.append(replace(f, samples=new_samples))
    return out


def null_same_mass_controls(filaments: Sequence[Filament]) -> List[Filament]:
    out = []
    for f in filaments:
        out.append(replace(f, ep1=replace(f.ep1, mass_proxy=1.0),
                           ep2=replace(f.ep2, mass_proxy=1.0)))
    return out


# ----- battery ------------------------------------------------------------
def _errors(filaments, system: MeasurementSystem, observed: ObservedCenterFn,
            spec, metric) -> np.ndarray:
    return np.array([
        abs(system.locate(f, spec=spec, metric=metric).t - observed(f))
        for f in filaments
    ])


def run_null_battery(
    filaments: Sequence[Filament],
    medoid_system: MeasurementSystem,
    baseline_system: MeasurementSystem,
    observed: ObservedCenterFn = observed_center_planted,
    spec=None,
    metric=None,
    n_null: int = 200,
    seed: int = 0,
) -> Dict[str, object]:
    """Compare medoid vs baseline alignment, then re-test under each null.

    Returns the observed improvement (baseline_err - medoid_err) with a bootstrap CI
    and effect size, plus, for each null, the improvement and a permutation p-value
    of the real improvement against the null improvements.
    """
    from ..geometry.metric import DEFAULT_METRIC
    from ..quantize.scale import DEFAULT_MASS_SCALE
    spec = spec or DEFAULT_MASS_SCALE
    metric = metric or DEFAULT_METRIC

    med = _errors(filaments, medoid_system, observed, spec, metric)
    base = _errors(filaments, baseline_system, observed, spec, metric)
    delta = base - med  # positive => medoid is closer to the observed center

    lo, point, hi = bootstrap_ci(delta, seed=seed)
    result: Dict[str, object] = {
        "n": len(filaments),
        "medoid_mean_err": float(med.mean()),
        "baseline_mean_err": float(base.mean()),
        "improvement_mean": float(point),
        "improvement_ci95": [lo, hi],
        "effect_size_d": cohen_d(base, med),
        "nulls": {},
    }

    transforms = {
        "shuffled_masses": null_shuffled_masses,
        "random_sky_pairs": null_random_sky_pairs,
        "rotated_axes": null_rotated_axes,
    }
    rng = np.random.default_rng(seed)
    for name, transform in transforms.items():
        null_improvements = []
        for k in range(n_null):
            nf = transform(filaments, seed=int(rng.integers(0, 2**31)))
            nm = _errors(nf, medoid_system, observed, spec, metric)
            nb = _errors(nf, baseline_system, observed, spec, metric)
            null_improvements.append(float((nb - nm).mean()))
        p = permutation_p_value(point, null_improvements, tail="right")
        result["nulls"][name] = {
            "null_improvement_mean": float(np.mean(null_improvements)),
            "p_value": p,
        }

    # Same-mass control is deterministic (no randomness): one evaluation.
    sm = null_same_mass_controls(filaments)
    sm_med = _errors(sm, medoid_system, observed, spec, metric)
    sm_base = _errors(sm, baseline_system, observed, spec, metric)
    result["nulls"]["same_mass_control"] = {
        "medoid_mean_err": float(sm_med.mean()),
        "baseline_mean_err": float(sm_base.mean()),
        "improvement_mean": float((sm_base - sm_med).mean()),
    }
    return result
