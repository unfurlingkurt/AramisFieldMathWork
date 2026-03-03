"""
Bifurcation Analysis for φ-Equation

Maps bifurcation diagram in 3D parameter space (α, β, γ).
Detects and classifies bifurcation points automatically.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
from stability_analysis import StabilityAnalyzer
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class BifurcationAnalyzer:
    """
    Analyze bifurcations in parameter space
    
    Detects Turing, Hopf, and edge bifurcations
    """
    
    def __init__(self, domain_size, dx, dim=1):
        """
        Initialize analyzer
        
        Parameters:
        -----------
        domain_size : tuple
            Size of domain
        dx : float
            Spatial step
        dim : int
            Dimension
        """
        self.domain_size = domain_size
        self.dx = dx
        self.dim = dim
        self.stability_analyzer = StabilityAnalyzer(domain_size, dx, dim)
        
    def detect_turing_bifurcation(self, alpha, beta_range, gamma, n_points=50):
        """
        Detect Turing bifurcation by varying β
        
        Parameters:
        -----------
        alpha : float
            Fixed α value
        beta_range : tuple
            (min, max) for β
        gamma : float
            Fixed γ value
        n_points : int
            Resolution
            
        Returns:
        --------
        beta_critical : float
            Critical β value where bifurcation occurs
        bifurcation_type : str
            'supercritical' or 'subcritical'
        """
        betas = np.linspace(beta_range[0], beta_range[1], n_points)
        
        pattern_amplitudes = []
        
        print(f"Detecting Turing bifurcation (α={alpha}, γ={gamma})...")
        
        for beta in betas:
            solver = AdvancedPhiSolver(self.domain_size, self.dx,
                                       alpha, beta, gamma, self.dim)
            
            # Start with small random perturbation
            solver.set_initial_condition('random', amplitude=0.01)
            
            # Evolve to steady state
            history = solver.run(500, save_interval=50)
            
            # Measure pattern amplitude
            final_state = history[-1]
            amplitude = np.std(final_state)
            pattern_amplitudes.append(amplitude)
        
        pattern_amplitudes = np.array(pattern_amplitudes)
        
        # Find critical point (where amplitude becomes non-zero)
        threshold = 0.05
        patterned = pattern_amplitudes > threshold
        
        if np.any(patterned):
            critical_idx = np.where(patterned)[0][0]
            beta_critical = betas[critical_idx]
            
            # Determine type by checking slope
            if critical_idx < len(betas) - 5:
                slope = (pattern_amplitudes[critical_idx+5] - 
                        pattern_amplitudes[critical_idx]) / (betas[critical_idx+5] - betas[critical_idx])
                bifurcation_type = 'supercritical' if slope > 0 else 'subcritical'
            else:
                bifurcation_type = 'supercritical'
        else:
            beta_critical = None
            bifurcation_type = None
        
        return beta_critical, bifurcation_type, betas, pattern_amplitudes
    
    def detect_hopf_bifurcation(self, alpha, beta, gamma_range, n_points=30):
        """
        Detect Hopf bifurcation by varying γ
        
        Looks for onset of oscillations
        
        Parameters:
        -----------
        alpha, beta : float
            Fixed parameter values
        gamma_range : tuple
            (min, max) for γ
        n_points : int
            Resolution
            
        Returns:
        --------
        gamma_critical : float
            Critical γ where oscillations begin
        frequency : float
            Oscillation frequency at bifurcation
        """
        gammas = np.linspace(gamma_range[0], gamma_range[1], n_points)
        
        oscillation_amplitudes = []
        
        print(f"Detecting Hopf bifurcation (α={alpha}, β={beta})...")
        
        for gamma in gammas:
            solver = AdvancedPhiSolver(self.domain_size, self.dx,
                                       alpha, beta, gamma, self.dim)
            
            solver.set_initial_condition('random', amplitude=0.1)
            
            # Evolve and measure temporal oscillations
            history = solver.run(200, save_interval=1)
            
            # Measure oscillation amplitude (variance over time)
            mean_field = np.array([np.mean(h) for h in history])
            osc_amplitude = np.std(mean_field)
            oscillation_amplitudes.append(osc_amplitude)
        
        oscillation_amplitudes = np.array(oscillation_amplitudes)
        
        # Find critical point
        threshold = 0.01
        oscillating = oscillation_amplitudes > threshold
        
        if np.any(oscillating):
            critical_idx = np.where(oscillating)[0][0]
            gamma_critical = gammas[critical_idx]
            
            # Estimate frequency from FFT
            solver = AdvancedPhiSolver(self.domain_size, self.dx,
                                       alpha, beta, gamma_critical, self.dim)
            solver.set_initial_condition('random', amplitude=0.1)
            history = solver.run(500, save_interval=1)
            mean_field = np.array([np.mean(h) for h in history])
            
            fft = np.fft.fft(mean_field)
            power = np.abs(fft)**2
            freqs = np.fft.fftfreq(len(mean_field))
            
            # Find dominant frequency (exclude DC)
            power[0] = 0
            peak_idx = np.argmax(power)
            frequency = np.abs(freqs[peak_idx])
        else:
            gamma_critical = None
            frequency = None
        
        return gamma_critical, frequency, gammas, oscillation_amplitudes
    
    def map_3d_bifurcation_diagram(self, alpha_range, beta_range, gamma_range,
                                   n_points=15, save_path=None):
        """
        Create 3D bifurcation diagram
        
        Maps bifurcation surfaces in (α, β, γ) space
        
        Parameters:
        -----------
        alpha_range, beta_range, gamma_range : tuple
            Parameter ranges
        n_points : int
            Resolution per dimension
        save_path : str, optional
            Path to save figure
            
        Returns:
        --------
        bifurcation_data : dict
            Dictionary with bifurcation surfaces
        """
        alphas = np.linspace(alpha_range[0], alpha_range[1], n_points)
        betas = np.linspace(beta_range[0], beta_range[1], n_points)
        gammas = np.linspace(gamma_range[0], gamma_range[1], n_points)
        
        # Store bifurcation points
        turing_points = []
        hopf_points = []
        edge_points = []
        
        print(f"Mapping 3D bifurcation diagram ({n_points}³ grid)...")
        print("This may take several minutes...")
        
        total = n_points * n_points
        count = 0
        
        # Scan (α, γ) plane, detect Turing bifurcation in β
        for i, alpha in enumerate(alphas):
            for k, gamma in enumerate(gammas):
                # Detect Turing bifurcation
                beta_crit, bif_type, _, _ = self.detect_turing_bifurcation(
                    alpha, beta_range, gamma, n_points=20
                )
                
                if beta_crit is not None:
                    turing_points.append([alpha, beta_crit, gamma])
                
                count += 1
                if count % 10 == 0:
                    print(f"  Progress: {count}/{total}")
        
        turing_points = np.array(turing_points) if turing_points else np.array([]).reshape(0, 3)
        
        print(f"Found {len(turing_points)} Turing bifurcation points")
        
        # Plot 3D bifurcation diagram
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        if len(turing_points) > 0:
            ax.scatter(turing_points[:, 0], turing_points[:, 1], turing_points[:, 2],
                      c='red', s=50, alpha=0.6, label='Turing bifurcation')
        
        ax.set_xlabel('α (diffusion)')
        ax.set_ylabel('β (reaction)')
        ax.set_zlabel('γ (gradient penalty)')
        ax.set_title('3D Bifurcation Diagram')
        ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"Saved to {save_path}")
        
        plt.show()
        
        bifurcation_data = {
            'turing_points': turing_points,
            'hopf_points': hopf_points,
            'edge_points': edge_points,
            'alpha_range': alpha_range,
            'beta_range': beta_range,
            'gamma_range': gamma_range
        }
        
        return bifurcation_data
    
    def plot_bifurcation_diagram_2d(self, alpha, gamma, beta_range,
                                    n_points=50, save_path=None):
        """
        Create 2D bifurcation diagram (β vs amplitude)
        
        Classic bifurcation diagram showing pattern amplitude vs control parameter
        
        Parameters:
        -----------
        alpha, gamma : float
            Fixed parameters
        beta_range : tuple
            Range for β (control parameter)
        n_points : int
            Resolution
        save_path : str, optional
            Path to save figure
        """
        beta_crit, bif_type, betas, amplitudes = self.detect_turing_bifurcation(
            alpha, beta_range, gamma, n_points
        )
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(betas, amplitudes, 'b-', linewidth=2)
        
        if beta_crit is not None:
            ax.axvline(beta_crit, color='r', linestyle='--', 
                      label=f'Bifurcation at β={beta_crit:.3f}')
            ax.plot(beta_crit, amplitudes[np.argmin(np.abs(betas - beta_crit))],
                   'ro', markersize=10)
        
        ax.set_xlabel('β (reaction strength)')
        ax.set_ylabel('Pattern amplitude (std)')
        ax.set_title(f'Bifurcation Diagram (α={alpha}, γ={gamma})')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"Saved to {save_path}")
        
        plt.show()
        
        return betas, amplitudes


if __name__ == "__main__":
    print("Testing BifurcationAnalyzer...")
    print()
    
    # Test 1: Detect Turing bifurcation
    print("Test 1: Turing bifurcation detection")
    print("-" * 60)
    
    analyzer = BifurcationAnalyzer((32,), dx=1.0, dim=1)
    
    alpha, gamma = 1.0, 0.1
    beta_crit, bif_type, betas, amps = analyzer.detect_turing_bifurcation(
        alpha, (0.0, 3.0), gamma, n_points=20
    )
    
    if beta_crit is not None:
        print(f"✓ Turing bifurcation detected at β_c = {beta_crit:.3f}")
        print(f"  Type: {bif_type}")
    else:
        print("  No bifurcation detected in range")
    print()
    
    # Test 2: 2D bifurcation diagram
    print("Test 2: 2D bifurcation diagram")
    print("-" * 60)
    
    analyzer.plot_bifurcation_diagram_2d(
        alpha=1.0, gamma=0.1, beta_range=(0.0, 3.0),
        n_points=30, save_path='bifurcation_diagram_2d.png'
    )
    print()
    
    # Test 3: Small 3D diagram
    print("Test 3: 3D bifurcation diagram (small)")
    print("-" * 60)
    
    analyzer_small = BifurcationAnalyzer((16,), dx=1.0, dim=1)
    
    bif_data = analyzer_small.map_3d_bifurcation_diagram(
        alpha_range=(0.5, 2.0),
        beta_range=(0.0, 3.0),
        gamma_range=(0.0, 0.5),
        n_points=5,
        save_path='bifurcation_diagram_3d.png'
    )
    
    print("✓ BifurcationAnalyzer test complete!")
