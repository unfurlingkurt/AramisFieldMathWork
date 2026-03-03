# Equation Specification

## Core Equation

```
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
```

## Parameter Space

- **φ_t**: Field variable at time t (scalar field in n-dimensional space)
- **α**: Diffusion coefficient (controls spatial smoothing strength)
- **γ**: Gradient penalty coefficient (edge preservation parameter)
- **β**: Reaction strength (nonlinear dynamics amplitude)
- **Δφ_t**: Laplacian operator (∇²φ)
- **∇φ_t**: Gradient operator
- **|∇φ_t|²**: Squared gradient magnitude (scalar)

## Operator Definitions

In n-dimensional space:
- Laplacian: Δφ = ∑ᵢ ∂²φ/∂xᵢ²
- Gradient: ∇φ = (∂φ/∂x₁, ∂φ/∂x₂, ..., ∂φ/∂xₙ)
- Gradient magnitude: |∇φ| = √(∑ᵢ (∂φ/∂xᵢ)²)

## Discovery Context

- Discovered over one year ago by researcher
- Known capabilities exist but require fresh analytical perspective
- No assumptions about intended application domain
- Open-minded investigation across multiple disciplines

## Investigation Goals

1. Mathematical characterization (stability, bifurcations, invariants)
2. Physical interpretations (thermodynamics, field theory, statistical mechanics)
3. Biological analogies (morphogenesis, neural dynamics, population dynamics)
4. Computational properties (numerical stability, emergent behaviors)
5. Cross-domain applications and novel insights
