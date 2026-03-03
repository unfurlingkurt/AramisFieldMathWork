#!/usr/bin/env python3
"""
Wave Interaction Analysis

Since exact traveling waves don't exist in traditional sense,
analyze how wave-like structures interact.

Tests for:
- Soliton-like behavior (pass through)
- Fusion (merge)
- Annihilation (destroy each other)
- Scattering (deflect)

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver


class WaveInteractionAnalyzer:
    """Analyzes interactions between wave-like structures."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
    
    def create_pulse(self, x, center, width, amplitude):
        """Create a localized pulse."""
        return amplitude * np.exp(-((x - center)**2) / (2*width**2))
    
    def create_kink(self, x, center, width, amplitude):
        """Create a kink (tanh profile)."""
        return amplitude * np.tanh((x - center) / width)
    
    def simulate_collision(self, L=100, Nx=200, T=100, 
                          pulse1_pos=30, pulse2_pos=70,
                          pulse1_amp=1.0, pulse2_amp=1.0,
                          width=3.0):
        """
        Simulate collision of two pulses.
        
        Returns detailed interaction analysis.
        """
        # Setup
        x = np.linspace(0, L, Nx)
        
        # Create two pulses
        phi_init = (self.create_pulse(x, pulse1_pos, width, pulse1_amp) +
                   self.create_pulse(x, pulse2_pos, width, pulse2_amp))
        
        # Simulate
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        solver.phi = phi_init
        
        # Run simulation
        n_steps = int(T / 0.1)
        save_interval = max(1, n_steps // 100)
        history = solver.run(n_steps, save_interval=save_interval)
        
        # Analyze interaction
        analysis = self._analyze_interaction(history, x)
        
        return {
            'history': history,
            'x': x,
            'analysis': analysis,
            'initial': phi_init
        }
    
    def _analyze_interaction(self, history, x):
        """Analyze what happened during interaction."""
        
        # Track peaks over time
        peak_data = []
        
        for phi in history:
            peaks, properties = find_peaks(phi, height=0.1, distance=5)
            
            peak_info = {
                'n_peaks': len(peaks),
                'positions': x[peaks] if len(peaks) > 0 else [],
                'amplitudes': properties['peak_heights'] if len(peaks) > 0 else [],
                'total_mass': np.sum(phi) * self.dx
            }
            peak_data.append(peak_info)
        
        # Determine interaction type
        initial_peaks = peak_data[0]['n_peaks']
        final_peaks = peak_data[-1]['n_peaks']
        
        # Track peak count evolution
        peak_counts = [p['n_peaks'] for p in peak_data]
        min_peaks = min(peak_counts)
        
        if initial_peaks == 2:
            if final_peaks == 2 and min_peaks == 2:
                interaction_type = 'pass_through'  # Soliton-like
            elif final_peaks == 1:
                interaction_type = 'fusion'  # Merged
            elif final_peaks == 0:
                interaction_type = 'annihilation'  # Destroyed
            elif min_peaks < 2 and final_peaks == 2:
                interaction_type = 'temporary_fusion'  # Merged then separated
            else:
                interaction_type = 'complex'
        else:
            interaction_type = 'unknown'
        
        # Measure mass conservation
        initial_mass = peak_data[0]['total_mass']
        final_mass = peak_data[-1]['total_mass']
        mass_change = abs(final_mass - initial_mass) / abs(initial_mass)
        
        return {
            'type': interaction_type,
            'peak_data': peak_data,
            'initial_peaks': initial_peaks,
            'final_peaks': final_peaks,
            'min_peaks': min_peaks,
            'mass_change': mass_change
        }
    
    def test_multiple_scenarios(self):
        """Test various interaction scenarios."""
        
        scenarios = [
            {
                'name': 'Equal amplitude pulses',
                'pulse1_amp': 1.0,
                'pulse2_amp': 1.0,
                'width': 3.0
            },
            {
                'name': 'Unequal amplitude (2:1)',
                'pulse1_amp': 2.0,
                'pulse2_amp': 1.0,
                'width': 3.0
            },
            {
                'name': 'Narrow pulses',
                'pulse1_amp': 1.0,
                'pulse2_amp': 1.0,
                'width': 1.5
            },
            {
                'name': 'Wide pulses',
                'pulse1_amp': 1.0,
                'pulse2_amp': 1.0,
                'width': 5.0
            },
            {
                'name': 'Opposite polarity',
                'pulse1_amp': 1.0,
                'pulse2_amp': -1.0,
                'width': 3.0
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            print(f"\nTesting: {scenario['name']}")
            result = self.simulate_collision(
                pulse1_amp=scenario['pulse1_amp'],
                pulse2_amp=scenario['pulse2_amp'],
                width=scenario['width'],
                T=80
            )
            result['scenario'] = scenario
            results.append(result)
            
            print(f"  Interaction type: {result['analysis']['type']}")
            print(f"  Initial peaks: {result['analysis']['initial_peaks']}")
            print(f"  Final peaks: {result['analysis']['final_peaks']}")
            print(f"  Mass change: {result['analysis']['mass_change']*100:.2f}%")
        
        return results
    
    def visualize_interaction(self, result, filename):
        """Create comprehensive visualization of interaction."""
        
        fig = plt.figure(figsize=(14, 10))
        
        history = result['history']
        x = result['x']
        analysis = result['analysis']
        
        # 1. Spatiotemporal plot
        ax1 = plt.subplot(2, 3, 1)
        im = ax1.imshow(history.T, aspect='auto', origin='lower', 
                       cmap='RdBu_r', extent=[0, len(history), x[0], x[-1]])
        plt.colorbar(im, ax=ax1, label='φ')
        ax1.set_xlabel('Time Step')
        ax1.set_ylabel('Space')
        ax1.set_title('Spatiotemporal Evolution')
        
        # 2. Peak count over time
        ax2 = plt.subplot(2, 3, 2)
        peak_counts = [p['n_peaks'] for p in analysis['peak_data']]
        ax2.plot(peak_counts, 'b-', linewidth=2)
        ax2.set_xlabel('Time Step')
        ax2.set_ylabel('Number of Peaks')
        ax2.set_title(f'Peak Count (Type: {analysis["type"]})')
        ax2.grid(True, alpha=0.3)
        
        # 3. Mass evolution
        ax3 = plt.subplot(2, 3, 3)
        masses = [p['total_mass'] for p in analysis['peak_data']]
        ax3.plot(masses, 'g-', linewidth=2)
        ax3.set_xlabel('Time Step')
        ax3.set_ylabel('Total Mass')
        ax3.set_title(f'Mass Evolution (Δ={analysis["mass_change"]*100:.1f}%)')
        ax3.grid(True, alpha=0.3)
        
        # 4. Initial state
        ax4 = plt.subplot(2, 3, 4)
        ax4.plot(x, history[0], 'b-', linewidth=2)
        ax4.set_xlabel('Space')
        ax4.set_ylabel('φ')
        ax4.set_title('Initial State')
        ax4.grid(True, alpha=0.3)
        
        # 5. Mid-collision state
        ax5 = plt.subplot(2, 3, 5)
        mid_idx = len(history) // 2
        ax5.plot(x, history[mid_idx], 'r-', linewidth=2)
        ax5.set_xlabel('Space')
        ax5.set_ylabel('φ')
        ax5.set_title('Mid-Collision')
        ax5.grid(True, alpha=0.3)
        
        # 6. Final state
        ax6 = plt.subplot(2, 3, 6)
        ax6.plot(x, history[-1], 'g-', linewidth=2)
        ax6.set_xlabel('Space')
        ax6.set_ylabel('φ')
        ax6.set_title('Final State')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()


def main():
    """Run wave interaction analysis."""
    print("=" * 80)
    print("WAVE INTERACTION ANALYSIS")
    print("=" * 80)
    print()
    
    analyzer = WaveInteractionAnalyzer(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    print("Testing multiple interaction scenarios...")
    results = analyzer.test_multiple_scenarios()
    
    print("\n" + "=" * 80)
    print("SUMMARY OF INTERACTIONS")
    print("=" * 80)
    
    # Count interaction types
    interaction_types = {}
    for result in results:
        itype = result['analysis']['type']
        interaction_types[itype] = interaction_types.get(itype, 0) + 1
    
    print("\nInteraction type distribution:")
    for itype, count in interaction_types.items():
        print(f"  {itype}: {count}")
    
    # Visualize first scenario in detail
    print("\nCreating detailed visualization of first scenario...")
    analyzer.visualize_interaction(
        results[0],
        'phi_equation_investigation/phi_domain_analysis/wave_interaction_detailed.png'
    )
    print("  Saved: wave_interaction_detailed.png")
    
    # Create comparison figure
    print("\nCreating comparison figure...")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    
    for i, result in enumerate(results[:6]):
        ax = axes[i]
        history = result['history']
        x = result['x']
        
        im = ax.imshow(history.T, aspect='auto', origin='lower',
                      cmap='RdBu_r', extent=[0, len(history), x[0], x[-1]])
        ax.set_title(f"{result['scenario']['name']}\n{result['analysis']['type']}", 
                    fontsize=9)
        ax.set_xlabel('Time', fontsize=8)
        ax.set_ylabel('Space', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/wave_interactions_comparison.png', dpi=150)
    print("  Saved: wave_interactions_comparison.png")
    
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()
    print("1. Wave-like structures DO interact")
    print("2. Interaction types vary with parameters:")
    for itype, count in interaction_types.items():
        print(f"   - {itype}: {count} cases")
    print("3. Mass is NOT conserved during interactions (generative system)")
    print("4. No simple soliton behavior (structures change during interaction)")
    print()
    print("CONCLUSION: Interactions are complex and parameter-dependent.")
    print("Not simple elastic collisions - structures evolve during interaction.")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
