"""Normalized data schema shared by every loader and downstream module.

Loaders (synthetic, Tempel/Bisous, SDSS LRG, ...) all emit these types, so the
geometry, measurement, and statistics layers are catalog-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Endpoint:
    """A filament endpoint with sky position, redshift, and a mass proxy."""

    id: str
    ra: float        # degrees
    dec: float       # degrees
    z: float         # redshift
    mass_proxy: float


@dataclass(frozen=True)
class Sample:
    """An emission sample along the filament axis.

    ``s`` is the axis fraction in ``[0, 1]`` measured from endpoint 1; ``intensity``
    is the (positive) measured emission used as a weight.
    """

    s: float
    intensity: float
    ra: Optional[float] = None
    dec: Optional[float] = None


@dataclass(frozen=True)
class Filament:
    """A filament / endpoint-pair with optional spine and emission samples."""

    id: str
    ep1: Endpoint
    ep2: Endpoint
    samples: List[Sample] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    @property
    def mass1(self) -> float:
        return self.ep1.mass_proxy

    @property
    def mass2(self) -> float:
        return self.ep2.mass_proxy
