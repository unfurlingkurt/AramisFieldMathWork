#!/usr/bin/env python3
"""
Solution Classification for φ-Equation

Catalogs all solution types:
1. Fixed points
2. Limit cycles
3. Chaos
4. Patterns
5. Basins of attraction
6. Lyapunov exponents

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.fft import fft, fftfreq
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver


class SolutionClassifier:
    """Classifies solution types of the φ-equation."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
    
    def find_fixed_points(self):
        """
        Find fixed points: φ where dφ/dt = 0.
        
        For 1D: α(Δφ - γ|∇φ|²) + β·tanh(φ)·e^(-|∇φ|) = 0
        """
        print("Finding fixed points...")
        
        # Uniform states: ∇φ = 0, Δφ = 0
        # Equation becomes: β·tanh(φ) = 0
        # Solutions: φ = 0 (always), φ = ±∞ (if tanh saturates)
        
        fixed_points = [
            {'type': 'uniform', 'value': 0.0, 'name': 'Zero state'}
        ]
        
        print(f"  Found {len(fixed_points)} uniform fixed points")
        
        # Test stability of zero state
        print("\n  Testing stability of zero state...")
        solver = AdvancedPhiSolver(
            domain_size=(100,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        # Small perturbation
        solver.phi = 0.01 * np.random.randn(100)
        initial_norm = np.linalg.norm(solver.phi)
        
        # Evolve
        for i in range(1000):
            solver.step()
        
        final_norm = np.linalg.norm(solver.phi)
        
        if final_norm < initial_norm:
            stability = 'stable'
        elif final_norm > 10 * initial_norm:
            stability = 'unstable'
        else:
            stability = 'marginal'
        
        print(f"    Initial norm: {initial_norm:.6f}")
        print(f"    Final norm: {final_norm:.6f}")
        print(f"    Stability: {stability}")
        
        fixed_points[0]['stability'] = stability
        
        return fixed_points
    
    def detect_limit_cycles(self, L=50, Nx=100, T=200):
        """
        Detect limit cycles (periodic solutions).
        
        Uses Fourier analysis to identify periodicity.
        """
        print("\nDetecting limit cycles...")
        
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        # Random initial condition
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Evolve and record
        n_steps = int(T / 0.1)
        center_idx = Nx // 2
        time_series = []
        
        for i in range(n_steps):
            solver.step()
            time_series.append(solver.phi[center_idx])
        
        time_series = np.array(time_series)
        
        # Fourier analysis
        fft_vals = np.abs(fft(time_series))
        freqs = fftfreq(len(time_series), 0.1)
        
        # Find peaks in power spectrum
        positive_mask = freqs > 0
        positive_freqs = freqs[positive_mask]
        positive_fft = fft_vals[positive_mask]
        
        peaks, properties = find_peaks(positive_fft, height=np.max(positive_fft) * 0.1)
        
        if len(peaks) > 0:
            dominant_freq = positive_freqs[peaks[0]]
            period = 1.0 / dominant_freq if dominant_freq > 0 else np.inf
            
            print(f"  Dominant frequency: {dominant_freq:.6f}")
            print(f"  Period: {period:.2f}")
            print(f"  Number of peaks: {len(peaks)}")
            
            has_limit_cycle = len(peaks) > 0 and period < T
        else:
            print("  No clear periodicity detected")
            has_limit_cycle = False
            dominant_freq = 0.0
            period = np.inf
        
        return {
            'has_limit_cycle': has_limit_cycle,
            'dominant_freq': dominant_freq,
            'period': period,
            'time_series': time_series,
            'freqs': positive_freqs,
            'power_spectrum': positive_fft
        }
    
    def compute_lyapunov_exponent(self, L=50, Nx=100, T=100):
        """
        Compute largest Lyapunov exponent.
        
        Positive → chaos
        Zero → marginal
        Negative → stable
        """
        print("\nComputing Lyapunov exponent...")
        
        # Setup two nearby initial conditions
        solver1 = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        solver2 = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        np.random.seed(42)
        phi0 = 0.5 * np.random.randn(Nx)
        
        solver1.phi = phi0.copy()
        solver2.phi = phi0 + 1e-8 * np.random.randn(Nx)
        
        # Track separation
        n_steps = int(T / 0.1)
        log_separations = []
        times = []
        
        for i in range(n_steps):
            solver1.step()
            solver2.step()
            
            # Compute separation
            separation = np.linalg.norm(solver2.phi - solver1.phi)
            
            if separation > 1e-6:  # Avoid log of very small numbers
                log_separations.append(np.log(separation))
                times.append(i * 0.1)
                
                # Renormalize to prevent overflow
                if separation > 0.1:
                    solver2.phi = solver1.phi + 1e-8 * (solver2.phi - solver1.phi) / separation
        
        # Compute Lyapunov exponent from slope
        if len(log_separations) > 10:
            lyapunov = np.polyfit(times, log_separations, 1)[0]
        else:
            lyapunov = 0.0
        
        print(f"  Largest Lyapunov exponent: {lyapunov:.6f}")
        
        if lyapunov > 0.01:
            classification = 'chaotic'
        elif lyapunov < -0.01:
            classification = 'stable'
        else:
            classification = 'marginal'
        
        print(f"  Classification: {classification}")
        
        return {
            'lyapunov': lyapunov,
            'classification': classification,
            'times': times,
            'log_separations': log_separations
        }
    
    def classify_patterns(self, L=100, Nx=200, T=100):
        """
        Classify spatial patterns that emerge.
        """
        print("\nClassifying spatial patterns...")
        
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        # Random initial condition
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Evolve
        n_steps = int(T / 0.1)
        for i in range(n_steps):
            solver.step()
        
        # Analyze final pattern
        phi_final = solver.phi
        
        # Spatial Fourier analysis
        fft_spatial = np.abs(fft(phi_final))
        k_vals = fftfreq(Nx, self.dx)
        
        positive_mask = k_vals > 0
        positive_k = k_vals[positive_mask]
        positive_fft = fft_spatial[positive_mask]
        
        # Find dominant wavelength
        peaks, _ = find_peaks(positive_fft, height=np.max(positive_fft) * 0.1)
        
        if len(peaks) > 0:
            dominant_k = positive_k[peaks[0]]
            wavelength = 2 * np.pi / dominant_k if dominant_k > 0 else np.inf
            
            print(f"  Dominant wavenumber: {dominant_k:.6f}")
            print(f"  Dominant wavelength: {wavelength:.2f}")
            
            # Classify pattern type
            if len(peaks) == 1:
                pattern_type = 'periodic'
            elif len(peaks) > 1:
                pattern_type = 'multi-scale'
            else:
                pattern_type = 'uniform'
        else:
            print("  No clear spatial pattern")
            pattern_type = 'disordered'
            wavelength = np.inf
            dominant_k = 0.0
        
        # Count peaks in real space
        real_peaks, _ = find_peaks(phi_final, height=np.mean(phi_final))
        n_peaks = len(real_peaks)
        
        print(f"  Pattern type: {pattern_type}")
        print(f"  Number of peaks: {n_peaks}")
        
        return {
            'pattern_type': pattern_type,
            'wavelength': wavelength,
            'dominant_k': dominant_k,
            'n_peaks': n_peaks,
            'phi_final': phi_final,
            'k_vals': positive_k,
            'power_spectrum': positive_fft
        }
    
    def create_solution_taxonomy(self):
        """Create complete taxonomy of solutions."""
        print("\n" + "=" * 80)
        print("CREATING SOLUTION TAXONOMY")
        print("=" * 80)
        
        taxonomy = {}
        
        # 1. Fixed points
        taxonomy['fixed_points'] = self.find_fixed_points()
        
        # 2. Limit cycles
        taxonomy['limit_cycles'] = self.detect_limit_cycles()
        
        # 3. Chaos
        taxonomy['chaos'] = self.compute_lyapunov_exponent()
        
        # 4. Patterns
        taxonomy['patterns'] = self.classify_patterns()
        
        return taxonomy


def main():
    """Run solution classification."""
    print("=" * 80)
    print("SOLUTION CLASSIFICATION - φ-Equation")
    print("=" * 80)
    print()
    
    classifier = SolutionClassifier(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    # Create complete taxonomy
    taxonomy = classifier.create_solution_taxonomy()
    
    # Visualize results
    print("\nCreating visualizations...")
    
    fig = plt.figure(figsize=(14, 10))
    
    # 1. Limit cycle time series
    ax1 = plt.subplot(2, 3, 1)
    lc = taxonomy['limit_cycles']
    ax1.plot(lc['time_series'], 'b-', linewidth=1, alpha=0.7)
    ax1.set_xlabel('Time Step')
    ax1.set_ylabel('φ(center)')
    ax1.set_title(f'Time Series\n(Period: {lc["period"]:.1f})')
    ax1.grid(True, alpha=0.3)
    
    # 2. Limit cycle power spectrum
    ax2 = plt.subplot(2, 3, 2)
    ax2.semilogy(lc['freqs'], lc['power_spectrum'], 'b-', linewidth=1.5)
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Power')
    ax2.set_title('Temporal Power Spectrum')
    ax2.grid(True, alpha=0.3)
    
    # 3. Lyapunov exponent
    ax3 = plt.subplot(2, 3, 3)
    chaos = taxonomy['chaos']
    if len(chaos['times']) > 0:
        ax3.plot(chaos['times'], chaos['log_separations'], 'r-', linewidth=2)
        # Fit line
        if len(chaos['times']) > 1:
            fit = np.polyfit(chaos['times'], chaos['log_separations'], 1)
            ax3.plot(chaos['times'], np.polyval(fit, chaos['times']), 'k--',
                    label=f'λ = {fit[0]:.4f}')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('log(separation)')
    ax3.set_title(f'Lyapunov Exponent\n({chaos["classification"]})')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Final spatial pattern
    ax4 = plt.subplot(2, 3, 4)
    patterns = taxonomy['patterns']
    x = np.arange(len(patterns['phi_final'])) * classifier.dx
    ax4.plot(x, patterns['phi_final'], 'g-', linewidth=2)
    ax4.set_xlabel('Space')
    ax4.set_ylabel('φ')
    ax4.set_title(f'Spatial Pattern\n({patterns["pattern_type"]})')
    ax4.grid(True, alpha=0.3)
    
    # 5. Spatial power spectrum
    ax5 = plt.subplot(2, 3, 5)
    ax5.semilogy(patterns['k_vals'], patterns['power_spectrum'], 'g-', linewidth=1.5)
    ax5.set_xlabel('Wavenumber k')
    ax5.set_ylabel('Power')
    ax5.set_title(f'Spatial Power Spectrum\n(λ = {patterns["wavelength"]:.1f})')
    ax5.grid(True, alpha=0.3)
    
    # 6. Summary text
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    summary_text = f"""
SOLUTION TAXONOMY

Fixed Points:
  • {len(taxonomy['fixed_points'])} found
  • Zero state: {taxonomy['fixed_points'][0]['stability']}

Temporal Dynamics:
  • Limit cycle: {lc['has_limit_cycle']}
  • Period: {lc['period']:.1f}
  • Lyapunov: {chaos['lyapunov']:.4f}
  • Type: {chaos['classification']}

Spatial Patterns:
  • Type: {patterns['pattern_type']}
  • Wavelength: {patterns['wavelength']:.1f}
  • Peaks: {patterns['n_peaks']}

Classification:
  {_classify_overall(taxonomy)}
    """
    
    ax6.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
            verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/solution_classification.png', dpi=150)
    print("  Saved: solution_classification.png")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SOLUTION CLASSIFICATION SUMMARY")
    print("=" * 80)
    print()
    print("1. Fixed Points:")
    for fp in taxonomy['fixed_points']:
        print(f"   • {fp['name']}: {fp['stability']}")
    
    print("\n2. Temporal Dynamics:")
    print(f"   • Limit cycles: {lc['has_limit_cycle']}")
    if lc['has_limit_cycle']:
        print(f"   • Period: {lc['period']:.2f}")
    print(f"   • Lyapunov exponent: {chaos['lyapunov']:.6f}")
    print(f"   • Classification: {chaos['classification']}")
    
    print("\n3. Spatial Patterns:")
    print(f"   • Type: {patterns['pattern_type']}")
    print(f"   • Wavelength: {patterns['wavelength']:.2f}")
    print(f"   • Number of peaks: {patterns['n_peaks']}")
    
    print("\n4. Overall Classification:")
    print(f"   {_classify_overall(taxonomy)}")
    
    print("\n" + "=" * 80)


def _classify_overall(taxonomy):
    """Classify overall solution behavior."""
    chaos = taxonomy['chaos']
    patterns = taxonomy['patterns']
    lc = taxonomy['limit_cycles']
    
    if chaos['lyapunov'] > 0.01:
        return "Chaotic dynamics with spatial patterns"
    elif lc['has_limit_cycle']:
        return "Periodic oscillations with spatial structure"
    elif patterns['pattern_type'] == 'periodic':
        return "Stationary periodic patterns"
    elif patterns['pattern_type'] == 'multi-scale':
        return "Complex multi-scale patterns"
    else:
        return "Disordered/transient dynamics"


if __name__ == '__main__':
    main()
