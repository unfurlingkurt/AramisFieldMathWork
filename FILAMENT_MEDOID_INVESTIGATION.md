# Cosmic Filament Medoid Investigation

**Date**: 2026-06-04
**Status**: NATIVE relational program built and run on real data. Four distinct native
encodings tested — **all non-detections** (no Farey/RatioSpace signal beyond random).
**Code**: [`aramis_filament_pipeline/`](aramis_filament_pipeline/)

## Native relational results (the real test)

After correcting the early linear contamination (means, Euclidean distance, projection),
the test was rebuilt to be strictly native: relationships not positions, connectivity taken
from the observed catalogue (never Euclidean proximity), exact-ratio encodings, only
composition `⊗` / mediant `⊕` / continued-fraction tension, and a relational rewiring null
(`aramis/web/`, guarded by a test that bans linear code). Run on the Tempel DR8 catalogue
(12,495 filaments, ~1.8M continued-fraction partial quotients):

| Test | native quantity | result | verdict |
|---|---|---|---|
| Position barcode | galaxy axis-position CF address | φ-coh 0.600 vs 0.596 uniform; no wall deficit | non-detection |
| Stage A | redshift difference-ratios `\|Δz_k\|:\|Δz_{k+1}\|` | φ-coh **0.5784** vs **0.5820** shuffled | refuted (real *more* complex) |
| Stage B | luminosity ratios `L_i:L_j` | φ-coh **0.5779** vs **0.5773** shuffled | non-detection |
| Stage C | Farey adjacency `\|ad−bc\|=1` of relation sequence | det=1 **0.046** vs **0.046** shuffled | non-detection |

**Honest conclusion so far:** across four framework-faithful native encodings, the Tempel
cosmic-web relations are statistically indistinguishable from generic reals (Gauss–Kuzmin
neighborhood) and from a relational-rewiring null. The hypothesis that the web's connected
nodes sit at low-tension Farey/Stern-Brocot relationships is **not supported by this data
under these encodings**. This is a falsifiable negative, not a proof of absence: it does not
rule out a different relational quantity (Stage D alignment is not yet run), but the
position, redshift, luminosity, and Farey-adjacency channels show nothing.

---

### Earlier (superseded) Stage-1 mass-only run

---

## The hypothesis

A cosmic filament's central emitting object sits at a **native RatioSpace (Farey)
medoid**, not at the Euclidean midpoint of its endpoints:

> **Centroid = projection shadow. Medoid = object.**

The Euclidean midpoint and the conventional force-balance point are estimates in a
*linear* measurement system. The framework's claim is that the physically realized
center is the point of least **continued-fraction tension** to the observed emission
— a *medoid* selected from a discrete Stern-Brocot corridor, not a continuous mean.

## Why this belongs to the φ-equation framework

This is the **empirical arm** of a result this repository already argues
theoretically:

- [`RATIOSPACE_FINDINGS_SUMMARY.md`](RATIOSPACE_FINDINGS_SUMMARY.md) — impedance
  clusters **11.83×** at Stern-Brocot ratios, with an exact vacuum/light/matter
  **thirds** split at **Farey depth 2** (`[0,1/3], [1/3,2/3], [2/3,1]`). The native
  axis corridor used here reproduces exactly those thirds at depth 2.
- [`RATIONAL_TIME_STRUCTURE.md`](RATIONAL_TIME_STRUCTURE.md) — distance/tension as
  continued-fraction length on the Stern-Brocot tree.
- [`COSMOLOGY_FROM_PHI.md`](COSMOLOGY_FROM_PHI.md) — large-scale structure from the
  φ-equation; filaments are the structure this predicts.

The new code reuses the framework's native geometry rather than reinventing it: its
`Ratio` is consistency-tested against the canonical `Rational` in
[`phi_domain_analysis/core/discrete_sb_simulator.py`](phi_domain_analysis/core/discrete_sb_simulator.py)
(agreement on mediant and continued fractions over 4000 random cases).

## The native geometry and the metric decision

Two candidate "tensions" existed in the prior material, and the result rests on which
is correct:

| metric | definition | self-distance (raw) | symmetry |
|---|---|---|---|
| **additive** (repo default) | `cf_length(\|x − y\|)` | 1 → normalized to 0 | symmetric |
| **multiplicative** (starter) | `cf_length(x ⊗ y)`, `⊗`=quotient | 1 → normalized to 0 | **asymmetric (quasi-metric)** |

Decisions, locked by tests in `src/aramis/geometry/metric.py`:
- `⊗` (compose) is the **quotient** ratio `(a/b)÷(c/d)` — an algebraic operation with
  a right identity `1:1`, **not** a distance, and neither associative nor commutative.
- Both metrics are normalized so `d(x,x)=0`; the raw `cf_length`-of-identity = 1 wart
  is pinned by a regression test so it cannot silently return.
- **Additive is the default.** The multiplicative tension is a genuine *quasi*-metric.
- **Which metric maximizes medoid-vs-emission alignment on real data is itself an open
  empirical question** — both are selectable (`aramis ... --metric ...`).

## What is built (the instrument)

A durable, installable, tested package — `aramis_filament_pipeline/` — that ingests
**linear/observational** data and re-expresses it in the **native ratio geometry**,
then compares **measurement systems** on identical inputs.

```
geometry/   Ratio, tension metrics, mediant corridors, Farey medoid (single source of truth)
quantize/   documented, reproducible ScaleSpec: the LINEAR -> NATIVE bridge
systems/    EuclideanMidpoint | ForceBalancePoint | FareyMedoid (one interface)
data/       normalized schema; synthetic + Tempel/Bisous + SDSS LRG loaders; astropy cosmology
maps/       HEALPix emission sampling along axes (ROSAT / GLEAM / Planck-y)
stats/      bootstrap CIs, effect sizes, and the four null controls
pipeline/   staged orchestration; cli.py: `aramis stage{0,1,2,3}`
```

Staging (each stage is a pure function; **Stage 0 runs on numpy alone**, astronomy
libraries are optional `[data]`/`[maps]` extras so the science core can never rot):

| stage | command | what it does | deps |
|---|---|---|---|
| 0 | `aramis stage0` | planted-signal recovery on synthetic data (machinery proof) | numpy |
| 1 | `aramis stage1 <catalog>` | real endpoint pairs → native geometry → three systems | `[data]` |
| 2 | `aramis stage2 <catalog> <map>` | sample emission along axes → medoid fit to emission | `[data]`,`[maps]` |
| 3 | `aramis stage3` | full null/control battery with significance | numpy |

## Results so far (machinery, not yet physics)

On **synthetic** data with centers planted at Farey nodes, the Farey medoid recovers
the planted center with mean error **0.018** vs **0.228** (Euclidean) and **0.079**
(force-balance); effect size **d ≈ 3.9**. In the null battery the **rotated-axes**
control (scrambling the emission axis) erases the advantage (p ≈ 0.02), confirming the
signal lives in the emission geometry. These numbers validate the *instrument*; they
are not evidence about real filaments. The real test runs Stages 1–2 on Tempel/Bisous
filaments and ROSAT/GLEAM/Planck-y maps (see `data/MANIFEST.toml`).

### Real-data run — Stage 1 (Tempel/Bisous, N = 15,421)

The published `dr8_filaments.fits` loads directly (`loader='dr8'`): each filament gives
comoving endpoints (bounding-box corners) and endpoint luminosities `lum1/lum2` as the
mass proxy. Stage 1 ran on all 15,421 filaments; for **59%** the discrete Farey medoid
places the center off the Euclidean midpoint (driven by real luminosity asymmetry).

**First result is a careful negative.** We asked whether the real luminosity-balance
fractions `lum2/(lum1+lum2)` cluster at low-depth Farey nodes vs a matched smooth null.
A naive test gives a striking `z = −18`, but it is an **artifact**: ~**32%** of
filaments have `lum1 == lum2` *exactly*, piling up at fraction 0.5 — which is itself the
lowest Farey node. Excluding that spike, the signal collapses to `z = −1.73` (not
significant). Reproduce with `python scripts/analyze_stage1_farey.py`.

**Takeaway:** the mass-only (luminosity-ratio) test does **not** support the medoid
hypothesis. This is informative — it rules out a spurious mass signal and says the
hypothesis, if true, lives in **emission geometry**, motivating Stage 2 on real maps
(with proper stacking and background subtraction, a sub-project in its own right).

## Key design finding (drives the next step)

The null battery showed the current emission-fit medoid is **mass-blind**:
mass-shuffling and random-pairing nulls leave its advantage unchanged, only emission
scrambling kills it. So there are two distinct, separately testable claims:
1. **Emission claim** — emission concentrates at a Farey-quantized axis position
   (tested at Stage 2 against real maps).
2. **Mass claim** — that position is predictable from the endpoint **mass ratio**
   via the native corridor (the Stage-1 "mass-snap" prediction). These must be tested
   independently; conflating them would be circular.

## Reproducibility & data policy

Raw catalogs/maps are **never committed**. `data/MANIFEST.toml` records every source
(Tempel/Bisous, SDSS LRG, ROSAT, GLEAM, Planck-y) with URLs, citations, and a sha256;
`scripts/download_data.py` fetches and verifies them. Every run writes its
`ScaleSpec`, metric, and seed into the output CSV header.

## Open questions / year-long roadmap

1. **Metric**: additive vs multiplicative — which best aligns the medoid with real
   emission? (A publishable statement about the native geometry.)
2. **Mass vs emission**: test the two claims above separately on real data.
3. **Spine-aware corridors**: seed corridors from Tempel filament *spine points*, not
   just endpoints; do filament **junctions** sit at higher-depth Farey nodes?
4. **Multi-layer maps**: X-ray (ROSAT), radio (GLEAM), SZ (Planck-y), lensing as
   independent sample sets — does the medoid agree across physically distinct tracers?
5. **Thirds structure**: does the depth-2 vacuum/light/matter thirds partition from
   `RATIOSPACE_FINDINGS_SUMMARY.md` appear in the mass-ratio distribution of real pairs?
6. **Cross-survey replication**: SDSS → DESI/Euclid via the same loader contract.

## How to start

```bash
cd aramis_filament_pipeline
pip install -e .            # Stage 0 (numpy only)
pytest                      # 49 tests: metric axioms, recovery, nulls, loaders, maps
aramis stage0               # zero-data demonstration
pip install -e ".[data]"    # then Stage 1 on a real catalog
pip install -e ".[maps]"    # then Stage 2 on a HEALPix map
```
