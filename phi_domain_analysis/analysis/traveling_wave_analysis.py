#!/usr/bin/env python3
"""
Traveling Wave Analysis for φ-Equation

Investigates traveling wave solutions with multi-scale temporal structure.

Key Questions:
1. Do traveling wave solutions exist?
2. What are their speeds and profiles?
3. How do they interact (soliton behavior)?
4. How does multi-scale time affect wave propagation?
5. Are wave speeds quantized by φ-harmonic ratios?

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, minimize
from scipy.signal import find_peaks, correlate
from scipy.fft import fft, fftfreq
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.equation_solver import AdvancedPhiSolver


class TravelingWaveAnalyzer:
    """Analyzes traveling wave solutions of the φ-equation."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        """
        Initialize analyzer.
        
        Parameters:
        -----------
        alpha : float
            Diffusion coefficient
        beta : float
            Reaction strength
        gamma : float
            Gradient penalty
        dx : float
            Spatial resolution
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
        
        # φ-harmonic ratios for multi-scale analysis
        self.phi = (1 + np.sqrt(5)) / 2
        self.phi_ratios = {
            'ultra_fast': self.phi,      # φ¹
            'fast': 1.0,                  # φ⁰
            'medium': 1/self.phi,         # φ⁻¹
            'slow': 1/self.phi**2,        # φ⁻²
            'ultra_slow': 1/self.phi**3,  # φ⁻³
            'quantum': 1/self.phi**4      # φ⁻⁴
        }
        
    def find_traveling_wave_1d(self, c_guess=1.0, L=50, N=200, max_iter=1000):
        """
        Find traveling wave solution φ(x - ct) in 1D.
        
        Uses moving frame transformation: ξ = x - ct
        Equation becomes: -c dφ/dξ = α d²φ/dξ² - αγ|dφ/dξ|² + β·tanh(φ)·e^(-|dφ/dξ|)
        
        Parameters:
        -----------
        c_guess : float
            Initial guess for wave speed
        L : float
            Domain size
        N : int
            Number of grid points
        max_iter : int
            Maximum iterations for solver
            
        Returns:
        --------
        dict with keys:
            'success': bool
            'wave_speed': float
            'profile': array
            'xi': array (moving frame coordinate)
            'stability': dict
        """
        xi = np.linspace(-L/2, L/2, N)
        dxi = xi[1] - xi[0]
        
        def wave_equation_residual(phi, c):
            """Compute residual of traveling wave equation."""
            # Compute derivatives using finite differences
            dphi_dxi = np.gradient(phi, dxi)
            d2phi_dxi2 = np.gradient(dphi_dxi, dxi)
            grad_mag = np.abs(dphi_dxi)
            
            # Traveling wave equation
            residual = (-c * dphi_dxi - 
                       self.alpha * d2phi_dxi2 + 
                       self.alpha * self.gamma * grad_mag**2 -
                       self.beta * np.tanh(phi) * np.exp(-grad_mag))
            
            return residual
        
        # Initial guess: tanh profile
        phi_init = np.tanh((xi) / 2)
        
        # Optimize for wave speed and profile
        def objective(params):
            """Objective function for optimization."""
            c = params[0]
            phi = params[1:]
            residual = wave_equation_residual(phi, c)
            return np.sum(residual**2)
        
        # Initial parameters
        params_init = np.concatenate([[c_guess], phi_init])
        
        # Optimize
        result = minimize(objective, params_init, method='L-BFGS-B',
                         options={'maxiter': max_iter})
        
        c_opt = result.x[0]
        phi_opt = result.x[1:]
        
        # Check stability
        stability = self._check_wave_stability(phi_opt, c_opt, xi)
        
        return {
            'success': result.success,
            'wave_speed': c_opt,
            'profile': phi_opt,
            'xi': xi,
            'stability': stability,
            'residual_norm': np.sqrt(result.fun)
        }
    
    def _check_wave_stability(self, phi, c, xi):
        """
        Check stability of traveling wave solution.
        
        Linearize around wave solution and compute eigenvalues.
        """
        dxi = xi[1] - xi[0]
        N = len(phi)
        
        # Compute derivatives
        dphi = np.gradient(phi, dxi)
        grad_mag = np.abs(dphi)
        
        # Linearization matrix (simplified)
        # Full analysis would require spectral methods
        
        # Compute local growth rates
        local_stability = (-self.alpha * self.gamma * 2 * grad_mag +
                          self.beta * (1 - np.tanh(phi)**2) * np.exp(-grad_mag))
        
        return {
            'max_growth_rate': np.max(local_stability),
            'min_growth_rate': np.min(local_stability),
            'stable': np.max(local_stability) < 0
        }
    
    def simulate_wave_propagation(self, initial_wave, T=100, Nx=200):
        """
        Simulate wave propagation and measure actual speed.
        
        Parameters:
        -----------
        initial_wave : dict
            Wave profile from find_traveling_wave_1d
        T : float
            Simulation time
        Nx : int
            Spatial grid points
            
        Returns:
        --------
        dict with measured wave properties
        """
        # Create solver
        solver = PhiEquationSolver(
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dx=self.dx
        )
        
        # Initialize with wave profile
        L = 100
        x = np.linspace(0, L, Nx)
        
        # Place wave in center
        xi_wave = initial_wave['xi']
        phi_wave = initial_wave['profile']
        
        # Interpolate to simulation grid
        phi_init = np.interp(x - L/2, xi_wave, phi_wave)
        phi_init = phi_init.reshape(Nx, 1)  # Make 2D for solver
        
        # Simulate
        result = solver.solve(
            phi_init=phi_init,
            T=T,
            save_interval=1.0
        )
        
        # Track wave position over time
        positions = []
        times = []
        
        for i, phi_t in enumerate(result['phi_history']):
            # Find wave center (maximum gradient)
            grad_mag = np.abs(np.gradient(phi_t[:, 0], self.dx))
            center_idx = np.argmax(grad_mag)
            positions.append(x[center_idx])
            times.append(result['t_history'][i])
        
        positions = np.array(positions)
        times = np.array(times)
        
        # Measure speed (linear fit)
        if len(times) > 1:
            speed_measured = np.polyfit(times, positions, 1)[0]
        else:
            speed_measured = 0.0
        
        # Analyze multi-scale temporal structure
        temporal_analysis = self._analyze_temporal_scales(result)
        
        return {
            'positions': positions,
            'times': times,
            'speed_measured': speed_measured,
            'speed_predicted': initial_wave['wave_speed'],
            'phi_history': result['phi_history'],
            'temporal_scales': temporal_analysis
        }
    
    def _analyze_temporal_scales(self, simulation_result):
        """
        Analyze multi-scale temporal structure in wave propagation.
        
        Decomposes temporal evolution into φ-harmonic frequency bands.
        """
        phi_history = simulation_result['phi_history']
        t_history = simulation_result['t_history']
        
        # Extract time series at spatial center
        Nx = phi_history[0].shape[0]
        center_idx = Nx // 2
        time_series = np.array([phi[center_idx, 0] for phi in phi_history])
        
        # Fourier analysis
        dt_mean = np.mean(np.diff(t_history))
        freqs = fftfreq(len(time_series), dt_mean)
        fft_vals = np.abs(fft(time_series))
        
        # Identify φ-harmonic frequencies
        # Base frequency from dominant peak
        positive_freqs = freqs[freqs > 0]
        positive_fft = fft_vals[freqs > 0]
        
        if len(positive_freqs) > 0:
            dominant_idx = np.argmax(positive_fft)
            f_base = positive_freqs[dominant_idx]
            
            # Check for φ-harmonic structure
            harmonic_powers = {}
            for name, ratio in self.phi_ratios.items():
                f_harmonic = f_base * ratio
                # Find power near this frequency
                freq_mask = np.abs(positive_freqs - f_harmonic) < 0.1 * f_base
                if np.any(freq_mask):
                    harmonic_powers[name] = np.max(positive_fft[freq_mask])
                else:
                    harmonic_powers[name] = 0.0
        else:
            f_base = 0.0
            harmonic_powers = {name: 0.0 for name in self.phi_ratios.keys()}
        
        return {
            'base_frequency': f_base,
            'harmonic_powers': harmonic_powers,
            'frequencies': positive_freqs,
            'power_spectrum': positive_fft
        }
    
    def test_wave_interactions(self, wave1, wave2, separation=20, T=100):
        """
        Simulate collision of two traveling waves.
        
        Tests for soliton behavior (waves pass through each other unchanged).
        
        Parameters:
        -----------
        wave1, wave2 : dict
            Wave profiles from find_traveling_wave_1d
        separation : float
            Initial separation between waves
        T : float
            Simulation time
            
        Returns:
        --------
        dict with interaction analysis
        """
        # Create solver
        solver = PhiEquationSolver(
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dx=self.dx
        )
        
        # Setup domain
        L = 150
        Nx = 300
        x = np.linspace(0, L, Nx)
        
        # Place waves
        xi1 = wave1['xi']
        phi1 = wave1['profile']
        xi2 = wave2['xi']
        phi2 = wave2['profile']
        
        # Interpolate to grid (waves moving toward each other)
        pos1 = L/2 - separation/2
        pos2 = L/2 + separation/2
        
        phi_init = (np.interp(x - pos1, xi1, phi1) +
                   np.interp(x - pos2, xi2, phi2))
        phi_init = phi_init.reshape(Nx, 1)
        
        # Simulate
        result = solver.solve(
            phi_init=phi_init,
            T=T,
            save_interval=1.0
        )
        
        # Analyze interaction
        interaction_analysis = self._analyze_interaction(result, x)
        
        return {
            'phi_history': result['phi_history'],
            't_history': result['t_history'],
            'x': x,
            'interaction': interaction_analysis
        }
    
    def _analyze_interaction(self, result, x):
        """Analyze wave interaction outcomes."""
        phi_history = result['phi_history']
        
        # Track number of peaks over time
        peak_counts = []
        peak_amplitudes = []
        
        for phi_t in phi_history:
            peaks, properties = find_peaks(phi_t[:, 0], height=0.1)
            peak_counts.append(len(peaks))
            if len(peaks) > 0:
                peak_amplitudes.append(properties['peak_heights'])
            else:
                peak_amplitudes.append([])
        
        # Determine interaction type
        initial_peaks = peak_counts[0] if len(peak_counts) > 0 else 0
        final_peaks = peak_counts[-1] if len(peak_counts) > 0 else 0
        
        if initial_peaks == 2 and final_peaks == 2:
            interaction_type = 'soliton' # Waves passed through
        elif initial_peaks == 2 and final_peaks == 1:
            interaction_type = 'fusion'  # Waves merged
        elif initial_peaks == 2 and final_peaks == 0:
            interaction_type = 'annihilation'  # Waves destroyed each other
        else:
            interaction_type = 'complex'
        
        return {
            'type': interaction_type,
            'peak_counts': peak_counts,
            'peak_amplitudes': peak_amplitudes,
            'initial_peaks': initial_peaks,
            'final_peaks': final_peaks
        }
    
    def measure_wave_speed_vs_parameters(self, alpha_range, beta_range, gamma_range):
        """
        Measure wave speed as function of parameters.
        
        Tests for φ-harmonic quantization of wave speeds.
        """
        results = []
        
        for alpha in alpha_range:
            for beta in beta_range:
                for gamma in gamma_range:
                    # Update parameters
                    self.alpha = alpha
                    self.beta = beta
                    self.gamma = gamma
                    
                    # Find wave
                    wave = self.find_traveling_wave_1d(c_guess=1.0)
                    
                    if wave['success']:
                        results.append({
                            'alpha': alpha,
                            'beta': beta,
                            'gamma': gamma,
                            'speed': wave['wave_speed'],
                            'stable': wave['stability']['stable']
                        })
        
        return results


def main():
    """Run comprehensive traveling wave analysis."""
    print("=" * 80)
    print("TRAVELING WAVE ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = TravelingWaveAnalyzer(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    print("1. Finding traveling wave solution...")
    wave = analyzer.find_traveling_wave_1d(c_guess=1.0, L=50, N=200)
    
    print(f"   Success: {wave['success']}")
    print(f"   Wave speed: {wave['wave_speed']:.4f}")
    print(f"   Residual norm: {wave['residual_norm']:.6f}")
    print(f"   Stable: {wave['stability']['stable']}")
    print(f"   Max growth rate: {wave['stability']['max_growth_rate']:.6f}")
    print()
    
    # Visualize wave profile
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(wave['xi'], wave['profile'], 'b-', linewidth=2)
    plt.xlabel('ξ = x - ct')
    plt.ylabel('φ(ξ)')
    plt.title(f'Traveling Wave Profile (c = {wave["wave_speed"]:.4f})')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    dphi = np.gradient(wave['profile'], wave['xi'][1] - wave['xi'][0])
    plt.plot(wave['xi'], dphi, 'r-', linewidth=2)
    plt.xlabel('ξ = x - ct')
    plt.ylabel('dφ/dξ')
    plt.title('Wave Gradient')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/traveling_wave_profile.png', dpi=150)
    print("   Saved: traveling_wave_profile.png")
    print()
    
    print("2. Simulating wave propagation...")
    propagation = analyzer.simulate_wave_propagation(wave, T=50, Nx=200)
    
    print(f"   Predicted speed: {propagation['speed_predicted']:.4f}")
    print(f"   Measured speed: {propagation['speed_measured']:.4f}")
    print(f"   Relative error: {abs(propagation['speed_measured'] - propagation['speed_predicted'])/abs(propagation['speed_predicted'])*100:.2f}%")
    print()
    
    # Analyze temporal scales
    temporal = propagation['temporal_scales']
    print("   Multi-scale temporal analysis:")
    print(f"   Base frequency: {temporal['base_frequency']:.6f}")
    print("   φ-harmonic powers:")
    for name, power in temporal['harmonic_powers'].items():
        print(f"      {name:12s}: {power:.6f}")
    print()
    
    # Visualize propagation
    plt.figure(figsize=(14, 10))
    
    # Spatiotemporal plot
    plt.subplot(2, 2, 1)
    phi_array = np.array([phi[:, 0] for phi in propagation['phi_history']])
    plt.imshow(phi_array.T, aspect='auto', origin='lower', cmap='RdBu_r',
              extent=[propagation['times'][0], propagation['times'][-1], 0, 100])
    plt.colorbar(label='φ')
    plt.xlabel('Time')
    plt.ylabel('Space')
    plt.title('Wave Propagation')
    
    # Wave position vs time
    plt.subplot(2, 2, 2)
    plt.plot(propagation['times'], propagation['positions'], 'b-', linewidth=2)
    # Linear fit
    if len(propagation['times']) > 1:
        fit = np.polyfit(propagation['times'], propagation['positions'], 1)
        plt.plot(propagation['times'], np.polyval(fit, propagation['times']), 
                'r--', label=f'Fit: v = {fit[0]:.4f}')
    plt.xlabel('Time')
    plt.ylabel('Wave Position')
    plt.title('Wave Speed Measurement')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Temporal power spectrum
    plt.subplot(2, 2, 3)
    freqs = temporal['frequencies']
    power = temporal['power_spectrum']
    plt.semilogy(freqs, power, 'b-', alpha=0.7)
    # Mark φ-harmonic frequencies
    f_base = temporal['base_frequency']
    for name, ratio in analyzer.phi_ratios.items():
        f_harm = f_base * ratio
        if f_harm > 0 and f_harm < np.max(freqs):
            plt.axvline(f_harm, color='r', linestyle='--', alpha=0.5, linewidth=1)
    plt.xlabel('Frequency')
    plt.ylabel('Power')
    plt.title('Temporal Power Spectrum')
    plt.grid(True, alpha=0.3)
    
    # φ-harmonic power distribution
    plt.subplot(2, 2, 4)
    names = list(temporal['harmonic_powers'].keys())
    powers = list(temporal['harmonic_powers'].values())
    plt.bar(range(len(names)), powers, color='steelblue', alpha=0.7)
    plt.xticks(range(len(names)), names, rotation=45, ha='right')
    plt.ylabel('Power')
    plt.title('φ-Harmonic Power Distribution')
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/wave_propagation_analysis.png', dpi=150)
    print("   Saved: wave_propagation_analysis.png")
    print()
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
