"""Bootstrap confidence intervals and effect sizes."""

from __future__ import annotations

from typing import Callable, Sequence, Tuple

import numpy as np


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[np.ndarray], float] = np.mean,
    n: int = 10_000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Return ``(low, point, high)`` percentile bootstrap CI for ``statistic``."""
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n, arr.size))
    resamples = arr[idx]
    try:  # vectorized path for axis-aware statistics (e.g. np.mean)
        boot = np.asarray(statistic(resamples, axis=1))
    except TypeError:
        boot = np.array([statistic(row) for row in resamples])
    lo = float(np.quantile(boot, alpha / 2))
    hi = float(np.quantile(boot, 1 - alpha / 2))
    return (lo, float(statistic(arr)), hi)


def cohen_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d effect size between two samples (pooled SD)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.size < 2 or b.size < 2:
        return float("nan")
    na, nb = a.size, b.size
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if sp == 0:
        return 0.0
    return float((a.mean() - b.mean()) / sp)


def permutation_p_value(
    observed: float,
    null_samples: Sequence[float],
    tail: str = "left",
) -> float:
    """p-value of ``observed`` against a null distribution.

    ``tail='left'`` tests whether ``observed`` is unusually small (e.g. an error that
    is lower than expected by chance).
    """
    null = np.asarray(null_samples, dtype=float)
    if null.size == 0:
        return float("nan")
    if tail == "left":
        count = np.sum(null <= observed)
    elif tail == "right":
        count = np.sum(null >= observed)
    else:
        count = np.sum(np.abs(null) >= abs(observed))
    return float((count + 1) / (null.size + 1))
