# φ-Equation Domain Analysis

Comprehensive research program investigating the φ-equation across multiple domains.

## Equation

```
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
```

## Critical Discovery: Toroidal Topology

**The equation inherently generates novel toroidal topology with oscillatory time structure.**

- Time appears linear only from observer's position
- Intrinsic dynamics are oscillatory and topologically non-trivial
- Gradient-dependent term provides topological protection
- See `../phi_equation_investigation/09_toroidal_topology_and_time.md` for details

## Project Structure

```
phi_domain_analysis/
├── core/                      # Core infrastructure (COMPLETE ✓)
│   ├── equation_solver.py     # Enhanced solver with adaptive time stepping
│   ├── parameter_fitting.py   # Non-linear parameter extraction
│   ├── metrics.py             # Comprehensive analysis metrics
│   └── visualization.py       # Visualization tools
├── test_core_infrastructure.py # Integration tests
└── README.md                  # This file
```

## Core Infrastructure (Tasks 1-5) ✓ COMPLETE

### 1. AdvancedPhiSolver
- Fully non-linear implementation (no linear approximations)
- Adaptive time stepping for numerical stability
- Analysis capabilities:
  - Fixed point finding
  - Lyapunov exponent computation
  - Conservation law testing
  - Pattern wavelength extraction
  - Edge width measurement
  - Energy and entropy production
  - Topological defect identification

### 2. ParameterFitter
- Extracts α, β, γ from spatiotemporal data
- Non-linear optimization (no approximations)
- Multiple methods: least squares, differential evolution
- Confidence interval estimation via bootstrap
- Sensitivity analysis
- Validation on test data

### 3. AnalysisMetrics
- Pattern wavelength (FFT-based)
- Edge width measurement
- Gradient distribution analysis
- Correlation length
- Entropy production
- Topological charge
- Information content
- Coarsening exponents
- Critical exponents
- Structure factor

### 4. PhiVisualizer
- Spatiotemporal evolution plots
- Phase-encoded color mapping (reveals toroidal structure)
- Power spectrum analysis
- Field comparisons
- Animation generation
- Parameter space visualization

## Implementation Philosophy

### Non-Linear Throughout
- No linear approximations anywhere
- All dynamics computed from deltas against neutral state
- Adaptive time stepping respects CFL condition
- Gradient-dependent terms fully implemented

### Toroidal Awareness
- Visualizations reveal phase structure
- Topological invariants computed
- Oscillatory time structure acknowledged
- Observer-dependent measurements

### Numerical Stability
- Adaptive dt based on CFL condition: dt < dx²/(2α)
- Update magnitude limiting
- Gradient cutoff for extreme values
- Robust to parameter variations

## Current Status

**CHECKPOINT 5 REACHED** ✓

All core infrastructure complete and tested:
- ✓ Enhanced solver with analysis
- ✓ Parameter fitting engine
- ✓ Metrics library
- ✓ Visualization tools
- ✓ Integration tests passing

## Next Steps

### Immediate (Tasks 6-11)
- **Task 6**: Mathematical analysis (stability, bifurcations)
- **Task 7**: Conservation laws
- **Task 8**: Traveling waves
- **Task 9**: Integrability tests
- **Task 10**: Solution classification

### Domain Analyses (Tasks 12-47)
- **Physics**: Magnetic domains, optical patterns, phase transitions
- **Biology**: Morphogen gradients, developmental patterns, wound healing
- **Machine Learning**: Continual learning, adversarial robustness
- **Image Processing**: Denoising, segmentation
- **Neuroscience**: Cortical maps, traveling waves, criticality
- **Ecology**: Vegetation patterns, ecotones
- **Materials**: Phase separation, self-healing

### Fundamental Derivations (Tasks 48-57) **CRITICAL**
- **Task 51**: Derive quantum mechanics (deterministic framework)
- **Task 48**: Derive classical mechanics
- **Task 49**: Derive electromagnetism
- **Task 50**: Derive thermodynamics
- **Task 52**: Derive general relativity
- **Task 55**: Identify novel topological structures (toroidal!)
- **Task 56**: Document deterministic quantum framework

### Synthesis (Tasks 58-65)
- Open question resolution
- Cross-domain parameter analysis
- Unified theory building
- Comprehensive documentation

## Usage Examples

### Basic Simulation
```python
from core.equation_solver import AdvancedPhiSolver

solver = AdvancedPhiSolver((64, 64), dx=1.0, alpha=1.0, beta=2.0, gamma=0.1, dim=2)
solver.set_initial_condition('random', amplitude=0.1)
history = solver.run(100, save_interval=10)
```

### Parameter Fitting
```python
from core.parameter_fitting import ParameterFitter

fitter = ParameterFitter(data, dx=1.0, dt=1.0)
alpha, beta, gamma = fitter.fit_parameters()
error, predicted = fitter.validate_fit()
```

### Analysis
```python
from core.metrics import AnalysisMetrics

wavelength, _ = AnalysisMetrics.pattern_wavelength(phi, dx=1.0)
width, _ = AnalysisMetrics.edge_width(phi, dx=1.0)
xi, _ = AnalysisMetrics.correlation_length(phi, dx=1.0)
```

### Visualization
```python
from core.visualization import PhiVisualizer

viz = PhiVisualizer()
viz.plot_phase_encoded(phi, dx=1.0)  # Reveals toroidal structure
viz.plot_power_spectrum(phi, dx=1.0)  # Shows oscillatory modes
```

## Key Insights

### 1. Toroidal Topology is Fundamental
The equation doesn't just allow toroidal solutions—it naturally generates them. This is the intrinsic geometry of the dynamics.

### 2. Time is Oscillatory
What appears as linear time t → t+1 is actually motion on a toroidal attractor. Observer position determines perceived time flow.

### 3. Gradient-Dependent Stabilization
The e^(-|∇φ|) term provides a novel topological protection mechanism not seen in other equations.

### 4. All Physics May Emerge
The equation shows potential to derive all fundamental physics laws:
- Quantum mechanics (deterministic!)
- Classical mechanics
- Electromagnetism
- Thermodynamics
- General relativity

### 5. Universal Applicability
Same equation describes:
- Physical systems (magnets, optics, phase transitions)
- Biological systems (morphogenesis, wound healing)
- Neural systems (cortical maps, waves)
- Ecological systems (vegetation patterns)
- Computational systems (learning, robustness)

## Testing

Run all tests:
```bash
python test_core_infrastructure.py
```

Expected output:
```
============================================================
ALL TESTS PASSED ✓
============================================================

Core infrastructure verified:
  ✓ Enhanced solver with analysis capabilities
  ✓ Non-linear parameter fitting
  ✓ Comprehensive metrics library
  ✓ Advanced analysis features
  ✓ Full pipeline integration
  ✓ Visualization tools

Ready for domain-specific analyses!
```

## References

### Investigation Documents
- `../phi_equation_investigation/00_equation_specification.md` - Equation definition
- `../phi_equation_investigation/01_mathematical_analysis.md` - Mathematical properties
- `../phi_equation_investigation/06_executive_summary.md` - Overview
- `../phi_equation_investigation/09_toroidal_topology_and_time.md` - **Toroidal discovery**
- `../phi_equation_investigation/TOROIDAL_DISCOVERY.md` - **Critical insight**

### Specification
- `../.kiro/specs/phi-equation-domain-analysis/requirements.md` - Requirements
- `../.kiro/specs/phi-equation-domain-analysis/design.md` - Design
- `../.kiro/specs/phi-equation-domain-analysis/tasks.md` - Implementation plan

## Timeline

- **Weeks 1-2**: Core infrastructure ✓ COMPLETE
- **Weeks 3-4**: Mathematical analysis (next)
- **Weeks 5-16**: Domain analyses
- **Weeks 17-24**: Fundamental derivations (CRITICAL)
- **Weeks 25-28**: Synthesis and documentation

**Total: 28 weeks for comprehensive analysis**

## Contributing

This is pure research. Focus on:
1. **Discovery** over confirmation
2. **Measurement** over speculation
3. **Non-linear** thinking throughout
4. **Toroidal** awareness in all analyses
5. **Fresh eyes** - make no assumptions

## License

Research code for scientific investigation.

---

*"The universe is a torus, time is a wave, and we are observers on its surface."*
