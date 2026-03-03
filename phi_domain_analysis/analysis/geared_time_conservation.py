"""
Geared Time Conservation Analysis

Tests if conservation laws hold when time is measured in discrete φ-harmonic gears
rather than continuous observer time.

Key Insight: Time is GEARED through φ-harmonic ratios, not continuous.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
import matplotlib.pyplot as plt

# Golden ratio
PHI = (1 + np.sqrt(5)) / 2

# Six temporal gears (φ-harmonic ratios)
TEMPORAL_GEARS = {
    'ultra_fast': PHI**1,      # 1.618 - Gamma waves, bond oscillations
    'fast': PHI**0,            # 1.000 - Beta waves, enzymatic reactions
    'medium': PHI**(-1),       # 0.618 - Alpha waves, cellular rhythms
    'slow': PHI**(-2),         # 0.382 - Theta waves, fluid flow
    'ultra_slow': PHI**(-3),   # 0.236 - Delta waves, organ coherence
    'quantum': PHI**(-4)       # 0.146 - Planck-scale, entanglement
}

def select_temporal_gear(phi, grad_phi, laplacian):
    """
    Select φ-harmonic temporal gear based on field state
    
    Hypothesis: Field activity determines which temporal gear the system operates in
    
    Parameters:
    -----------
    phi : ndarray
        Field configuration
    grad_phi : ndarray
        Gradient magnitude
    laplacian : ndarray
        Laplacian
        
    Returns:
    --------
    gear_ratio : float
        φ-harmonic gear ratio
    gear_name : str
        Name of selected gear
    """
    # Measure field activity (gradient magnitude)
    activity = np.mean(np.abs(grad_phi))
    
    # Measure field curvature
    curvature = np.mean(np.abs(laplacian))
    
    # Gear selection based on activity level
    # Higher activity → faster gear
    if activity > 2.0:
        return TEMPORAL_GEARS['ultra_fast'], 'ultra_fast'
    elif activity > 1.0:
        return TEMPORAL_GEARS['fast'], 'fast'
    elif activity > 0.5:
        return TEMPORAL_GEARS['medium'], 'medium'
    elif activity > 0.2:
        return TEMPORAL_GEARS['slow'], 'slow'
    elif activity > 0.1:
        return TEMPORAL_GEARS['ultra_slow'], 'ultra_slow'
    else:
        return TEMPORAL_GEARS['quantum'], 'quantum'


def test_mass_conservation_geared_time(solver, n_steps=500):
    """
    Test if mass is conserved in geared time
    
    Key hypothesis: Mass appears non-conserved in observer time because
    we're measuring in the wrong temporal frame. In geared time, it may be conserved.
    """
    print("=" * 70)
    print("MASS CONSERVATION IN GEARED TIME")
    print("=" * 70)
    print()
    print("Hypothesis: Mass is conserved when measured in φ-harmonic geared time")
    print()
    
    # Track quantities
    observer_times = [0]
    geared_times = [0]
    masses = [np.sum(solver.phi) * solver.dx]
    gear_history = []
    activity_history = []
    
    # Evolve
    for step in range(n_steps):
        # Compute field state
        grad_phi = solver.compute_gradient_magnitude(solver.phi)
        laplacian = solver.compute_laplacian(solver.phi)
        
        # Select temporal gear
        gear_ratio, gear_name = select_temporal_gear(solver.phi, grad_phi, laplacian)
        gear_history.append(gear_name)
        
        # Measure activity
        activity = np.mean(np.abs(grad_phi))
        activity_history.append(activity)
        
        # Compute dt (same logic as solver)
        dt_diffusion = 0.25 * solver.dx**2 / (solver.alpha + 1e-10)
        diffusion_term = solver.alpha * (laplacian - solver.gamma * grad_phi**2)
        reaction_term = solver.beta * np.tanh(solver.phi) * np.exp(-grad_phi)
        total_update = diffusion_term + reaction_term
        max_update = np.max(np.abs(total_update))
        max_phi = np.max(np.abs(solver.phi)) + 1e-10
        dt_nonlinear = 0.5 * max_phi / (max_update + 1e-10)
        dt_observer = min(dt_diffusion, dt_nonlinear, 1.0)
        
        # Step
        solver.step()
        
        # Update times
        observer_times.append(observer_times[-1] + dt_observer)
        geared_times.append(geared_times[-1] + dt_observer * gear_ratio)
        
        # Measure mass
        masses.append(np.sum(solver.phi) * solver.dx)
    
    observer_times = np.array(observer_times)
    geared_times = np.array(geared_times)
    masses = np.array(masses)
    activity_history = np.array(activity_history)
    
    # Analyze conservation
    print("OBSERVER TIME:")
    print(f"  Initial mass: {masses[0]:.6f}")
    print(f"  Final mass: {masses[-1]:.6f}")
    print(f"  Change: {masses[-1] - masses[0]:.6f}")
    print(f"  Relative change: {abs(masses[-1] - masses[0])/abs(masses[0]):.6f}")
    print()
    
    print("GEARED TIME:")
    print(f"  Initial τ: {geared_times[0]:.6f}")
    print(f"  Final τ: {geared_times[-1]:.6f}")
    print(f"  τ/t ratio: {geared_times[-1]/observer_times[-1]:.6f}")
    
    # Compute dM/dτ in geared time
    dM_dtau_geared = np.gradient(masses, geared_times)
    print(f"  Mean |dM/dτ|: {np.mean(np.abs(dM_dtau_geared)):.6f}")
    print(f"  Max |dM/dτ|: {np.max(np.abs(dM_dtau_geared)):.6f}")
    print()
    
    # Gear statistics
    from collections import Counter
    gear_counts = Counter(gear_history)
    print("GEAR USAGE:")
    for gear_name in ['ultra_fast', 'fast', 'medium', 'slow', 'ultra_slow', 'quantum']:
        count = gear_counts.get(gear_name, 0)
        pct = 100 * count / len(gear_history)
        print(f"  {gear_name:12s}: {count:4d} steps ({pct:5.1f}%)")
    print()
    
    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Mass vs observer time
    axes[0, 0].plot(observer_times, masses, 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Observer time t')
    axes[0, 0].set_ylabel('Mass M')
    axes[0, 0].set_title('Mass vs Observer Time\n(NOT conserved)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Mass vs geared time
    axes[0, 1].plot(geared_times, masses, 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Geared time τ')
    axes[0, 1].set_ylabel('Mass M')
    axes[0, 1].set_title('Mass vs Geared Time\n(Testing conservation)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Activity vs time
    axes[1, 0].plot(observer_times[:-1], activity_history, 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Observer time t')
    axes[1, 0].set_ylabel('Activity (mean |∇φ|)')
    axes[1, 0].set_title('Field Activity Over Time')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Gear transitions
    gear_to_num = {
        'ultra_fast': 6,
        'fast': 5,
        'medium': 4,
        'slow': 3,
        'ultra_slow': 2,
        'quantum': 1
    }
    gear_nums = [gear_to_num[g] for g in gear_history]
    axes[1, 1].plot(observer_times[:-1], gear_nums, 'k-', linewidth=1)
    axes[1, 1].set_xlabel('Observer time t')
    axes[1, 1].set_ylabel('Temporal Gear')
    axes[1, 1].set_yticks([1, 2, 3, 4, 5, 6])
    axes[1, 1].set_yticklabels(['quantum', 'ultra_slow', 'slow', 'medium', 'fast', 'ultra_fast'])
    axes[1, 1].set_title('Temporal Gear Shifts')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('geared_time_conservation.png', dpi=150, bbox_inches='tight')
    print("Saved: geared_time_conservation.png")
    plt.show()
    
    return {
        'observer_times': observer_times,
        'geared_times': geared_times,
        'masses': masses,
        'gear_history': gear_history,
        'activity_history': activity_history
    }


def test_gear_quantization(solver, n_steps=1000):
    """
    Test if temporal rate shows quantization at φ-harmonic ratios
    
    Prediction: Plot of dφ/dt vs |∇φ| should show discrete levels
    at φ-harmonic gear ratios
    """
    print("=" * 70)
    print("TESTING GEAR QUANTIZATION")
    print("=" * 70)
    print()
    print("Prediction: Temporal rate should be quantized at φ-harmonic ratios")
    print()
    
    activities = []
    temporal_rates = []
    
    for step in range(n_steps):
        # Measure activity
        grad_phi = solver.compute_gradient_magnitude(solver.phi)
        activity = np.mean(np.abs(grad_phi))
        activities.append(activity)
        
        # Measure temporal rate (magnitude of update)
        laplacian = solver.compute_laplacian(solver.phi)
        diffusion_term = solver.alpha * (laplacian - solver.gamma * grad_phi**2)
        reaction_term = solver.beta * np.tanh(solver.phi) * np.exp(-grad_phi)
        total_update = diffusion_term + reaction_term
        rate = np.mean(np.abs(total_update))
        temporal_rates.append(rate)
        
        # Step
        solver.step()
    
    activities = np.array(activities)
    temporal_rates = np.array(temporal_rates)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(activities, temporal_rates, alpha=0.3, s=10)
    
    # Add φ-harmonic reference lines
    for gear_name, gear_ratio in TEMPORAL_GEARS.items():
        ax.axhline(gear_ratio, color='r', linestyle='--', alpha=0.5, linewidth=1)
        ax.text(ax.get_xlim()[1] * 0.95, gear_ratio, f'{gear_name}\n({gear_ratio:.3f})',
               ha='right', va='center', fontsize=8, color='r')
    
    ax.set_xlabel('Activity (mean |∇φ|)')
    ax.set_ylabel('Temporal Rate (mean |dφ/dt|)')
    ax.set_title('Gear Quantization Test\n(Red lines = φ-harmonic gear ratios)')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('gear_quantization.png', dpi=150, bbox_inches='tight')
    print("Saved: gear_quantization.png")
    plt.show()
    
    print("Check plot for clustering near φ-harmonic ratios")
    print()


if __name__ == "__main__":
    print("GEARED TIME ANALYSIS")
    print("=" * 70)
    print()
    print("Testing if conservation laws hold in φ-harmonic geared time")
    print()
    print("φ-Harmonic Temporal Gears:")
    for name, ratio in TEMPORAL_GEARS.items():
        print(f"  {name:12s}: {ratio:.6f}")
    print()
    print("=" * 70)
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
    
    # Test mass conservation in geared time
    results = test_mass_conservation_geared_time(solver, n_steps=500)
    
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
    
    # Test gear quantization
    test_gear_quantization(solver, n_steps=1000)
    
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
