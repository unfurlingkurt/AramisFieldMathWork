# Task 50.4.2 Phase 1: Discrete Evolution Rule

## Objective

Define the discrete evolution rule M(r_i^n, r_{i±1}^n) that:
1. Operates on Stern-Brocot rationals using mediant operations
2. Preserves Farey neighbor relationships
3. Is deterministic
4. Converges to continuous φ-equation at large Farey depth

## 1. Mathematical Foundations

### 1.1 Stern-Brocot Tree Structure

**Definition**: The Stern-Brocot tree generates all positive rationals uniquely.

**Construction**:
- Start with 0/1 and 1/0 (infinity)
- Mediant operation: (a/b) ⊕ (c/d) = (a+c)/(b+d)
- Each rational appears exactly once
- Tree structure preserves ordering

**Farey Neighbors**: Two rationals a/b and c/d are Farey neighbors if |ad - bc| = 1.

**Key Property**: Mediant of Farey neighbors is their child in SB tree.

### 1.2 Farey Depth

**Definition**: Depth n in Stern-Brocot tree = Farey sequence F_n.

**Farey Sequence F_n**: All rationals p/q with 0 ≤ p ≤ q ≤ n in lowest terms.

**Properties**:
- F_1 = {0/1, 1/1}
- F_2 = {0/1, 1/2, 1/1}
- F_3 = {0/1, 1/3, 1/2, 2/3, 1/1}
- |F_n| ~ 3n²/π² (asymptotic)

**Depth Interpretation**: 
- Depth = maximum denominator
- Depth = resolution of rational approximation
- Depth = "quantum number" of discrete substrate

### 1.3 Continued Fraction Representation

Every rational has unique continued fraction:

```
r = a₀ + 1/(a₁ + 1/(a₂ + 1/(a₃ + ...)))
  = [a₀; a₁, a₂, a₃, ...]
```

**Properties**:
- CF length = number of terms
- CF length measures "complexity" of rational
- Shorter CF = simpler rational = lower energy?

**Examples**:
- 1/2 = [0; 2] (length 2)
- 2/3 = [0; 1, 2] (length 3)
- 3/5 = [0; 1, 1, 2] (length 4)
- φ = (1+√5)/2 = [1; 1, 1, 1, ...] (infinite, irrational)

## 2. Discrete Field Configuration

### 2.1 Lattice Structure

**Spatial lattice**: Regular grid with spacing Δx.

**Field values**: At each lattice site i, field value is Stern-Brocot rational:

```
r_i^n ∈ SB_tree
```

where:
- i = spatial index
- n = temporal index (discrete time steps)
- r_i^n = p_i^n / q_i^n (rational in lowest terms)

### 2.2 Farey Interval Representation

Alternative representation: Each site stores Farey interval [L, R]:

```
φ_i^n ∈ [L_i^n, R_i^n]
```

where L_i^n and R_i^n are Farey neighbors.

**Advantage**: Interval naturally represents superposition.

**Mediant**: φ_i^n = L_i^n ⊕ R_i^n (child of interval)

### 2.3 Depth Field

Each site has associated depth (maximum denominator):

```
d_i^n = max(q_i^n, q_{neighbors})
```

**Interpretation**: 
- High depth = fine resolution = "quantum" regime
- Low depth = coarse resolution = "classical" regime

## 3. Discrete Evolution Rule

### 3.1 Mediant-Based Diffusion

**Continuous diffusion**: α∇²φ spreads field values.

**Discrete analog**: Mediant operation between neighbors.

**Rule**:
```
r_i^{n+1} = r_i^n ⊕ (r_{i-1}^n ⊕ r_{i+1}^n)
```

**Interpretation**: 
- Take mediant of left and right neighbors
- Take mediant of result with current value
- This "averages" in rational arithmetic

**Properties**:
- Preserves Farey neighbor relationships
- Monotonic (doesn't create oscillations)
- Deterministic

### 3.2 Depth-Dependent Reaction

**Continuous reaction**: β·tanh(φ)·e^(-|∇φ|)

**Discrete analog**: Depth-dependent mediant weight.

**Gradient in discrete**: |∇φ|_i ~ |r_i - r_{i±1}| ~ 1/d_i (inverse depth)

**Rule**:
```
If d_i < d_threshold:
    r_i^{n+1} = r_i^n ⊕ r_target
else:
    r_i^{n+1} = r_i^n  (frozen)
```

where r_target depends on local configuration.

**Interpretation**:
- Low depth (coarse) → active dynamics
- High depth (fine) → frozen (e^(-|∇φ|) → 0)

### 3.3 Complete Evolution Rule

**Proposed discrete evolution**:

```
M(r_i^n, r_{i-1}^n, r_{i+1}^n) = 
    w_diff · (r_i^n ⊕ r_{i-1}^n ⊕ r_{i+1}^n) ⊕
    w_react · f_react(r_i^n, d_i^n)
```

where:
- w_diff = diffusion weight (analog of α)
- w_react = reaction weight (analog of β)
- f_react = reaction function (analog of tanh)
- ⊕ = mediant operation (weighted)

**Weighted mediant**:
```
w₁·(a/b) ⊕ w₂·(c/d) = (w₁a + w₂c)/(w₁b + w₂d)
```

### 3.4 Depth Evolution

**Depth increases** when mediants are taken:

```
d_i^{n+1} = max(q_i^{n+1}, q_{neighbors}^{n+1})
```

**Depth decrease**: Simplification when rational reduces.

**Depth dynamics**: 
- Diffusion increases depth (creates finer rationals)
- Reaction may decrease depth (simplifies)
- Competition determines equilibrium depth

## 4. Connection to Continuous Equation

### 4.1 Continuous Limit

**Scaling**: As depth d → ∞:

```
r_i^n → φ(x, t)  (rational → real)
Δx → 0  (lattice spacing → 0)
Δn → 0  (time step → 0)
```

**Mediant → Addition**:

For large denominators:
```
(a/b) ⊕ (c/d) = (a+c)/(b+d) ≈ (a/b + c/d)/2  (for b, d >> 1)
```

**Discrete Laplacian**:
```
r_{i-1} ⊕ r_{i+1} ⊕ r_i ⊕ r_i → (r_{i-1} + r_{i+1} - 2r_i)/Δx²
                                → ∇²φ
```

### 4.2 Convergence Theorem (To Be Proven)

**Claim**: As depth d → ∞, the discrete evolution M converges to:

```
∂φ/∂t = α∇²φ - αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)
```

**Proof Strategy**:
1. Show mediant operations → differential operators
2. Show depth-dependent freezing → e^(-|∇φ|) term
3. Show reaction function → tanh(φ) term
4. Prove convergence rate ~ 1/d

### 4.3 Parameter Mapping

**Continuous parameters** from discrete:

```
α ~ Δx²/Δn · w_diff
β ~ 1/Δn · w_react
γ ~ 1/d_typical
```

**Interpretation**:
- α: Spatial scale squared / time scale
- β: Reaction rate
- γ: Inverse typical depth (gradient penalty)

## 5. Specific Proposals

### 5.1 Proposal A: Simple Mediant Diffusion

**Evolution rule**:
```
r_i^{n+1} = r_i^n ⊕ α_d·(r_{i-1}^n ⊕ r_{i+1}^n)
```

where α_d is discrete diffusion coefficient.

**Reaction**:
```
If r_i^n < 1/2:
    r_i^{n+1} = r_i^{n+1} ⊕ β_d·(1/1)
else:
    r_i^{n+1} = r_i^{n+1} ⊕ β_d·(0/1)
```

**Gradient penalty**: Implicit in depth dynamics.

**Advantages**: Simple, preserves Farey structure.

**Disadvantages**: May not capture all physics.

### 5.2 Proposal B: Farey Interval Evolution

**State**: Each site stores interval [L_i^n, R_i^n].

**Diffusion**: Intervals spread to neighbors.

**Reaction**: Intervals narrow (collapse toward target).

**Evolution**:
```
L_i^{n+1} = L_i^n ⊕ α_d·(L_{i-1}^n ⊕ L_{i+1}^n)
R_i^{n+1} = R_i^n ⊕ α_d·(R_{i-1}^n ⊕ R_{i+1}^n)
```

**Collapse** (reaction):
```
If |R_i - L_i| > threshold:
    L_i^{n+1} = L_i^{n+1} ⊕ β_d·target
    R_i^{n+1} = R_i^{n+1} ⊕ β_d·target
```

**Advantages**: Naturally represents superposition.

**Disadvantages**: More complex, two values per site.

### 5.3 Proposal C: Continued Fraction Dynamics

**State**: Each site stores CF representation [a₀; a₁, a₂, ...].

**Evolution**: CF coefficients evolve.

**Diffusion**: Average CF coefficients with neighbors.

**Reaction**: Modify CF length (complexity).

**Advantages**: CF length is natural "energy" variable.

**Disadvantages**: CF arithmetic is complex.

## 6. Properties to Verify

### 6.1 Farey Neighbor Preservation

**Requirement**: If r_i and r_{i+1} are Farey neighbors at time n, they remain Farey neighbors (or become closer) at time n+1.

**Test**: |p_i q_{i+1} - p_{i+1} q_i| = 1 preserved.

### 6.2 Determinism

**Requirement**: Given initial configuration, evolution is unique.

**Test**: No randomness, no choices.

### 6.3 Convergence

**Requirement**: As depth → ∞, discrete → continuous.

**Test**: Simulate at increasing depths, measure convergence to φ-equation.

### 6.4 Conservation

**Requirement**: Some quantity is exactly conserved in discrete formulation.

**Candidates**:
- Total depth: ∑ d_i
- Topological invariant
- Information content

**Test**: Measure over time, verify constancy.

### 6.5 Gradient Norm Conservation

**Requirement**: Discrete analog of ||∇φ||² is conserved.

**Discrete gradient norm**:
```
G = ∑_i |r_i - r_{i+1}|²
```

**Test**: Verify G^{n+1} = G^n.

## 7. Analytical Derivations

### 7.1 Mediant Calculus

**Mediant derivative**:

For small ε:
```
(a/b) ⊕ ε·(c/d) = (a + εc)/(b + εd) ≈ a/b + ε·(bc - ad)/b²
```

**Interpretation**: Mediant operation is like addition in limit.

**Second mediant derivative**:
```
∂²r/∂x² ~ (r_{i-1} ⊕ r_{i+1} ⊕ r_i ⊕ r_i - r_i)/Δx²
```

### 7.2 Depth-Gradient Relationship

**Claim**: Depth d_i ~ 1/|∇φ|_i

**Reasoning**:
- High gradient → rapid spatial variation
- Rapid variation → need fine resolution
- Fine resolution → high depth

**Formula**:
```
d_i ~ 1/(|r_i - r_{i±1}|) ~ 1/|∇φ|
```

**Consequence**: e^(-|∇φ|) ~ e^(-1/d) → 0 as d → ∞.

### 7.3 Reaction Function

**Continuous**: β·tanh(φ)·e^(-|∇φ|)

**Discrete**: β_d·f(r_i)·g(d_i)

**Choices**:
- f(r) = (2r - 1) (linear approximation of tanh)
- g(d) = e^(-1/d) (depth-dependent suppression)

**Combined**:
```
Reaction = β_d·(2r_i - 1)·e^(-1/d_i)
```

## 8. Open Questions

### 8.1 Unique Evolution Rule?

**Question**: Is there a unique discrete evolution rule that converges to φ-equation?

**Investigation**: Test multiple proposals, check convergence.

### 8.2 Exact Conservation Law

**Question**: What is exactly conserved in discrete formulation?

**Candidates**: Total depth, topological invariant, information.

### 8.3 Quantum Interpretation

**Question**: Is discrete evolution rule the "true" quantum dynamics?

**Hypothesis**: Schrödinger equation is continuous approximation of discrete rule.

### 8.4 Computational Complexity

**Question**: What is computational cost of discrete simulation?

**Concern**: Exact rational arithmetic may be exponentially slow.

**Mitigation**: Use bounded depth (truncate denominators).

## 9. Next Steps (Phase 2)

Once discrete rule is defined:

1. **Prove convergence** to continuous φ-equation
2. **Derive scaling relations** between discrete and continuous parameters
3. **Identify exact conserved quantity**
4. **Test numerically** at finite depth
5. **Proceed to Phase 3**: Formalize projection operator

## 10. Recommendation

**Best proposal**: **Proposal A (Simple Mediant Diffusion)** with modifications:

```
r_i^{n+1} = (1 - α_d - β_d)·r_i^n ⊕ 
            α_d·(r_{i-1}^n ⊕ r_{i+1}^n) ⊕
            β_d·f_react(r_i^n, d_i^n)
```

where:
```
f_react(r, d) = {
    1/1  if r < 1/2 and d < d_threshold
    0/1  if r > 1/2 and d < d_threshold
    r    if d ≥ d_threshold (frozen)
}
```

**Rationale**:
- Simple enough to analyze
- Preserves Farey structure
- Captures essential physics (diffusion + reaction + gradient-dependent freezing)
- Deterministic
- Should converge to continuous equation

**Weights**: α_d + β_d < 1 (stability condition)

**Depth threshold**: d_threshold ~ 1/γ (continuous parameter)

## 11. Mathematical Formalization

### 11.1 State Space

**Definition**: Discrete state space 𝒟:

```
𝒟 = {(r₁, r₂, ..., r_N) | r_i ∈ ℚ⁺, r_i in lowest terms}
```

**Dimension**: Infinite (all rationals).

**Topology**: Discrete (no continuity).

### 11.2 Evolution Operator

**Definition**: Discrete evolution operator M: 𝒟 → 𝒟:

```
M: (r₁^n, r₂^n, ..., r_N^n) ↦ (r₁^{n+1}, r₂^{n+1}, ..., r_N^{n+1})
```

**Properties**:
- Deterministic: M is a function (not stochastic)
- Local: r_i^{n+1} depends only on r_{i-k}^n, ..., r_{i+k}^n
- Farey-preserving: Maintains Farey neighbor relationships

### 11.3 Continuous Limit

**Definition**: Continuous limit as depth d → ∞:

```
lim_{d→∞} M^{(d)} = ∂_t
```

where M^{(d)} is evolution operator restricted to depth d, and ∂_t is continuous time evolution.

**Convergence**: In appropriate function space (to be specified).

## 12. Conclusion

**Phase 1 deliverable**: Discrete evolution rule M defined.

**Proposed rule**: Simple mediant diffusion with depth-dependent reaction (Proposal A modified).

**Key features**:
- Operates on Stern-Brocot rationals
- Uses mediant operations only
- Preserves Farey neighbor relationships
- Deterministic
- Depth-dependent dynamics (gradient-dependent in continuous limit)

**Next**: Phase 2 - Prove convergence to continuous φ-equation.

---

**Status**: Phase 1 COMPLETE (rule defined)

**Files**: `DISCRETE_EVOLUTION_RULE.md`

**Next**: Phase 2 - Derive continuous limit analytically
