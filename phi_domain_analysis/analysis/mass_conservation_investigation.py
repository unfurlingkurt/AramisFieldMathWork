"""
Rigorous Investigation of Mass Conservation

The φ-equation is:
φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)

Question: Is total mass M = ∫ φ dV conserved?

Analysis:
dM/dt = ∫ dφ/dt dV
      = ∫ [α(Δφ - γ|∇φ|²) + β·tanh(φ)·e^(-|∇φ|)] dV

For periodic or zero-flux boundary conditions:
∫ Δφ dV = 0  (divergence theorem)

Therefore:
dM/dt = ∫ [-αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)] dV

Mass is conserved IF AND ONLY IF:
∫ [-αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)] dV = 0

This is NOT generally true, so mass is NOT conserved.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
import matplotlib.pyplot as plt


def analyze_mass_change_rate(solver, phi):
    """
    Compute dM/dt rigorously
    
    dM/dt = ∫ [-αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)] dV
    """
    # Compute gradient magnitude
    grad_phi = solver.compute_gradient_magnitude(phi)
    
    # Diffusion contribution (with gradient penalty)
    # ∫ Δφ dV = 0 for periodic boundaries
    # ∫ -γ|∇φ|² dV remains
    diffusion_term = -solver.alpha * solver.gamma * grad_phi**2
    
    # Reaction contribution
    reaction_term = solver.beta * np.tanh(phi) * np.exp(-grad_phi)
    
    # Total rate of mass change
    dM_dt_field = diffusion_term + reaction_term
    
    if solver.dim == 1:
        dM_dt = np.sum(dM_dt_field) * solver.dx
    elif solver.dim == 2:
        dM_dt = np.sum(dM_dt_field) * solver.dx**2
    else:
        dM_dt = np.sum(dM_dt_field) * solver.dx**3
    
    return dM_dt, diffusion_term, reaction_term


def test_mass_conservation_rigorously():
    """
    Test mass conservation with proper mathematical analysis
    """
    print("=" * 70)
    print("RIGOROUS MASS CONSERVATION ANALYSIS")
    print("=" * 70)
    print()
    
    print("Equation: φ_{t+1} = φ_t + α(Δφ - γ|∇φ|²) + β·tanh(φ)·e^(-|∇φ|)")
    print()
    print("Theoretical analysis:")
    print("  dM/dt = ∫ dφ/dt dV")
    print("        = ∫ [α(Δφ - γ|∇φ|²) + β·tanh(φ)·e^(-|∇φ|)] dV")
    print("        = ∫ [-αγ|∇φ|² + β·tanh(φ)·e^(-|∇φ|)] dV  (∫Δφ dV = 0)")
    print()
    print("Mass is conserved IFF this integral = 0 for all configurations.")
    print("This is NOT generally true.")
    print()
    print("-" * 70)
    print()
    
    # Test with different parameter sets
    test_cases = [
        {"alpha": 1.0, "beta": 0.0, "gamma": 0.1, "name": "Pure diffusion (β=0)"},
        {"alpha": 1.0, "beta": 0.5, "gamma": 0.0, "name": "No gradient penalty (γ=0)"},
        {"alpha": 1.0, "beta": 0.5, "gamma": 0.1, "name": "Standard parameters"},
        {"alpha": 1.0, "beta": 2.0, "gamma": 0.5, "name": "Strong reaction & penalty"},
    ]
    
    for case in test_cases:
        print(f"Test: {case['name']}")
        print(f"  Parameters: α={case['alpha']}, β={case['beta']}, γ={case['gamma']}")
        
        solver = AdvancedPhiSolver(
            domain_size=(64,),
            dx=1.0,
            alpha=case['alpha'],
            beta=case['beta'],
            gamma=case['gamma'],
            dim=1
        )
        
        # Set initial condition
        solver.set_initial_condition('random', amplitude=0.1)
        
        # Measure mass and dM/dt over time
        masses = []
        dM_dts = []
        times = []
        
        for step in range(100):
            # Compute current mass
            mass = np.sum(solver.phi) * solver.dx
            masses.append(mass)
            times.append(step)
            
            # Compute theoretical dM/dt
            dM_dt, diff_term, react_term = analyze_mass_change_rate(solver, solver.phi)
            dM_dts.append(dM_dt)
            
            # Evolve one step
            solver.step()
        
        masses = np.array(masses)
        dM_dts = np.array(dM_dts)
        
        # Compute actual mass change
        actual_dM = np.diff(masses)
        
        # Compare theoretical vs actual
        if len(actual_dM) > 0:
            correlation = np.corrcoef(dM_dts[:-1], actual_dM)[0, 1]
            print(f"  Initial mass: {masses[0]:.6f}")
            print(f"  Final mass: {masses[-1]:.6f}")
            print(f"  Total change: {masses[-1] - masses[0]:.6f}")
            print(f"  Mean dM/dt: {np.mean(dM_dts):.6f}")
            print(f"  Theoretical vs actual correlation: {correlation:.6f}")
            
            if np.abs(masses[-1] - masses[0]) < 1e-6:
                print(f"  ✓ Mass CONSERVED")
            else:
                print(f"  ✗ Mass NOT conserved")
        
        print()
    
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("Mass is NOT conserved in general because:")
    print("  1. Gradient penalty term: -αγ|∇φ|² removes mass")
    print("  2. Reaction term: β·tanh(φ)·e^(-|∇φ|) can add or remove mass")
    print("  3. These terms do NOT cancel in general")
    print()
    print("Special case: If β=0 AND γ=0, then dM/dt = 0 → mass conserved")
    print("              (pure diffusion with ∫Δφ dV = 0)")
    print()
    print("For γ>0 or β>0: Mass is NOT conserved.")
    print()


def visualize_mass_evolution():
    """
    Visualize mass evolution for different parameter sets
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    test_cases = [
        {"alpha": 1.0, "beta": 0.0, "gamma": 0.0, "name": "Pure diffusion"},
        {"alpha": 1.0, "beta": 0.5, "gamma": 0.0, "name": "Reaction, no penalty"},
        {"alpha": 1.0, "beta": 0.0, "gamma": 0.1, "name": "Diffusion + penalty"},
        {"alpha": 1.0, "beta": 0.5, "gamma": 0.1, "name": "Full equation"},
    ]
    
    for ax, case in zip(axes, test_cases):
        solver = AdvancedPhiSolver(
            domain_size=(64,),
            dx=1.0,
            alpha=case['alpha'],
            beta=case['beta'],
            gamma=case['gamma'],
            dim=1
        )
        
        solver.set_initial_condition('random', amplitude=0.1)
        
        masses = []
        for step in range(200):
            mass = np.sum(solver.phi) * solver.dx
            masses.append(mass)
            solver.step()
        
        masses = np.array(masses)
        normalized = masses / masses[0]
        
        ax.plot(normalized, 'b-', linewidth=2)
        ax.axhline(1.0, color='r', linestyle='--', alpha=0.5)
        ax.set_xlabel('Time step')
        ax.set_ylabel('Normalized mass')
        ax.set_title(f"{case['name']}\nα={case['alpha']}, β={case['beta']}, γ={case['gamma']}")
        ax.grid(True, alpha=0.3)
        
        # Add conservation status
        final_change = np.abs(normalized[-1] - 1.0)
        if final_change < 0.01:
            ax.text(0.05, 0.95, 'CONSERVED', transform=ax.transAxes,
                   fontsize=12, color='green', weight='bold',
                   verticalalignment='top')
        else:
            ax.text(0.05, 0.95, 'NOT CONSERVED', transform=ax.transAxes,
                   fontsize=12, color='red', weight='bold',
                   verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig('mass_conservation_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved visualization to mass_conservation_analysis.png")
    plt.show()


if __name__ == "__main__":
    test_mass_conservation_rigorously()
    print()
    visualize_mass_evolution()
