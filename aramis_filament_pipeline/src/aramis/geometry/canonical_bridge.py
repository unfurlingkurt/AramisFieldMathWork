"""Consistency bridge to the repository's pre-existing canonical ``Rational``.

The native :class:`~aramis.geometry.ratio.Ratio` must not silently diverge from the
``Rational`` already used by the verified φ-equation work in
``phi_domain_analysis/core/discrete_sb_simulator.py``. This module loads that class
by file path (it lives in a non-package script directory and pulls in matplotlib),
and provides converters + assertions so a test can confirm the two agree on the
shared operations — ``mediant`` and the continued fraction.

Nothing here is on the science path. If the canonical module cannot be imported
(e.g. matplotlib absent), :class:`CanonicalUnavailable` is raised and the bridge
tests skip rather than fail — keeping Stage 0 dependency-clean.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .ratio import Ratio


class CanonicalUnavailable(RuntimeError):
    """Raised when the canonical ``Rational`` module cannot be imported."""


def _find_canonical_path() -> Path:
    """Walk up from this file to locate the canonical simulator module."""
    rel = Path("phi_domain_analysis") / "core" / "discrete_sb_simulator.py"
    for parent in Path(__file__).resolve().parents:
        candidate = parent / rel
        if candidate.exists():
            return candidate
    raise CanonicalUnavailable(f"Could not locate {rel} above {__file__}.")


def load_canonical_rational() -> Any:
    """Import and return the canonical ``Rational`` class, or raise CanonicalUnavailable."""
    try:
        path = _find_canonical_path()
        spec = importlib.util.spec_from_file_location("_aramis_canonical_sb", path)
        if spec is None or spec.loader is None:
            raise CanonicalUnavailable("Could not build import spec for canonical module.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Rational
    except CanonicalUnavailable:
        raise
    except Exception as exc:  # missing matplotlib/numpy, syntax drift, etc.
        raise CanonicalUnavailable(str(exc)) from exc


def to_canonical(r: Ratio, Rational: Any) -> Any:
    """Convert a native ``Ratio`` to a canonical ``Rational`` (finite only)."""
    if r.is_infinite():
        raise ValueError("Canonical Rational has no infinity anchor.")
    return Rational(r.p, r.q)


def assert_mediant_agrees(a: Ratio, b: Ratio, Rational: Any) -> None:
    native = a.mediant(b)
    canon = Rational.mediant(Rational(a.p, a.q), Rational(b.p, b.q))
    assert (native.p, native.q) == (canon.num, canon.den), (
        f"mediant disagreement: native {native} vs canonical {canon.num}/{canon.den}"
    )


def assert_cf_agrees(r: Ratio, Rational: Any) -> None:
    native = list(r.cf())
    canon = Rational(r.p, r.q).to_continued_fraction()
    assert native == canon, f"CF disagreement for {r}: {native} vs {canon}"
