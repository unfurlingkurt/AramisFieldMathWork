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


def stage1_catalog(
    catalog_path: str | Path,
    out_dir: str | Path = "outputs/stage1",
    loader: str = "tempel",
    spec: ScaleSpec = DEFAULT_MASS_SCALE,
    metric: RatioMetric = DEFAULT_METRIC,
) -> Dict[str, object]:
    """Real catalog geometry: load endpoint pairs and run the three systems.

    No emission samples yet (that is Stage 2), so this is descriptive: it reports,
    per filament, where each measurement system places the center, and how the
    discrete Farey medoid differs from the continuous force-balance point and the
    Euclidean midpoint. ``loader`` is one of ``tempel`` | ``lrg`` | ``csv``.
    """
    if loader == "dr8":
        from ..data.loaders.tempel_bisous import load_dr8_fits
        filaments = load_dr8_fits(catalog_path)
    elif loader == "tempel":
        from ..data.loaders.tempel_bisous import load_filaments
        filaments = load_filaments(catalog_path)
    elif loader == "lrg":
        from ..data.loaders.sdss_lrg_pairs import load_pairs
        filaments = load_pairs(catalog_path)
    else:
        from ..data.loaders.tabular import load_pairs_csv
        filaments = load_pairs_csv(catalog_path)

    systems = default_systems()
    rows = evaluate_filaments(filaments, systems=systems, spec=spec, metric=metric)
    # How often does the discrete medoid disagree with the continuous midpoint?
    n_diff_mid = sum(1 for r in rows if abs(r["farey_medoid_t"] - 0.5) > 1e-6)
    summary = {
        "n_filaments": len(rows),
        "loader": loader,
        "medoid_differs_from_midpoint_frac": (n_diff_mid / len(rows)) if rows else None,
    }
    metadata = {"stage": "1_catalog", "metric": metric.__name__,
                "catalog": str(catalog_path), **spec.to_metadata(),
                **{f"summary_{k}": v for k, v in summary.items()}}
    out_path = write_csv(Path(out_dir) / "catalog_systems.csv", rows, metadata)
    return {"rows": rows, "summary": summary, "csv": str(out_path)}


def attach_emission_samples(
    filaments: Sequence[Filament],
    map_array,
    n_samples: int = 32,
    radius_arcmin: float | None = 30.0,
) -> List[Filament]:
    """Sample a HEALPix map along each filament axis and attach cleaned emission.

    Requires the ``[data]`` (great-circle sampling) and ``[maps]`` (healpy) extras.
    """
    from dataclasses import replace

    from ..data.cosmology import sky_samples_along_axis
    from ..maps.healpix_sampling import sample_along_sky
    from ..maps.profiles import clean_profile, has_signal

    out: List[Filament] = []
    for f in filaments:
        pts = sky_samples_along_axis(f.ep1.ra, f.ep1.dec, f.ep2.ra, f.ep2.dec, n_samples)
        raw = sample_along_sky(map_array, pts, radius_arcmin=radius_arcmin)
        clean = clean_profile(raw)
        out.append(replace(f, samples=clean) if has_signal(clean) else f)
    return out


def stage2_maps(
    catalog_path: str | Path,
    map_path: str | Path,
    out_dir: str | Path = "outputs/stage2",
    loader: str = "tempel",
    n_samples: int = 32,
    radius_arcmin: float | None = 30.0,
    spec: ScaleSpec = DEFAULT_MASS_SCALE,
    metric: RatioMetric = DEFAULT_METRIC,
) -> Dict[str, object]:
    """Sample a real emission map along filament axes and locate centers from it.

    Compares, per filament, the emission peak against each measurement system. This
    is the first stage where the Farey medoid is fit to *observed emission* rather
    than mass alone.
    """
    if loader == "dr8":
        from ..data.loaders.tempel_bisous import load_dr8_fits
        filaments = load_dr8_fits(catalog_path)
    elif loader == "tempel":
        from ..data.loaders.tempel_bisous import load_filaments
        filaments = load_filaments(catalog_path)
    elif loader == "lrg":
        from ..data.loaders.sdss_lrg_pairs import load_pairs
        filaments = load_pairs(catalog_path)
    else:
        from ..data.loaders.tabular import load_pairs_csv
        filaments = load_pairs_csv(catalog_path)

    from ..maps.healpix_sampling import load_healpix_map
    from ..stats.nulls import observed_center_emission

    map_array, nside = load_healpix_map(map_path)
    filaments = attach_emission_samples(filaments, map_array, n_samples, radius_arcmin)

    systems = default_systems()
    rows: List[Dict[str, object]] = []
    for f in filaments:
        emission = observed_center_emission(f)
        row: Dict[str, object] = {"id": f.id, "mass1": f.mass1, "mass2": f.mass2,
                                  "emission_center": round(emission, 6)}
        for sysm in systems:
            loc = sysm.locate(f, spec=spec, metric=metric)
            row[f"{sysm.name}_t"] = round(loc.t, 6)
            row[f"{sysm.name}_err"] = round(abs(loc.t - emission), 6)
        rows.append(row)

    summary = summarize(rows, [s.name for s in systems])
    metadata = {"stage": "2_maps", "metric": metric.__name__, "nside": nside,
                "catalog": str(catalog_path), "map": str(map_path),
                "n_samples": n_samples, "radius_arcmin": radius_arcmin,
                **spec.to_metadata(),
                **{f"summary_{k}": v for k, v in summary.items()}}
    out_path = write_csv(Path(out_dir) / "map_systems.csv", rows, metadata)
    return {"rows": rows, "summary": summary, "csv": str(out_path)}


def stage3_battery(
    out_dir: str | Path = "outputs/stage3",
    n: int = 120,
    seed: int = 0,
    n_null: int = 200,
    spec: ScaleSpec = DEFAULT_MASS_SCALE,
    metric: RatioMetric = DEFAULT_METRIC,
    filaments: Optional[Sequence[Filament]] = None,
    observed=None,
) -> Dict[str, object]:
    """Full null/control battery: Farey medoid vs Euclidean midpoint with significance.

    Defaults to synthetic data with the planted center as ground truth; pass real
    ``filaments`` and an ``observed`` emission-center function for Stage-2 catalogs.
    """
    import json

    from ..stats.nulls import observed_center_planted, run_null_battery
    from ..systems import EuclideanMidpoint, FareyMedoid

    if filaments is None:
        filaments = make_synthetic(n=n, seed=seed)
    if observed is None:
        observed = observed_center_planted

    result = run_null_battery(
        filaments,
        medoid_system=FareyMedoid(),
        baseline_system=EuclideanMidpoint(),
        observed=observed,
        spec=spec,
        metric=metric,
        n_null=n_null,
        seed=seed,
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = {"stage": "3_battery", "seed": seed, "metric": metric.__name__,
              **spec.to_metadata(), "result": result}
    json_path = out / "null_battery.json"
    json_path.write_text(json.dumps(report, indent=2))
    return {"result": result, "json": str(json_path)}
