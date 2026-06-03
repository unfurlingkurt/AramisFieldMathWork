"""Aramis filament medoid pipeline.

Tests whether a cosmic filament's central emitting object aligns with a native
RatioSpace (Farey) medoid rather than a Euclidean midpoint, by ingesting linear /
observational data and re-expressing it in the framework's native ratio geometry.

See ``FILAMENT_MEDOID_INVESTIGATION.md`` at the repository root for the scientific
framing and its connection to ``RATIOSPACE_FINDINGS_SUMMARY.md``.
"""

from .geometry import Ratio, axis_corridor, corridor_candidates, farey_medoid

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Ratio",
    "corridor_candidates",
    "axis_corridor",
    "farey_medoid",
]
