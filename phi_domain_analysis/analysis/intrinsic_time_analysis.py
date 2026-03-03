"""
Intrinsic Time Analysis

Tests conservation laws in intrinsic time τ vs observer time t

Key Question: Are mass and energy conserved in intrinsic time even though
they're not conserved in observer time?
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
import matplotlib.pyplot as plt


def compute_intrinsic_time_rate(solver, phi):
    """
    Compute dτ/dt = 1 + f(φ, ∇φ, ∇²φ)
    
    We need to determine what f is. Possibilities:
    1. f = β·tanh(φ)·e^(-|∇φ|) (reaction term)
    2. f = -γ|∇φ|² (gradient penalty)
    3. f = combination of both
    4. f = something else entirely
    
    Let's test multiple hypotheses.
    """
    grad_phi = solver.compute_gradient_magnitude(phi)
    laplacian = solver.compute_laplacian(phi)
    
    # Hypothesis 1: Reaction term modulates time
    f1 = solver.beta * np.tanh(phi) * np.exp(-grad_phi)
    dtau_dt_1 = 1.0 + np.mean(f1)
    
    # Hypothesis 2: Gradient penalty modulates time
    f2 = -solver.gamma * grad_phi**2
    dtau_dt_2 = 1.0 + np.mean(f2)
    
    # Hypothesis 3: Both terms
    f3 = f1 + solver.alpha * f2
    dtau_dt_3 = 1.0 + np.mean(f3)
    
    # Hypothesis 4: Total update magnitude
    update = solver.alpha * (laplacian - solver.gamma * grad_phi**2) + \
             solver.beta * np.tanh(phi) * np.exp(-grad_phi)
    f4 = update
    dtau_dt_4 = 1.0 + np.mean(np.abs(f4))
    
    return {
        'reaction': dtau_dt_1,
        'gradient': dtau_dt_2,
        'combined': dtau_dt_3,
        'update': dtau_dt_4
    }


def test_mass_in_intrinsic_time(solver, n_steps=500):
    """
    Test if mass is conserved in intrinsic time
    
    In observer time: dM/dt ≠ 0
    In intrinsic time: dM/dτ = (dM/dt) / (dτ/dt)
    
    If dM/dτ = 0, then mass IS conserved in intrinsic time!
    """
    print("=" * 70)
    print("TESTING MASS CONSERVATION IN INTRINSIC TIME")
    print("=" * 70)
    print()
    
    # Track quantities
    observer_times = [0]
    intrinsic_times_h1 = [0]
    intrinsic_times_h2 = [0]
    intrinsic_times_h3 = [0]
    intrinsic_times_h4 = [0]
    
    masses = [np.sum(solver.phi) * solver.dx]
    
    # Evolve
    for step in range(n_steps):
        # Compute dτ/dt before stepping
        dtau_dt = compute_intrinsic_time_rate(solver, solver.phi)
        
        # Compute dt that will be used (same logic as in solver.step())
        lap_phi = solver.compute_laplacian(solver.phi)
        grad_mag = solver.compute_gradient_magnitude(solver.phi)
        diffusion_term = solver.alpha * (lap_phi - solver.gamma * grad_mag**2)
        reaction_term = solver.beta * np.tanh(solver.phi) * np.exp(-grad_mag)
        total_update = diffusion_term + reaction_term
        
        dt_diffusion = 0.25 * solver.dx**2 / (solver.alpha + 1e-10)
        max_update = np.max(np.abs(total_update))
        max_phi = np.max(np.abs(solver.phi)) + 1e-10
        dt_nonlinear = 0.5 * max_phi / (max_update + 1e-10)
        dt_observer = min(dt_diffusion, dt_nonlinear, 1.0)
        
        # Step in observer time
        solver.step()
        
        # Update times
        observer_times.append(observer_times[-1] + dt_observer)
        intrinsic_times_h1.append(intrinsic_times_h1[-1] + dt_observer * dtau_dt['reaction'])
        intrinsic_times_h2.append(intrinsic_times_h2[-1] + dt_observer * dtau_dt['gradient'])
        intrinsic_times_h3.append(intrinsic_times_h3[-1] + dt_observer * dtau_dt['combined'])
        intrinsic_times_h4.append(intrinsic_times_h4[-1] + dt_observer * dtau_dt['update'])
        
        # Measure mass
        masses.append(np.sum(solver.phi) * solver.dx)
    
    observer_times = np.array(observer_times)
    intrinsic_times_h1 = np.array(intrinsic_times_h1)
    intrinsic_times_h2 = np.array(intrinsic_times_h2)
    intrinsic_times_h3 = np.array(intrinsic_times_h3)
    intrinsic_times_h4 = np.array(intrinsic_times_h4)
    masses = np.array(masses)
    
    # Analyze conservation
    print("Observer Time Analysis:")
    print(f"  Initial mass: {masses[0]:.6f}")
    print(f"  Final mass: {masses[-1]:.6f}")
    print(f"  Change: {masses[-1] - masses[0]:.6f}")
    print(f"  Relative change: {abs(masses[-1] - masses[0])/abs(masses[0]):.6f}")
    print()
    
    # For intrinsic time, we need to check if M(τ) is constant
    # This is tricky because τ is not uniformly spaced
    
    # Hypothesis 1: Reaction term
    print("Intrinsic Time (Hypothesis 1: Reaction term):")
    print(f"  τ_final: {intrinsic_times_h1[-1]:.6f}")
    print(f"  τ/t ratio: {intrinsic_times_h1[-1]/observer_times[-1]:.6f}")
    # Check if dM/dτ ≈ 0
    dM_dtau_h1 = np.gradient(masses, intrinsic_times_h1)
    print(f"  Mean |dM/dτ|: {np.mean(np.abs(dM_dtau_h1)):.6f}")
    print(f"  Max |dM/dτ|: {np.max(np.abs(dM_dtau_h1)):.6f}")
    print()
    
    # Hypothesis 2: Gradient penalty
    print("Intrinsic Time (Hypothesis 2: Gradient penalty):")
    print(f"  τ_final: {intrinsic_times_h2[-1]:.6f}")
    print(f"  τ/t ratio: {intrinsic_times_h2[-1]/observer_times[-1]:.6f}")
    dM_dtau_h2 = np.gradient(masses, intrinsic_times_h2)
    print(f"  Mean |dM/dτ|: {np.mean(np.abs(dM_dtau_h2)):.6f}")
    print(f"  Max |dM/dτ|: {np.max(np.abs(dM_dtau_h2)):.6f}")
    print()
    
    # Hypothesis 3: Combined
    print("Intrinsic Time (Hypothesis 3: Combined):")
    print(f"  τ_final: {intrinsic_times_h3[-1]:.6f}")
    print(f"  τ/t ratio: {intrinsic_times_h3[-1]/observer_times[-1]:.6f}")
    dM_dtau_h3 = np.gradient(masses, intrinsic_times_h3)
    print(f"  Mean |dM/dτ|: {np.mean(np.abs(dM_dtau_h3)):.6f}")
    print(f"  Max |dM/dτ|: {np.max(np.abs(dM_dtau_h3)):.6f}")
    print()
    
    # Hypothesis 4: Update magnitude
    print("Intrinsic Time (Hypothesis 4: Update magnitude):")
    print(f"  τ_final: {intrinsic_times_h4[-1]:.6f}")
    print(f"  τ/t ratio: {intrinsic_times_h4[-1]/observer_times[-1]:.6f}")
    dM_dtau_h4 = np.gradient(masses, intrinsic_times_h4)
    print(f"  Mean |dM/dτ|: {np.mean(np.abs(dM_dtau_h4)):.6f}")
    print(f"  Max |dM/dτ|: {np.max(np.abs(dM_dtau_h4)):.6f}")
    print()
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Observer time
    axes[0, 0].plot(observer_times, masses, 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Observer time t')
    axes[0, 0].set_ylabel('Mass M')
    axes[0, 0].set_title('Mass vs Observer Time\n(NOT conserved)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Intrinsic time hypotheses
    axes[0, 1].plot(intrinsic_times_h1, masses, 'r-', linewidth=2, label='H1: Reaction')
    axes[0, 1].set_xlabel('Intrinsic time τ')
    axes[0, 1].set_ylabel('Mass M')
    axes[0, 1].set_title('Mass vs Intrinsic Time (H1)')
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].plot(intrinsic_times_h2, masses, 'g-', linewidth=2, label='H2: Gradient')
    axes[1, 0].set_xlabel('Intrinsic time τ')
    axes[1, 0].set_ylabel('Mass M')
    axes[1, 0].set_title('Mass vs Intrinsic Time (H2)')
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].plot(intrinsic_times_h3, masses, 'm-', linewidth=2, label='H3: Combined')
    axes[1, 1].set_xlabel('Intrinsic time τ')
    axes[1, 1].set_ylabel('Mass M')
    axes[1, 1].set_title('Mass vs Intrinsic Time (H3)')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('intrinsic_time_mass_conservation.png', dpi=150, bbox_inches='tight')
    print("Saved: intrinsic_time_mass_conservation.png")
    plt.show()
    
    return {
        'observer_times': observer_times,
        'intrinsic_times': {
            'h1': intrinsic_times_h1,
            'h2': intrinsic_times_h2,
            'h3': intrinsic_times_h3,
            'h4': intrinsic_times_h4
        },
        'masses': masses,
        'dM_dtau': {
            'h1': dM_dtau_h1,
            'h2': dM_dtau_h2,
            'h3': dM_dtau_h3,
            'h4': dM_dtau_h4
        }
    }


def test_alternative_mass_definitions(solver, n_steps=500):
    """
    Test if alternative mass definitions are conserved
    
    M1 = ∫ φ dV (standard)
    M2 = ∫ φ·e^(-|∇φ|) dV (gradient-weighted)
    M3 = ∫ tanh(φ) dV (bounded)
    M4 = ∫ |φ| dV (absolute)
    """
    print("=" * 70)
    print("TESTING ALTERNATIVE MASS DEFINITIONS")
    print("=" * 70)
    print()
    
    masses = {
        'standard': [],
        'gradient_weighted': [],
        'bounded': [],
        'absolute': []
    }
    
    for step in range(n_steps):
        phi = solver.phi
        grad_phi = solver.compute_gradient_magnitude(phi)
        
        # M1: Standard
        m1 = np.sum(phi) * solver.dx
        masses['standard'].append(m1)
        
        # M2: Gradient-weighted
        m2 = np.sum(phi * np.exp(-grad_phi)) * solver.dx
        masses['gradient_weighted'].append(m2)
        
        # M3: Bounded
        m3 = np.sum(np.tanh(phi)) * solver.dx
        masses['bounded'].append(m3)
        
        # M4: Absolute
        m4 = np.sum(np.abs(phi)) * solver.dx
        masses['absolute'].append(m4)
        
        solver.step()
    
    # Analyze
    for name, values in masses.items():
        values = np.array(values)
        initial = values[0]
        final = values[-1]
        change = final - initial
        if abs(initial) > 1e-10:
            rel_change = abs(change / initial)
        else:
            rel_change = abs(change)
        
        print(f"{name.upper()}:")
        print(f"  Initial: {initial:.6f}")
        print(f"  Final: {final:.6f}")
        print(f"  Change: {change:.6f}")
        print(f"  Relative change: {rel_change:.6f}")
        
        if rel_change < 0.01:
            print(f"  ✓ CONSERVED")
        else:
            print(f"  ✗ NOT conserved")
        print()
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for ax, (name, values) in zip(axes, masses.items()):
        values = np.array(values)
        normalized = values / values[0] if abs(values[0]) > 1e-10 else values
        
        ax.plot(normalized, linewidth=2)
        ax.axhline(1.0, color='r', linestyle='--', alpha=0.5)
        ax.set_xlabel('Time step')
        ax.set_ylabel('Normalized value')
        ax.set_title(f'{name.replace("_", " ").title()}')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('alternative_mass_definitions.png', dpi=150, bbox_inches='tight')
    print("Saved: alternative_mass_definitions.png")
    plt.show()


if __name__ == "__main__":
    print("INTRINSIC TIME ANALYSIS")
    print("=" * 70)
    print()
    print("Testing if conservation laws hold in intrinsic time τ")
    print("even though they don't hold in observer time t")
    print()
    
    # Create solver
    solver = AdvancedPhiSolver(
        domain_size=(64,),
        dx=1.0,
        alpha=1.0,
        beta=0.5,
        gamma=0.1,
        dim=1
    )
    
    solver.set_initial_condition('random', amplitude=0.1)
    
    # Test mass in intrinsic time
    results = test_mass_in_intrinsic_time(solver, n_steps=500)
    
    print()
    print("=" * 70)
    print()
    
    # Reset solver
    solver = AdvancedPhiSolver(
        domain_size=(64,),
        dx=1.0,
        alpha=1.0,
        beta=0.5,
        gamma=0.1,
        dim=1
    )
    
    solver.set_initial_condition('random', amplitude=0.1)
    
    # Test alternative mass definitions
    test_alternative_mass_definitions(solver, n_steps=500)
    
    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
