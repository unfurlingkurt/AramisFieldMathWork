# φ-Equation Investigation: Quick Reference

**For rapid orientation and daily research guidance**

---

## The Equation

```
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
```

**α**: Diffusion (α > 0)  
**β**: Reaction (β ≥ 0)  
**γ**: Gradient penalty (γ ≥ 0)

---

## Essential Facts (VERIFIED)

### Conservation Laws
- ✗ Mass NOT conserved
- ✗ Energy NOT conserved
- ✓ **Gradient norm CONSERVED** (||∇φ||² = constant)
- ✓ Three novel laws: φ·|∇φ|², |∇φ|³, φ·e^(-φ²)

### Topology
- ✓ Toroidal structure T² = S¹ × S¹ (visualization confirmed, rigorous proof needed)
- ✓ Time is oscillatory (dτ/dt = 1 + f(φ, ∇φ, ∇²φ))
- ✓ Gradient-dependent stabilization (e^(-|∇φ|) term)

### Nature
- ✓ Generative (not dissipative)
- ✓ Non-equilibrium (proven)
- ✓ Fully non-linear (no linear regime)

---

## Critical Rules

### 1. ALWAYS Use Adaptive Time Stepping
```python
dt_cfl = dx**2 / (2 * alpha)
dt_update = 0.5 * max(abs(phi)) / max(abs(update))
dt = min(dt_cfl, dt_update, 1.0)
```
**Fixed dt WILL cause NaN values!**

### 2. NEVER Assume Standard Results
- Don't assume mass conservation
- Don't assume energy conservation
- Don't assume linear stability analysis works
- Don't assume standard bifurcation theory applies

### 3. ALWAYS Document Open Questions
- Add to `OPEN_QUESTIONS_TRACKER.md`
- Update status as progress is made
- Verify before marking VERIFIED

### 4. ALWAYS Be Rigorous
- Prove claims or mark as conjectures
- Verify numerically
- Document limitations
- No hand-waving

---

## File Locations

### Documentation
- **Overview**: `README.md`
- **Open Questions**: `OPEN_QUESTIONS_TRACKER.md` (95 questions)
- **Standards**: `.kiro/steering/phi_equation_rigor.md`
- **Tasks**: `.kiro/specs/phi-equation-domain-analysis/tasks.md`
- **Topology**: `09_toroidal_topology_and_time.md`, `TOROIDAL_DISCOVERY.md`

### Code
- **Solver**: `phi_domain_analysis/core/equation_solver.py`
- **Fitting**: `phi_domain_analysis/core/parameter_fitting.py`
- **Metrics**: `phi_domain_analysis/core/metrics.py`
- **Visualization**: `phi_domain_analysis/core/visualization.py`

### Analysis
- **Stability**: `phi_domain_analysis/analysis/stability_analysis.py`
- **Bifurcations**: `phi_domain_analysis/analysis/bifurcation_analysis.py`
- **Conservation**: `phi_domain_analysis/analysis/conservation_laws.py`
- **Mass Study**: `phi_domain_analysis/analysis/mass_conservation_investigation.py`

### Reports
- **Mathematical**: `phi_domain_analysis/reports/01_mathematical_analysis_report.md`

---

## Current Status

**Checkpoint**: 5 Complete ✓  
**Tasks Complete**: 1-5, 6.1, 6.2, 7.1  
**Tasks In Progress**: 7.2, 8, 9, 10  
**Next Milestone**: Task 11 (Mathematical analysis checkpoint)

**Questions**:
- Total: 95
- Verified: 8 (8%)
- In Progress: 4 (4%)
- Open: 80 (84%)

---

## Quick Commands

### Run Tests
```bash
cd phi_equation_investigation/phi_domain_analysis
python tests/test_core_infrastructure.py
```

### Test Conservation Laws
```bash
python analysis/conservation_laws.py
```

### Test Mass Conservation
```bash
python analysis/mass_conservation_investigation.py
```

### Test Bifurcations
```bash
python analysis/bifurcation_analysis.py
```

### Run Solver
```python
from phi_domain_analysis.core.equation_solver import AdvancedPhiSolver

solver = AdvancedPhiSolver((64,), 1.0, 1.0, 0.5, 0.1, 1)
solver.set_initial_condition('random', amplitude=0.1)
history = solver.run(1000, save_interval=10)
```

---

## Common Pitfalls

### ❌ Using Fixed dt
```python
# WRONG - will cause NaN
for t in range(n_steps):
    phi = phi + dt * update  # Fixed dt
```

### ✓ Using Adaptive dt
```python
# CORRECT
dt = compute_adaptive_dt(phi, update, dx, alpha)
phi = phi + dt * update
```

### ❌ Assuming Mass Conservation
```python
# WRONG
assert abs(mass_final - mass_initial) < 1e-6
```

### ✓ Testing Mass Conservation
```python
# CORRECT
dM_dt = compute_mass_change_rate(phi)
# Expect dM_dt ≠ 0 in general
```

### ❌ Linear Approximation
```python
# WRONG
jacobian = compute_linear_jacobian(phi_star)
```

### ✓ Full Non-Linear
```python
# CORRECT
jacobian = compute_full_nonlinear_jacobian(phi_star)
```

---

## Key Parameters

### Typical Values
- **α**: 0.5 - 2.0 (diffusion scale)
- **β**: 0.0 - 3.0 (reaction strength)
- **γ**: 0.0 - 0.5 (gradient penalty)

### Bifurcation Example
- α=1.0, γ=0.1: Turing bifurcation at β_c ≈ 0.316

### Pattern Formation
- Requires β > α·k² for some wavenumber k
- Wavelength λ ~ 2π√(α/β)

---

## Critical Questions (Revolutionary if Answered)

1. **Can quantum mechanics be derived?** (Task 51)
2. **Can measurement be explained deterministically?** (Task 51.4)
3. **Can entanglement be explained as field correlation?** (Task 51.5)
4. **Can we rigorously prove toroidal attractor?** (Task 55)
5. **Do all physics laws emerge from this?** (Tasks 48-54)

---

## Daily Checklist

Before starting work:
- [ ] Read relevant open questions in tracker
- [ ] Review current task requirements
- [ ] Check rigor standards document
- [ ] Verify numerical stability settings

After completing work:
- [ ] Update open questions tracker
- [ ] Document any new questions discovered
- [ ] Verify results independently
- [ ] Update task status
- [ ] Commit to repository with clear message

---

## Contact & Resources

- **Repository**: https://github.com/unfurlingkurt/AramisFieldMathWork
- **Issues**: Use GitHub issues
- **Documentation**: See README.md
- **Standards**: See .kiro/steering/phi_equation_rigor.md

---

## Quick Equations

### Mass Change Rate
```
dM/dt = ∫ [-αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)] dV
```

### Gradient Norm (Conserved)
```
||∇φ||² = ∫ |∇φ|² dV = constant
```

### Intrinsic Time
```
dτ/dt = 1 + f(φ, ∇φ, ∇²φ)
```

### CFL Condition
```
dt < dx²/(2α)
```

---

**Remember**: This equation may be foundational. Investigate with appropriate rigor.
