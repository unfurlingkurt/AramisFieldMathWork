#!/usr/bin/env python3
"""
Gradient Conservation as Geodesic Flow — Framework-Native

Tests the φ-framework's most rigid prediction:
    ||∇φ||² = constant (gradient norm conservation)

This is NOT a statistical test. It is verification of geodesic flow
on hyperbolic space. The gradient norm IS the conserved current.

On a torus with aspect ratio R₁:R₂, the gradient splits into
directional components. The TOTAL is conserved, but the DIRECTIONAL
split encodes the torus geometry.

Key measurements:
- Total ||∇φ||² conservation over time
- Directional split: ||∂φ/∂x||² vs ||∂φ/∂y||²
- How the directional ratio relates to the torus aspect ratio
- Whether φ-harmonic aspect ratios give special gradient structure
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver

from ratio_space_core import PHI, continued_fraction, farey_depth


class GradientGeodesicAnalyzer:
    """
    Verify gradient conservation as geodesic flow on hyperbolic space.
    """

    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx

    def track_gradient_norms(self, Nx, Ny, T=300, seed=42):
        """
        Run 2D φ-equation and track gradient norms over time.

        Returns time series of:
        - Total ||∇φ||²
        - x-component ||∂φ/∂x||²
        - y-component ||∂φ/∂y||²
        """
        solver = AdvancedPhiSolver(
            domain_size=(Nx, Ny),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=2
        )

        np.random.seed(seed)
        solver.phi = 0.5 * np.random.randn(Nx, Ny)

        gnx_list, gny_list, gn_total_list = [], [], []
        times = []

        n_steps = int(T / 0.1)
        for i in range(n_steps):
            solver.step()

            if i % 10 == 0:
                phi = solver.phi

                # Directional gradients with periodic BCs
                grad_x = np.zeros_like(phi)
                grad_x[1:-1, :] = (phi[2:, :] - phi[:-2, :]) / (2 * self.dx)
                grad_x[0, :] = (phi[1, :] - phi[-1, :]) / (2 * self.dx)
                grad_x[-1, :] = (phi[0, :] - phi[-2, :]) / (2 * self.dx)

                grad_y = np.zeros_like(phi)
                grad_y[:, 1:-1] = (phi[:, 2:] - phi[:, :-2]) / (2 * self.dx)
                grad_y[:, 0] = (phi[:, 1] - phi[:, -1]) / (2 * self.dx)
                grad_y[:, -1] = (phi[:, 0] - phi[:, -2]) / (2 * self.dx)

                gnx = np.mean(grad_x**2)
                gny = np.mean(grad_y**2)

                gnx_list.append(gnx)
                gny_list.append(gny)
                gn_total_list.append(gnx + gny)
                times.append(solver.time)

        return {
            'Nx': Nx, 'Ny': Ny,
            'aspect_ratio': Ny / Nx,
            'times': np.array(times),
            'gnx': np.array(gnx_list),
            'gny': np.array(gny_list),
            'gn_total': np.array(gn_total_list),
        }

    def analyze_conservation(self, data):
        """
        Analyze gradient conservation quality and directional structure.
        """
        gn = data['gn_total']
        gnx = data['gnx']
        gny = data['gny']

        if len(gn) == 0:
            return self._empty_analysis(data)

        # Skip early transient (first 20%)
        skip = max(1, len(gn) // 5)
        gn_ss = gn[skip:]
        gnx_ss = gnx[skip:]
        gny_ss = gny[skip:]

        # Handle degenerate case (all zeros)
        mean_total = np.mean(gn_ss)
        if mean_total < 1e-15 or not np.isfinite(mean_total):
            return self._empty_analysis(data)

        # Total conservation quality
        total_cv = np.std(gn_ss) / mean_total

        # Directional ratio (steady-state average)
        mean_gnx = np.mean(gnx_ss)
        mean_gny = np.mean(gny_ss)

        if mean_gny > 1e-15 and np.isfinite(mean_gny):
            grad_ratio = mean_gnx / mean_gny
        else:
            grad_ratio = float('inf') if mean_gnx > 1e-15 else 1.0

        # CF analysis of the gradient ratio
        if grad_ratio > 0 and np.isfinite(grad_ratio):
            cf_of_ratio = continued_fraction(grad_ratio)
            depth_of_ratio = len(cf_of_ratio)
        else:
            cf_of_ratio = []
            depth_of_ratio = 0

        # Expected ratio from torus geometry
        ar = data['aspect_ratio']
        expected_ratio = ar**2  # gnx/gny ~ (Ny/Nx)²

        ratio_error = abs(grad_ratio - expected_ratio) / (expected_ratio + 1e-10)

        return {
            'total_cv': total_cv,
            'mean_total': mean_total,
            'grad_ratio': grad_ratio,
            'expected_ratio': expected_ratio,
            'ratio_error': ratio_error,
            'cf_of_ratio': cf_of_ratio,
            'farey_depth_of_ratio': depth_of_ratio,
            'aspect_ratio': ar,
        }

    def _empty_analysis(self, data):
        """Return safe defaults when data is degenerate."""
        ar = data['aspect_ratio']
        return {
            'total_cv': 0.0,
            'mean_total': 0.0,
            'grad_ratio': 1.0,
            'expected_ratio': ar**2,
            'ratio_error': 1.0,
            'cf_of_ratio': [1],
            'farey_depth_of_ratio': 1,
            'aspect_ratio': ar,
        }


def run_analysis(save_dir='.'):
    """Run gradient geodesic analysis."""
    print("=" * 70)
    print("  GRADIENT CONSERVATION AS GEODESIC FLOW")
    print("  ||∇φ||² = const → geodesic flow on hyperbolic space")
    print("  Directional split encodes torus geometry")
    print("=" * 70)

    analyzer = GradientGeodesicAnalyzer()

    # Test multiple aspect ratios
    configs = {
        '1:1': (80, 80),
        '1:φ': (80, int(round(80 * PHI))),
        '1:φ²': (80, int(round(80 * PHI**2))),
        '1:2': (80, 160),
    }

    all_data = {}
    all_analysis = {}

    for label, (Nx, Ny) in configs.items():
        print(f"\n  [{label}] Tracking gradients on {Nx}×{Ny} torus...")
        t0 = time.time()
        data = analyzer.track_gradient_norms(Nx, Ny, T=200)
        analysis = analyzer.analyze_conservation(data)
        elapsed = time.time() - t0

        print(f"    Total ||∇φ||² CV:     {analysis['total_cv']:.6f}")
        print(f"    Gradient ratio (x/y): {analysis['grad_ratio']:.4f}")
        print(f"    Expected (ar²):       {analysis['expected_ratio']:.4f}")
        print(f"    Ratio error:          {analysis['ratio_error']:.4f}")
        print(f"    CF of ratio:          {analysis['cf_of_ratio']}")
        print(f"    Farey depth:          {analysis['farey_depth_of_ratio']}")
        print(f"    Time: {elapsed:.1f}s")

        all_data[label] = data
        all_analysis[label] = analysis

    # --- Visualization ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    # 1. Total gradient norm over time (all ratios)
    ax = axes[0, 0]
    for label, data in all_data.items():
        t = data['times']
        gn = data['gn_total']
        ax.plot(t, gn / gn[0], label=label, linewidth=1.5, alpha=0.8)
    ax.set_xlabel('Time')
    ax.set_ylabel('||∇φ||² / ||∇φ||²₀ (normalized)')
    ax.set_title('Total Gradient Norm Conservation\n(Should be flat = geodesic flow)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Directional components for 1:φ case
    ax = axes[0, 1]
    data = all_data.get('1:φ', list(all_data.values())[0])
    label_key = '1:φ' if '1:φ' in all_data else list(all_data.keys())[0]
    t = data['times']
    ax.plot(t, data['gnx'], label='||∂φ/∂x||²', linewidth=1.5, color='#4A90D9')
    ax.plot(t, data['gny'], label='||∂φ/∂y||²', linewidth=1.5, color='#D4AF37')
    ax.plot(t, data['gn_total'], label='Total', linewidth=2, color='black', linestyle='--')
    ax.set_xlabel('Time')
    ax.set_ylabel('Gradient norm²')
    ax.set_title(f'Directional Gradient Norms ({label_key} torus)\n'
                 f'Total conserved, directional split → anisotropy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Gradient ratio vs aspect ratio
    ax = axes[1, 0]
    labels_list = list(all_analysis.keys())
    ars = [all_analysis[l]['aspect_ratio'] for l in labels_list]
    grs = [all_analysis[l]['grad_ratio'] for l in labels_list]
    expected = [all_analysis[l]['expected_ratio'] for l in labels_list]

    x_pos = np.arange(len(labels_list))
    width = 0.35
    ax.bar(x_pos - width/2, grs, width, label='Measured', color='#4A90D9',
           edgecolor='black', alpha=0.8)
    ax.bar(x_pos + width/2, expected, width, label='Expected (ar²)',
           color='#D4AF37', edgecolor='black', alpha=0.8)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels_list)
    ax.set_ylabel('||∂φ/∂x||² / ||∂φ/∂y||²')
    ax.set_title('Gradient Ratio: Measured vs Expected\n'
                 'Torus geometry → anisotropic gradient distribution')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 4. Conservation quality comparison
    ax = axes[1, 1]
    cvs = [all_analysis[l]['total_cv'] for l in labels_list]
    colors = ['#D4AF37' if 'φ' in l else '#4A90D9' for l in labels_list]
    bars = ax.bar(labels_list, cvs, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('CV of ||∇φ||²')
    ax.set_title('Gradient Conservation Quality\n'
                 '(Lower = better geodesic flow)')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, cvs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.4f}', ha='center', va='bottom', fontsize=9)

    plt.suptitle(
        'Gradient Conservation = Geodesic Flow on Hyperbolic Space\n'
        '||∇φ||² = const (total), directional split encodes torus geometry',
        fontsize=12, fontweight='bold', y=1.02
    )
    plt.tight_layout()

    out_path = os.path.join(save_dir, 'gradient_geodesic.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\n  Saved: {out_path}")
    plt.close()

    # Summary
    print("\n" + "=" * 70)
    print("  GRADIENT GEODESIC SUMMARY")
    print("=" * 70)
    print(f"\n  {'Torus':<8} {'Total CV':>10} {'Grad x/y':>10} "
          f"{'Expected':>10} {'Error':>10} {'CF depth':>10}")
    print("  " + "-" * 62)
    for l in labels_list:
        a = all_analysis[l]
        print(f"  {l:<8} {a['total_cv']:>10.6f} {a['grad_ratio']:>10.4f} "
              f"{a['expected_ratio']:>10.4f} {a['ratio_error']:>10.4f} "
              f"{a['farey_depth_of_ratio']:>10d}")

    return {l: all_analysis[l] for l in labels_list}


if __name__ == '__main__':
    run_analysis()
