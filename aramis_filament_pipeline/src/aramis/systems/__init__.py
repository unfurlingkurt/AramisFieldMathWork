"""Pluggable measurement systems for locating a filament's central object."""

from .base import LocatedObject, MeasurementSystem
from .euclidean import EuclideanMidpoint
from .farey_medoid import FareyMedoid
from .force_balance import ForceBalancePoint


def default_systems():
    """The three systems compared on identical inputs."""
    return [EuclideanMidpoint(), ForceBalancePoint(), FareyMedoid()]


__all__ = [
    "MeasurementSystem",
    "LocatedObject",
    "EuclideanMidpoint",
    "ForceBalancePoint",
    "FareyMedoid",
    "default_systems",
]
