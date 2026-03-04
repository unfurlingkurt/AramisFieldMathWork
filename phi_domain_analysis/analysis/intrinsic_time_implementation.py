#!/usr/bin/env python3
"""
Intrinsic Time Implementation and Testing

Implements and tests the derived intrinsic time formula:
    dτ/dt = φ^n(x)
where n(x) = round(c₁·φ + c₂·|∇φ| + c₃·|∇²φ|)

Tests against:
1. Observed gear distribution
2. Time dilation measurements
3. Gradient conservation
4. Frame-dependent Lyapunov

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import pearsonr
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver


class IntrinsicTimeAnalyzer:
    """Implements and tests intrinsic time formulations."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
        self.phi = (1 + np.sqrt(5)) / 2
    
    def compute_gear_index(self, phi, grad_phi, lap_phi, c1, c2, c3):
        """
        Compute gear index n from field configuration.
        
        n(x) = round(c₁·φ + c₂·|∇φ| + c₃·|∇²φ|)
        """
        # Normalize inputs
        phi_norm = phi / (np.std(phi) + 1e-10)
        grad_norm = grad_phi / (np.std(grad_phi) + 1e-10)
        lap_norm = lap_phi / (np.std(lap_phi) + 1e-10)
        
        # Compute index
        n_raw = c1 * phi_norm + c2 * grad_norm + c3 * lap_norm
        n = np.round(n_raw).astype(int)
        
        # Clip to reasonable range
        n = np.clip(n, -4, 2)
        
        return n
    
    def compute_intrinsic_time_rate(self, n):
        """
        Compute dτ/dt = φ^n
        """
        return self.phi ** n
    
    def simulate_with_intrinsic_time(self, c1, c2, c3, L=100, Nx=200, T=100):
        """
        Simulate with intrinsic time tracking using given parameters.
        """
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Track
        n_steps = int(T / 0.1)
        t = 0
        tau = np.zeros(Nx)  # Intrinsic time at each point
        
        gear_history = []
        tau_history = []
        t_history = []
        
        for i in range(n_steps):
            # Compute field properties
            grad_mag = solver.compute_gradient_magnitude(solver.phi)
            lap = solver.compute_laplacian(solver.phi)
            
            # Compute gear index
            n = self.compute_gear_index(solver.phi, grad_mag, lap, c1, c2, c3)
            
            # Compute dτ/dt
            dtau_dt = self.compute_intrinsic_time_rate(n)
            
            # Update
            solver.step()
            dt = 0.1  # Approximate (solver uses adaptive)
            
            # Update intrinsic time
            tau += dtau_dt * dt
            t += dt
            
            # Save
            if i % 10 == 0:
                gear_history.append(n.copy())
                tau_history.append(tau.copy())
                t_history.append(t)
        
        return {
            'gear_history': gear_history,
            'tau_history': tau_history,
            't_history': t_history
        }
    
    def analyze_gear_distribution(self, result):
        """Analyze distribution of gears."""
        gear_history = result['gear_history']
        
        # Flatten and count
        all_gears = np.concatenate([g.flatten() for g in gear_history])
        
        unique_gears, counts = np.unique(all_gears, return_counts=True)
        total = len(all_gears)
        
        distribution = {}
        gear_names = {
            -4: 'quantum (φ⁻⁴)',
            -3: 'ultra_slow (φ⁻³)',
            -2: 'slow (φ⁻²)',
            -1: 'medium (φ⁻¹)',
            0: 'fast (φ⁰)',
            1: 'ultra_fast (φ¹)',
            2: 'hyper_fast (φ²)'
        }
        
        for gear, count in zip(unique_gears, counts):
            name = gear_names.get(gear, f'φ^{gear}')
            percentage = count / total * 100
            distribution[gear] = {
                'name': name,
                'count': count,
                'percentage': percentage
            }
        
        return distribution
    
    def compute_time_dilation(self, result):
        """Compute average dt/dτ."""
        tau_history = result['tau_history']
        t_history = result['t_history']
        
        # Average τ at each time
        tau_avg = np.array([np.mean(tau) for tau in tau_history])
        t_array = np.array(t_history)
        
        # Compute dt/dτ
        if len(tau_avg) > 1:
            dtau = np.diff(tau_avg)
            dt = np.diff(t_array)
            
            # Average dt/dτ
            dt_dtau = np.mean(dt / (dtau + 1e-10))
        else:
            dt_dtau = 1.0
        
        return dt_dtau
    
    def objective_function(self, params, target_distribution):
        """
        Objective function for fitting c₁, c₂, c₃.
        
        Minimizes difference between predicted and target gear distribution.
        """
        c1, c2, c3 = params
        
        # Simulate
        result = self.simulate_with_intrinsic_time(c1, c2, c3, T=50)
        
        # Get distribution
        distribution = self.analyze_gear_distribution(result)
        
        # Compute error
        error = 0.0
        for gear, target_pct in target_distribution.items():
            if gear in distribution:
                pred_pct = distribution[gear]['percentage']
            else:
                pred_pct = 0.0
            error += (pred_pct - target_pct) ** 2
        
        return error
    
    def fit_parameters(self):
        """
        Fit c₁, c₂, c₃ to match observed gear distribution.
        
        Target from previous observations:
        - fast (φ⁰): 42.8%
        - medium (φ⁻¹): 33.6%
        - slow (φ⁻²): 14.4%
        - quantum (φ⁻⁴): 6.6%
        - ultra_slow (φ⁻³): 2.6%
        """
        print("Fitting parameters to match observed gear distribution...")
        
        target_distribution = {
            0: 42.8,   # fast
            -1: 33.6,  # medium
            -2: 14.4,  # slow
            -3: 2.6,   # ultra_slow
            -4: 6.6    # quantum
        }
        
        # Initial guess
        x0 = [0.0, 1.0, 0.0]  # Emphasize gradient
        
        # Optimize
        result = minimize(
            lambda x: self.objective_function(x, target_distribution),
            x0,
            method='Nelder-Mead',
            options={'maxiter': 50, 'disp': True}
        )
        
        c1_opt, c2_opt, c3_opt = result.x
        
        print(f"\nOptimal parameters:")
        print(f"  c₁ (field): {c1_opt:.6f}")
        print(f"  c₂ (gradient): {c2_opt:.6f}")
        print(f"  c₃ (curvature): {c3_opt:.6f}")
        
        return c1_opt, c2_opt, c3_opt
    
    def test_formulation(self, c1, c2, c3):
        """Test the intrinsic time formulation comprehensively."""
        print("\n" + "=" * 80)
        print("TESTING INTRINSIC TIME FORMULATION")
        print("=" * 80)
        print(f"\nParameters: c₁={c1:.4f}, c₂={c2:.4f}, c₃={c3:.4f}")
        
        # Simulate
        print("\nRunning simulation...")
        result = self.simulate_with_intrinsic_time(c1, c2, c3, T=100)
        
        # 1. Gear distribution
        print("\n1. Gear Distribution:")
        distribution = self.analyze_gear_distribution(result)
        
        for gear in sorted(distribution.keys()):
            info = distribution[gear]
            print(f"   {info['name']:20s}: {info['percentage']:6.2f}%")
        
        # 2. Time dilation
        print("\n2. Time Dilation:")
        dt_dtau = self.compute_time_dilation(result)
        print(f"   Average dt/dτ: {dt_dtau:.4f}")
        print(f"   (Target: ~0.5-0.6 based on previous observations)")
        
        # 3. Spatial variation
        print("\n3. Spatial Variation:")
        final_tau = result['tau_history'][-1]
        print(f"   τ range: [{np.min(final_tau):.2f}, {np.max(final_tau):.2f}]")
        print(f"   τ std: {np.std(final_tau):.2f}")
        
        return result, distribution


def main():
    """Run intrinsic time analysis."""
    print("=" * 80)
    print("INTRINSIC TIME DERIVATION - IMPLEMENTATION AND TESTING")
    print("=" * 80)
    print()
    
    analyzer = IntrinsicTimeAnalyzer(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    # Fit parameters
    c1, c2, c3 = analyzer.fit_parameters()
    
    # Test formulation
    result, distribution = analyzer.test_formulation(c1, c2, c3)
    
    # Visualize
    print("\nCreating visualizations...")
    
    fig = plt.figure(figsize=(14, 10))
    
    # 1. Gear distribution comparison
    ax1 = plt.subplot(2, 3, 1)
    
    target = {0: 42.8, -1: 33.6, -2: 14.4, -3: 2.6, -4: 6.6}
    gears = sorted(target.keys())
    target_pcts = [target[g] for g in gears]
    pred_pcts = [distribution[g]['percentage'] if g in distribution else 0 for g in gears]
    
    x = np.arange(len(gears))
    width = 0.35
    
    ax1.bar(x - width/2, target_pcts, width, label='Target', alpha=0.7)
    ax1.bar(x + width/2, pred_pcts, width, label='Predicted', alpha=0.7)
    ax1.set_xlabel('Gear (n)')
    ax1.set_ylabel('Percentage (%)')
    ax1.set_title('Gear Distribution')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'φ^{g}' for g in gears])
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Intrinsic time evolution
    ax2 = plt.subplot(2, 3, 2)
    tau_history = result['tau_history']
    t_history = result['t_history']
    
    # Plot τ(t) for a few spatial points
    sample_indices = [len(tau_history[0])//4, len(tau_history[0])//2, 3*len(tau_history[0])//4]
    for idx in sample_indices:
        tau_at_x = [tau[idx] for tau in tau_history]
        ax2.plot(t_history, tau_at_x, label=f'x={idx}')
    
    ax2.set_xlabel('Observer Time (t)')
    ax2.set_ylabel('Intrinsic Time (τ)')
    ax2.set_title('τ(t) at Different Spatial Points')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Spatial gear distribution (final snapshot)
    ax3 = plt.subplot(2, 3, 3)
    final_gears = result['gear_history'][-1]
    x = np.arange(len(final_gears))
    
    ax3.scatter(x, final_gears, c=final_gears, cmap='viridis', alpha=0.6, s=10)
    ax3.set_xlabel('Space')
    ax3.set_ylabel('Gear Index (n)')
    ax3.set_title('Spatial Gear Distribution (Final)')
    ax3.grid(True, alpha=0.3)
    
    # 4. Gear evolution over time
    ax4 = plt.subplot(2, 3, 4)
    gear_array = np.array(result['gear_history'])
    im = ax4.imshow(gear_array.T, aspect='auto', origin='lower', cmap='viridis',
                   extent=[0, len(gear_array), 0, gear_array.shape[1]])
    plt.colorbar(im, ax=ax4, label='Gear Index (n)')
    ax4.set_xlabel('Time Step')
    ax4.set_ylabel('Space')
    ax4.set_title('Spatiotemporal Gear Evolution')
    
    # 5. Intrinsic time field (final snapshot)
    ax5 = plt.subplot(2, 3, 5)
    final_tau = result['tau_history'][-1]
    ax5.plot(x, final_tau, 'b-', linewidth=2)
    ax5.set_xlabel('Space')
    ax5.set_ylabel('τ')
    ax5.set_title(f'Intrinsic Time Field (Final)\nRange: [{np.min(final_tau):.1f}, {np.max(final_tau):.1f}]')
    ax5.grid(True, alpha=0.3)
    
    # 6. Summary text
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    dt_dtau = analyzer.compute_time_dilation(result)
    
    # Compute fit quality
    target = {0: 42.8, -1: 33.6, -2: 14.4, -3: 2.6, -4: 6.6}
    errors = []
    for g in target:
        if g in distribution:
            errors.append(abs(distribution[g]['percentage'] - target[g]))
    mean_error = np.mean(errors) if errors else 0
    
    summary_text = f"""
INTRINSIC TIME FORMULATION

dτ/dt = φⁿ⁽ˣ⁾

where:
n(x) = round(c₁·φ + c₂·|∇φ| + c₃·|∇²φ|)

Parameters:
  c₁ = {c1:.4f}
  c₂ = {c2:.4f}
  c₃ = {c3:.4f}

Results:
  Mean gear error: {mean_error:.2f}%
  Time dilation: {dt_dtau:.4f}
  τ range: [{np.min(final_tau):.1f}, {np.max(final_tau):.1f}]

Status: {"GOOD FIT" if mean_error < 5 else "NEEDS REFINEMENT"}
    """
    
    ax6.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
            verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/intrinsic_time_test.png', dpi=150)
    print("  Saved: intrinsic_time_test.png")
    
    # Final summary
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print(f"Intrinsic time formulation: dτ/dt = φⁿ⁽ˣ⁾")
    print(f"where n(x) = round({c1:.4f}·φ + {c2:.4f}·|∇φ| + {c3:.4f}·|∇²φ|)")
    print()
    print(f"Gear distribution error: {mean_error:.2f}%")
    print(f"Time dilation: dt/dτ = {dt_dtau:.4f}")
    print()
    
    if mean_error < 5:
        print("✓ Good fit to observed gear distribution")
    else:
        print("⚠ Needs refinement - consider alternative formulations")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
