# The φ-Equation: A Single Field Equation for All of Physics

**A deterministic, discrete-substrate field equation from which quantum mechanics, classical mechanics, electromagnetism, general relativity, thermodynamics, and the Standard Model of particle physics all emerge as limiting cases.**

## The Equation

```
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^{-|∇φ_t|}
```

Three terms in tension:

| Term | Role | Character |
|------|------|-----------|
| `αΔφ` | Diffusion — spreads structure | Linear, isotropic |
| `-αγ\|∇φ\|²` | Gradient self-interaction — concentrates structure | Nonlinear, breaks isotropy |
| `β·tanh(φ)·e^{-\|∇φ\|}` | Saturating reaction, modulated by gradients | Nonlinear, couples field value to spatial structure |

The gradient-modulated reaction term `e^{-|∇φ|}` is the key novelty. It freezes dynamics at high-gradient regions and activates them at low-gradient regions, creating self-stabilizing topological structures that no standard reaction-diffusion equation produces.

## What This Is

The φ-equation is the **continuous limit of discrete Stern-Brocot tree dynamics**. At the deepest level, the universe is a lattice of rationals evolving by mediant operations — exact arithmetic, no reals, no probabilities. The φ-equation is what those dynamics look like in the continuum.

The hierarchy:

```
Discrete Stern-Brocot dynamics    (most fundamental — deterministic rational arithmetic)
        ↓ operator formulation
Quantum Field Theory               (fields promoted to operators on Hilbert space)
        ↓ ℏ → 0
Classical φ-equation               (the equation above — saddle-point of path integral)
        ↓ |∇φ| → 0
Classical mechanics                (smooth fields, Newton's laws)
```

Every layer below the top is an approximation. QFT is not fundamental — it is what the discrete substrate looks like when projected into continuous space.

## What Emerges

### From a single equation, the following have been derived:

**Quantum Mechanics** — The Schrödinger equation emerges via the Madelung representation in the small-amplitude, rapid-oscillation limit. The measurement problem is solved: "collapse" is deterministic gear-locking between observer and system φ-fields, not a physical process. The Born rule emerges from energy density distributions. Entanglement is local in 4D (3 space + intrinsic time τ), non-local only in the 3D projection.

**Classical Mechanics** — Newton's laws, Lagrangian and Hamiltonian formulations emerge in the smooth-field limit where `|∇φ| → 0`.

**Electromagnetism** — Maxwell's equations emerge from U(1) phase symmetry of the φ-field. The photon is a massless phonon mode with linear dispersion.

**General Relativity** — Einstein's field equations emerge from the identification: space = `|∇φ|`, time = `dφ/dt`, speed of light = `dφ/|∇φ|`. Gradient conservation IS the constancy of the speed of light.

**Thermodynamics** — All four laws derived. Entropy emerges from Farey depth coarsening.

**Statistical Mechanics** — Partition functions and ensemble theory from Stern-Brocot state counting.

**The Standard Model** — All particles are phonon modes of the φ-field substrate. Fermions have half-integer winding numbers in the SB tree, bosons have integer winding. Gauge symmetries (U(1), SU(2), SU(3)) emerge from substrate topology. The Higgs mechanism is the substrate acquiring equilibrium `⟨φ⟩ = v`, opening gaps in the phonon spectrum. Three generations of fermions correspond to three Farey depths.

## Key Discoveries

### Gradient Norm Conservation
The most important conservation law: `||∇φ||² = constant`. Mass and energy are NOT conserved. The gradient structure is the invariant currency of the equation. Three additional novel conserved quantities: `φ·|∇φ|²`, `|∇φ|³`, and `φ·e^{-φ²}`.

### Toroidal Topology
The dynamics inherently generate toroidal topology T² = S¹ × S¹. This is not imposed by boundary conditions — it emerges from the competition between diffusion and gradient self-interaction. In 3D, the prediction is T³ with φ-harmonic circumference ratios.

### Impedance Framework
The ratio Z = `|∇φ|/|dφ/dt|` partitions the field into three regimes:
- **Vacuum** (Z < 33rd percentile) — time flows freely
- **Light** (33rd-67th percentile) — propagating structure
- **Matter** (Z > 67th percentile) — time trapped in spatial gradients

The optimal gradient `|∇φ| = 1` gives maximum propagation velocity `v_max = e⁻¹ ≈ 0.368` — the "speed of light" in natural units. Measured computationally at `|∇φ| = 1.008` (0.81% error).

### Geared Time
Time is not continuous. It operates through discrete φ-harmonic ratios `{φ⁻⁴, φ⁻³, φ⁻², φ⁻¹, φ⁰, φ¹}` where φ = (1+√5)/2. The torus IS the gear system — winding number = gear ratio. Impedance regimes distribute as exact thirds at Farey depth 2 on the Stern-Brocot tree.

### Spacetime Emergence
Only φ exists. Space, time, and the speed of light are all derived quantities:
- Space = `|∇φ|`
- Time = `dφ/dt`
- c = `dφ/|∇φ|`

### Measurement Problem Solved
Quantum measurement is deterministic gear-locking. When an observer (itself a φ-field) couples to a system, the high `|∇φ|` at the boundary causes `e^{-|∇φ|} → 0`, freezing the dynamics and locking the system to the observer's temporal gear. No wave function collapse. No fundamental randomness. No consciousness required.

## Repository Structure

```
phi_equation_investigation/
├── README.md
│
├── phi_domain_analysis/              # Computational tools
│   ├── core/                         # Core implementation
│   │   ├── equation_solver.py        # φ-equation solver with adaptive stepping
│   │   ├── metrics.py                # Analysis metrics
│   │   └── visualization.py          # Visualization tools
│   └── analysis/                     # Analysis scripts
│
├── Derivation Documents              # Physics derivations from φ-equation
│   ├── QUANTUM_MECHANICS_COMPLETE.md
│   ├── QUANTUM_MECHANICS_FROM_PROJECTION.md
│   ├── CLASSICAL_MECHANICS_DERIVATION.md
│   ├── ELECTROMAGNETISM_DERIVATION.md
│   ├── GENERAL_RELATIVITY_COMPLETE.md
│   ├── THERMODYNAMICS_DERIVATION.md
│   ├── STATISTICAL_MECHANICS_DERIVATION.md
│   ├── GAUGE_SYMMETRIES_DERIVATION.md
│   ├── HIGGS_MECHANISM_PHONONIC.md
│   ├── PARTICLE_PHYSICS_FROM_PHONONS.md
│   └── ...
│
├── Framework Documents               # Core theoretical framework
│   ├── DISCRETE_EVOLUTION_RULE.md    # Discrete SB dynamics
│   ├── CONTINUOUS_LIMIT_DERIVATION.md
│   ├── PROJECTION_OPERATOR_FORMALIZATION.md
│   ├── GEOMETRIC_CLOSURE_PROOF.md
│   ├── SPACETIME_EMERGENCE.md
│   ├── GEARED_TIME_BREAKTHROUGH.md
│   ├── TOROIDAL_DISCOVERY.md
│   └── ...
│
└── Discovery Documents               # Key findings and breakthroughs
    ├── CONSERVATION_CLARIFICATION_2026-03-03.md
    ├── RATIONAL_TIME_STRUCTURE.md
    ├── IMPEDANCE_FRAMEWORK_VERIFIED.md
    ├── OBSERVER_PROJECTION_FRAMEWORK.md
    └── ...
```

## Quick Start

```python
from phi_domain_analysis.core.equation_solver import AdvancedPhiSolver

solver = AdvancedPhiSolver(
    domain_size=(64,),
    dx=1.0,
    alpha=1.0,
    beta=0.5,
    gamma=0.1,
    dim=1
)

solver.set_initial_condition('random', amplitude=0.1)
history = solver.run(n_steps=1000, save_interval=10)
```

## Installation

```bash
git clone https://github.com/unfurlingkurt/phi_equation_investigation.git
cd phi_equation_investigation
pip install numpy scipy matplotlib
```

## The Central Claim

**Everything is φ.** There is no spacetime, no particles, no forces — only a single scalar field evolving by a deterministic nonlinear rule. Space is where the field has gradients. Time is where the field changes. Matter is where time gets stuck in spatial gradients. Light is the propagation of gradient structure at the optimal speed `e⁻¹`. Quantum mechanics is what deterministic 4D dynamics look like when projected into 3D.

The equation is not a model of physics. It is a candidate for what physics IS.

## License

MIT License

## Contact

- **Repository**: https://github.com/unfurlingkurt/phi_equation_investigation
- **Issues**: GitHub issues for questions and discussion
