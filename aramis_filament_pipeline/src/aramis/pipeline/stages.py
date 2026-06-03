"""Staged pipeline entry points. Each stage is a pure function: inputs -> artifacts.

Stage 0 runs with zero external data and proves the machinery recovers a planted
signal. Stages 1-3 (real catalogs, map sampling, full null battery) are added in
later commits and degrade gracefully if their optional dependencies are absent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

from ..data.loaders.synthetic import make_synthetic
from ..data.schema import Filament
from ..geometry.metric import DEFAULT_METRIC, RatioMetric
from ..quantize.scale import DEFAULT_MASS_SCALE, ScaleSpec
from ..systems import default_systems
from ..systems.base import MeasurementSystem
from .report import write_csv


def evaluate_filaments(
    filaments: Sequence[Filament],
    systems: Optional[Sequence[MeasurementSystem]] = None,
    spec: ScaleSpec = DEFAULT_MASS_SCALE,
    metric: RatioMetric = DEFAULT_METRIC,
) -> List[Dict[str, object]]:
    """Run every system on every filament; one row per filament.

    Includes per-system located axis fraction ``t`` and, when a planted center is
    known (synthetic data), the absolute error of each system.
    """
    systems = list(systems) if systems is not None else default_systems()
    rows: List[Dict[str, object]] = []
    for fil in filaments:
        planted = fil.meta.get("planted_center")
        row: Dict[str, object] = {
            "id": fil.id,
            "mass1": fil.mass1,
            "mass2": fil.mass2,
            "planted_center": planted,
        }
        for sysm in systems:
            located = sysm.locate(fil, spec=spec, metric=metric)
            row[f"{sysm.name}_t"] = round(located.t, 6)
            if planted is not None:
                row[f"{sysm.name}_err"] = round(abs(located.t - planted), 6)
        rows.append(row)
    return rows


def summarize(rows: Sequence[Dict[str, object]], systems_names: Sequence[str]) -> Dict[str, object]:
    """Mean absolute error per system + the medoid-vs-midpoint recovery verdict."""
    summary: Dict[str, object] = {}
    for name in systems_names:
        errs = [r[f"{name}_err"] for r in rows if r.get(f"{name}_err") is not None]
        summary[f"{name}_mean_err"] = float(np.mean(errs)) if errs else None
    me = summary.get("farey_medoid_mean_err")
    eu = summary.get("euclidean_midpoint_mean_err")
    if me is not None and eu is not None:
        summary["medoid_beats_euclidean"] = bool(me < eu)
        summary["improvement"] = float(eu - me)
    return summary


def stage0_puremath(
    out_dir: str | Path = "outputs/stage0",
    n: int = 60,
    seed: int = 0,
    spec: ScaleSpec = DEFAULT_MASS_SCALE,
    metric: RatioMetric = DEFAULT_METRIC,
) -> Dict[str, object]:
    """Zero-data demonstration: planted-signal recovery on synthetic filaments."""
    systems = default_systems()
    filaments = make_synthetic(n=n, seed=seed)
    rows = evaluate_filaments(filaments, systems=systems, spec=spec, metric=metric)
    summary = summarize(rows, [s.name for s in systems])

    metadata = {
        "stage": "0_puremath",
        "n_filaments": n,
        "seed": seed,
        "metric": metric.__name__,
        **spec.to_metadata(),
        **{f"summary_{k}": v for k, v in summary.items()},
    }
    out_path = write_csv(Path(out_dir) / "medoid_vs_centroid.csv", rows, metadata)
    return {"rows": rows, "summary": summary, "csv": str(out_path)}
