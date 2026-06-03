# Aramis Filament Medoid Pipeline

A durable research instrument for testing one hypothesis on real cosmic-web data:

> A filament's central emitting object sits at a **native RatioSpace (Farey) medoid**,
> not at the Euclidean midpoint. *Centroid = projection shadow. Medoid = object.*

It ingests **linear / observational** data (sky positions, redshifts, mass proxies,
HEALPix emission maps) and re-expresses it in the framework's **native ratio
geometry** (exact ratios, mediant corridors, continued-fraction tension), then
compares **measurement systems** — Euclidean midpoint, force-balance, Farey medoid —
on identical inputs.

This is the empirical arm of the theoretical RatioSpace result in
`../RATIOSPACE_FINDINGS_SUMMARY.md` (impedance clusters 11.83× at Stern-Brocot
ratios; an exact vacuum/light/matter thirds split at Farey depth 2). See
`../FILAMENT_MEDOID_INVESTIGATION.md` for the full scientific framing and roadmap.

## Design at a glance

```
src/aramis/
  geometry/   native RatioSpace: Ratio, metric (tension), mediant corridors, medoid
  quantize/   the LINEAR -> NATIVE bridge (documented, reproducible ScaleSpec)
  systems/    pluggable MeasurementSystem: euclidean / force_balance / farey_medoid
  data/       normalized schema + loaders (synthetic now; Tempel/Bisous, SDSS LRG next)
  pipeline/   staged orchestration + reproducible CSV output
  cli.py      `aramis <stage>` entry point
```

**Staging.** Stage 0 (native geometry + planted-signal demo) runs on **numpy only**.
Astronomy libraries are optional extras (`[data]`, `[maps]`) so the science core
never rots when an upstream catalog URL or library changes.

## Quickstart (Stage 0 — zero external data)

```bash
pip install -e .          # numpy only
pytest                    # geometry axioms + planted-signal recovery
aramis stage0 --out outputs/stage0
```

`aramis stage0` generates synthetic filaments with a *planted* Farey-node center,
runs all three measurement systems, and reports that the Farey medoid recovers the
planted center better than the Euclidean midpoint — proving the machinery before any
real data is introduced.

## Later stages

```bash
pip install -e ".[data]"            # Stage 1: real catalogs (astropy)
pip install -e ".[maps]"            # Stage 2: HEALPix map sampling (healpy)
python scripts/download_data.py --source tempel_bisous   # checksum-verified
```

Real data is **never committed**; it is reproduced from `data/MANIFEST.toml`.

## The metric decision (important)

There are two candidate native "tensions": additive `cf_length(|x − y|)` (the
existing repo's convention, the default here) and multiplicative `cf_length(x ⊗ y)`
(the starter's). Both are normalized so self-distance is 0. Which one maximizes
medoid-vs-emission alignment on real data is an open empirical question — `aramis`
exposes both via `--metric`. See `src/aramis/geometry/metric.py`.
