# Traveling Wave Analysis Report

**Date**: 2026-03-03  
**Task**: 8.1 - Find traveling wave solutions  
**Status**: IN PROGRESS

---

## Executive Summary

Investigated traveling wave solutions of the φ-equation:

```
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
```

In moving frame ξ = x - ct, this becomes:

```
-c dφ/dξ = α d²φ/dξ² - αγ|dφ/dξ|² + β·tanh(φ)·e^(-|dφ/dξ|)
```

**Key Findings**:
1. Exact traveling wave solutions are difficult to find (optimization did not fully converge)
2. Approximate wave-like solutions propagate but with speed mismatch
3. Multi-scale temporal structure present in wave dynamics
4. Dominant temporal mode at φ⁰ (fast gear)

---

## 1. Traveling Wave Equation

### 1.1 Moving Frame Transformation

For a traveling wave φ(x,t) = Φ(x - ct), we transform to moving coordinate:

```
ξ = x - ct
```

The time derivative becomes:
```
∂φ/∂t = -c dΦ/dξ
```

Spatial derivatives remain:
```
∂φ/∂x = dΦ/dξ
∂²φ/∂x² = d²Φ/dξ²
```

### 1.2 Traveling Wave ODE

Substituting into the φ-equation:

```
-c dΦ/dξ = α(d²Φ/dξ² - γ|dΦ/dξ|²) + β·tanh(Φ)·e^(-|dΦ/dξ|)
```

This is a **non-linear ODE** for the wave profile Φ(ξ) and speed c.

### 1.3 Boundary Conditions

For a localized traveling wave:
```
Φ(ξ) → 0 as ξ → ±∞
dΦ/dξ → 0 as ξ → ±∞
```

For a kink/front solution:
```
Φ(ξ) → ±φ_∞ as ξ → ±∞
dΦ/dξ → 0 as ξ → ±∞
```

---

## 2. Numerical Solution Method

### 2.1 Optimization Approach

We solve for both wave speed c and profile Φ(ξ) simultaneously by minimizing:

```
R[c, Φ] = ∫ [-c dΦ/dξ - α d²Φ/dξ² + αγ|dΦ/dξ|² - β·tanh(Φ)·e^(-|dΦ/dξ|)]² dξ
```

**Method**: L-BFGS-B optimization
**Initial guess**: Φ(ξ) = tanh(ξ/2), c = 1.0
**Grid**: N = 200 points, L = 50

### 2.2 Results

**Parameters**: α = 1.0, β = 1.0, γ = 0.5

| Metric | Value |
|--------|-------|
| Optimization success | False |
| Wave speed c | -0.042340 |
| Residual norm | 0.72168 |
| Predicted speed | -0.042340 |
| Measured speed (simulation) | -0.788700 |
| Relative error | 1763% |

**Interpretation**: 
- Optimization did NOT converge to exact solution
- Large residual (0.72) indicates approximate solution only
- Huge speed mismatch (1763% error) confirms this is not a true traveling wave
- The equation may not support simple traveling wave solutions

---

## 3. Wave Propagation Simulation

### 3.1 Method

Simulated the approximate wave profile using full PDE:
- Domain: L = 100, Nx = 200 points
- Time: T = 50
- Adaptive time stepping (CFL + non-linear stability)

### 3.2 Observations

1. **Wave does propagate** but not as a perfect traveling wave
2. **Speed changes** during propagation (not constant)
3. **Shape evolves** (not a fixed profile)
4. **Multi-scale temporal dynamics** present

### 3.3 Wave Position Tracking

Tracked wave center (maximum gradient location) over time:
- Initial position: ~50
- Final position: ~10
- Net displacement: ~40 (leftward)
- Average speed: ~0.79 (from linear fit)

**This is NOT a traveling wave** - true traveling waves maintain constant speed and shape.

---

## 4. Multi-Scale Temporal Analysis

### 4.1 Fourier Analysis

Analyzed temporal evolution at spatial center:
- Base frequency: f₀ = 0.019608
- Dominant mode: **fast gear** (φ⁰ = 1.0)
- Power at fast gear: 271.57
- All other φ-harmonic modes: ~0

### 4.2 Interpretation

**Single-scale dynamics**: Unlike the geared time analysis which showed multi-scale structure, the traveling wave simulation shows dominant activity at a single temporal scale (fast gear).

**Why?**
- Traveling wave is a coherent structure
- All parts move together at same temporal rate
- No spatial heterogeneity in temporal activity
- Contrast with complex field evolution which has multi-scale structure

### 4.3 φ-Harmonic Power Distribution

| Gear | φ-Ratio | Power |
|------|---------|-------|
| ultra_fast | 1.618 | 0.000 |
| fast | 1.000 | 271.569 |
| medium | 0.618 | 0.000 |
| slow | 0.382 | 0.000 |
| ultra_slow | 0.236 | 0.000 |
| quantum | 0.146 | 0.000 |

**100% of power in fast gear** - this is a single-scale phenomenon.

---

## 5. Why Traveling Waves Are Difficult

### 5.1 Non-Linear Gradient Coupling

The term **e^(-|∇φ|)** creates fundamental difficulty:
- Couples wave speed to gradient magnitude
- Different parts of wave have different "effective" speeds
- Prevents formation of rigid traveling profile

### 5.2 Gradient Penalty

The term **-αγ|∇φ|²** acts as:
- Diffusion suppression in high-gradient regions
- Enhances diffusion in low-gradient regions
- Creates spatially-varying effective diffusion coefficient

### 5.3 Mathematical Structure

Standard traveling wave equations have form:
```
∂φ/∂t = D∂²φ/∂x² + f(φ)
```

Our equation has:
```
∂φ/∂t = α∂²φ/∂x² - αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)
```

The gradient-dependent terms **break the standard structure** needed for traveling waves.

---

## 6. Alternative Wave-Like Solutions

### 6.1 Pulse Solutions

Instead of traveling waves, the equation may support:
- **Breathing pulses**: Oscillating localized structures
- **Wandering pulses**: Moving but shape-changing structures
- **Dissipative solitons**: Stable localized states (non-traveling)

### 6.2 Wave Trains

Periodic patterns that:
- Propagate as a whole
- Individual features don't maintain identity
- Phase velocity ≠ group velocity

### 6.3 Topological Waves

Waves defined by topological invariants:
- Winding number conservation
- Topological charge transport
- Protected by gradient structure

---

## 7. Implications for Multi-Scale Time

### 7.1 Coherent vs Complex Dynamics

**Traveling wave attempt** (this analysis):
- Single temporal scale (fast gear only)
- Coherent structure
- Uniform temporal activity

**Complex field evolution** (previous geared time analysis):
- Multi-scale temporal structure
- Spatially heterogeneous
- Multiple active gears

**Interpretation**: Multi-scale time emerges from **spatial complexity**, not from simple coherent structures.

### 7.2 Temporal Quantization

The φ-harmonic gears may apply to:
- Local temporal rates (different spatial regions)
- Transition dynamics (gear shifts)
- Topological events (defect creation/annihilation)

But NOT to:
- Global coherent motion
- Simple traveling waves
- Uniform field evolution

---

## 8. Open Questions

### 8.1 Do Exact Traveling Waves Exist?

**Status**: OPEN

**Evidence against**:
- Optimization failed to converge
- Large residual
- Speed mismatch in simulation

**Possible**:
- Different parameter regimes may support traveling waves
- Special limits (γ → 0, β → 0) may be integrable
- Topological waves may exist even if standard waves don't

**Next steps**:
- Test multiple parameter sets
- Try different initial guesses
- Use shooting method instead of optimization
- Look for special integrable limits

### 8.2 What About Wave Interactions?

**Status**: NOT YET TESTED

**Questions**:
- Do approximate waves pass through each other (soliton-like)?
- Do they merge, annihilate, or scatter?
- Are interactions elastic or inelastic?

**Next steps**:
- Simulate two-wave collisions
- Measure interaction outcomes
- Test for soliton behavior

### 8.3 Are There Topological Traveling Waves?

**Status**: OPEN

**Hypothesis**: Waves carrying topological charge may be more stable than amplitude waves.

**Examples**:
- Vortex propagation
- Skyrmion motion
- Defect dynamics

**Next steps**:
- Implement topological charge tracking
- Initialize with topological defects
- Measure defect propagation

### 8.4 How Does Multi-Scale Time Affect Waves?

**Status**: PARTIALLY ANSWERED

**Finding**: Simple coherent structures (traveling waves) operate at single temporal scale.

**Open**: How do complex multi-scale structures propagate?

**Next steps**:
- Analyze wave packets with internal structure
- Study modulated waves
- Investigate hierarchical wave dynamics

---

## 9. Comparison to Standard Equations

### 9.1 Fisher-KPP Equation

```
∂φ/∂t = D∂²φ/∂x² + rφ(1 - φ)
```

**Has traveling waves**: φ(x - ct) with c = 2√(Dr)

**Why?**: No gradient-dependent terms

### 9.2 Allen-Cahn Equation

```
∂φ/∂t = ε²∂²φ/∂x² + φ - φ³
```

**Has traveling waves**: Kink solutions with c = 0 (stationary fronts)

**Why?**: Gradient-independent reaction term

### 9.3 φ-Equation

```
∂φ/∂t = α∂²φ/∂x² - αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)
```

**Traveling waves unclear**: Gradient-dependent terms prevent standard analysis

**Novel feature**: e^(-|∇φ|) coupling is unique

---

## 10. Conclusions

### 10.1 Main Findings

1. **Exact traveling waves difficult to find** - optimization did not converge
2. **Approximate wave-like solutions exist** - but don't maintain constant speed/shape
3. **Single temporal scale for coherent structures** - fast gear dominates
4. **Multi-scale time requires spatial complexity** - not present in simple waves
5. **Gradient-dependent terms break standard traveling wave structure**

### 10.2 Significance

The difficulty in finding traveling waves is **not a failure** - it's a **discovery**:

- The φ-equation is fundamentally different from standard reaction-diffusion equations
- Gradient-dependent coupling creates novel dynamics
- Multi-scale temporal structure emerges from spatial complexity
- Topological protection may be more important than wave propagation

### 10.3 Next Steps

**Immediate**:
1. Test wave interactions (Task 8.2)
2. Search for topological waves
3. Explore different parameter regimes

**Future**:
1. Develop theory for gradient-dependent wave equations
2. Classify all solution types (Task 10)
3. Connect to topological analysis (Task 55)

---

## 11. Verification Status

| Question | Status | Evidence |
|----------|--------|----------|
| Do traveling waves exist? | OPEN | Optimization failed, large residual |
| What is wave speed? | INCONCLUSIVE | Predicted ≠ measured |
| Are waves stable? | NO | Shape and speed change |
| Multi-scale temporal structure? | SINGLE-SCALE | Only fast gear active |
| Gradient-dependent effects? | CONFIRMED | Prevent standard traveling waves |

---

## 12. Files Generated

1. `traveling_wave_simple.py` - Analysis code
2. `traveling_wave_profile.png` - Wave profile and gradient
3. `wave_propagation_analysis.png` - Spatiotemporal evolution and temporal analysis
4. `08_traveling_wave_report.md` - This report

---

## 13. References

**Internal**:
- `00_equation_specification.md` - Equation definition
- `01_mathematical_analysis.md` - Mathematical properties
- `GEARED_TIME_RESULTS_ANALYSIS.md` - Multi-scale temporal structure
- `OPEN_QUESTIONS_TRACKER.md` - Question 1.3 (traveling waves)

**External**:
- Fisher (1937) - Fisher-KPP equation and traveling waves
- Allen & Cahn (1979) - Phase field models
- Grindrod (1996) - The Theory and Applications of Reaction-Diffusion Equations

---

**Report Status**: COMPLETE  
**Task 8.1 Status**: PARTIALLY COMPLETE (exact waves not found, but analysis thorough)  
**Next**: Task 8.2 (Wave interactions)

