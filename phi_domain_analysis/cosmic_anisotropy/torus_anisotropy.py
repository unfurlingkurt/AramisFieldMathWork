#!/usr/bin/env python3
"""
Torus Anisotropy Analysis — Depth-12 Crystallization Framework

Runs the actual phi-equation on 2D toroidal domains (periodic BCs)
with various aspect ratios. Measures everything via CF tension to
the three crystallization anchors at Farey depth 12:

    Octave  (1:2) — Loop via divisor 6
    Fifth   (2:3) — Loop via divisor 4
    Fourth  (3:4) — Loop via divisor 3

The equation:
    phi_{t+1} = phi_t + alpha(Delta phi_t - gamma|nabla phi_t|^2) + beta*tanh(phi_t)*e^{-|nabla phi_t|}

On a 2D domain with periodic BCs = T^2 = S^1(L_x) x S^1(L_y).
Aspect ratio = L_y / L_x = Ny / Nx.

Key question: Do phi-harmonic aspect ratios (1:phi, 1:phi^2) produce
structurally distinct crystallization patterns compared to other ratios?

All measurements:
- Directional impedance Z_x, Z_y (ratios, not scalars)
- CF tension to three crystallization anchors (not Euclidean distance)
- Anchor basin classification (not flat Farey intervals)
- Gradient conservation quality
- Anisotropy = difference between x and y anchor distributions
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver

from ratio_space_core import (
    PHI, ANCHORS, ANCHOR_VALUES, CRYSTALLIZATION_DEPTH,
    classify_array_by_anchor, anchor_clustering_strength,
    farey_depth, continued_fraction, tension,
)


class TorusAnisotropyAnalyzer:
    """
    Run the phi-equation on a 2D torus and measure anisotropy
    via crystallization anchor tension.
    """

    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx

    def _compute_directional_gradients(self, phi):
        """
        Compute x and y gradients with periodic BCs (torus topology).
        """
        Nx, Ny = phi.shape

        grad_x = np.zeros_like(phi)
        grad_x[1:-1, :] = (phi[2:, :] - phi[:-2, :]) / (2 * self.dx)
        grad_x[0, :] = (phi[1, :] - phi[-1, :]) / (2 * self.dx)
        grad_x[-1, :] = (phi[0, :] - phi[-2, :]) / (2 * self.dx)

        grad_y = np.zeros_like(phi)
        grad_y[:, 1:-1] = (phi[:, 2:] - phi[:, :-2]) / (2 * self.dx)
        grad_y[:, 0] = (phi[:, 1] - phi[:, -1]) / (2 * self.dx)
        grad_y[:, -1] = (phi[:, 0] - phi[:, -2]) / (2 * self.dx)

        return grad_x, grad_y

    def run_torus(self, Nx, Ny, T=200, seed=42, sample_interval=20):
        """
        Run phi-equation on Nx x Ny torus and collect data.
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

        impedances_x = []
        impedances_y = []
        grad_norms_x = []
        grad_norms_y = []
        grad_norms_total = []
        times = []

        n_steps = int(T / 0.1)
        eps = 1e-10

        for i in range(n_steps):
            phi_prev = solver.phi.copy()
            t_prev = solver.time
            solver.step()
            dt = solver.time - t_prev

            if i % sample_interval == 0 and i > 0 and dt > 1e-12:
                dphi_dt = (solver.phi - phi_prev) / dt
                grad_x, grad_y = self._compute_directional_gradients(solver.phi)

                Z_x = np.abs(grad_x) / (np.abs(dphi_dt) + eps)
                Z_y = np.abs(grad_y) / (np.abs(dphi_dt) + eps)

                impedances_x.append(Z_x)
                impedances_y.append(Z_y)

                gnx = np.mean(grad_x**2)
                gny = np.mean(grad_y**2)

                grad_norms_x.append(gnx)
                grad_norms_y.append(gny)
                grad_norms_total.append(gnx + gny)
                times.append(solver.time)

        return {
            'Nx': Nx, 'Ny': Ny,
            'aspect_ratio': Ny / Nx,
            'impedances_x': impedances_x,
            'impedances_y': impedances_y,
            'grad_norms_x': np.array(grad_norms_x),
            'grad_norms_y': np.array(grad_norms_y),
            'grad_norms_total': np.array(grad_norms_total),
            'times': np.array(times),
            'final_phi': solver.phi.copy()
        }

    def analyze_single_torus(self, sim):
        """
        Analyze a single torus simulation using crystallization anchors.
        """
        # Collect directional impedances
        Zx_all = np.concatenate([z.flatten() for z in sim['impedances_x']])
        Zy_all = np.concatenate([z.flatten() for z in sim['impedances_y']])

        # 1. Anchor classification for each direction
        anchor_x = classify_array_by_anchor(Zx_all)
        anchor_y = classify_array_by_anchor(Zy_all)

        # 2. Anchor clustering strength (combined)
        Z_combined = np.concatenate([Zx_all, Zy_all])
        clustering, mean_obs, mean_rand = anchor_clustering_strength(Z_combined)

        # 3. Gradient conservation quality
        gn_total = sim['grad_norms_total']
        mean_gn = np.mean(gn_total)
        if mean_gn > 1e-15 and np.isfinite(mean_gn):
            grad_cv = np.std(gn_total) / mean_gn
        else:
            grad_cv = 0.0

        # 4. Directional gradient ratio
        gnx = sim['grad_norms_x']
        gny = sim['grad_norms_y']
        mean_gnx = np.mean(gnx)
        mean_gny = np.mean(gny)
        if mean_gny > 1e-15 and np.isfinite(mean_gny):
            grad_ratio = mean_gnx / mean_gny
        else:
            grad_ratio = float('inf') if mean_gnx > 1e-15 else 1.0

        # 5. Anchor anisotropy: difference between x and y anchor distributions
        anchor_aniso = {}
        total_aniso = 0.0
        for name in list(ANCHORS.keys()) + ['transitional']:
            x_val = anchor_x.get(name, 0)
            y_val = anchor_y.get(name, 0)
            diff = abs(x_val - y_val)
            anchor_aniso[name] = diff
            total_aniso += diff

        # 6. Mean tensions to each anchor
        mean_tensions_x = anchor_x.get('mean_tensions', {})
        mean_tensions_y = anchor_y.get('mean_tensions', {})

        return {
            'aspect_ratio': sim['aspect_ratio'],
            'anchor_x': anchor_x,
            'anchor_y': anchor_y,
            'anchor_clustering': clustering,
            'gradient_cv': grad_cv,
            'gradient_ratio': grad_ratio,
            'anchor_anisotropy': anchor_aniso,
            'total_anchor_anisotropy': total_aniso,
            'mean_tensions_x': mean_tensions_x,
            'mean_tensions_y': mean_tensions_y,
        }

    def scan_aspect_ratios(self, base_N=80, T=150):
        """
        Scan multiple aspect ratios. Phi-harmonic ratios (1:phi, 1:phi^2)
        should show distinct crystallization patterns.
        """
        ratios = {
            '1:1': 1.0,
            '1:phi': PHI,
            '1:phi2': PHI**2,
            '1:2': 2.0,
            '1:rt2': np.sqrt(2),
        }

        all_results = {}

        for label, ratio in ratios.items():
            Nx = base_N
            Ny = max(int(round(base_N * ratio)), base_N + 1)

            print(f"\n  [{label}] Torus {Nx}x{Ny} (ratio={ratio:.4f})")
            t0 = time.time()

            sim = self.run_torus(Nx, Ny, T=T)
            analysis = self.analyze_single_torus(sim)

            elapsed = time.time() - t0

            ax = analysis['anchor_x']
            ay = analysis['anchor_y']
            print(f"    Anchor clustering:  {analysis['anchor_clustering']:.2f}x")
            print(f"    Gradient CV:        {analysis['gradient_cv']:.4f}")
            print(f"    Grad ratio (x/y):   {analysis['gradient_ratio']:.4f}")
            print(f"    Anchor anisotropy:  {analysis['total_anchor_anisotropy']:.4f}")
            print(f"    X anchors: Oct={ax['octave']:.3f} "
                  f"5th={ax['fifth']:.3f} 4th={ax['fourth']:.3f} "
                  f"Trans={ax.get('transitional',0):.3f}")
            print(f"    Y anchors: Oct={ay['octave']:.3f} "
                  f"5th={ay['fifth']:.3f} 4th={ay['fourth']:.3f} "
                  f"Trans={ay.get('transitional',0):.3f}")
            print(f"    Time: {elapsed:.1f}s")

            all_results[label] = {
                'ratio': ratio,
                'analysis': analysis,
                'simulation': sim,
            }

        return all_results


def run_analysis(save_dir='.'):
    """Run the full torus anisotropy analysis."""
    print("=" * 70)
    print("  TORUS ANISOTROPY — Depth-12 Crystallization Framework")
    print("  phi_{t+1} = phi_t + alpha(Delta phi - gamma|nabla phi|^2) + beta*tanh(phi)*e^{-|nabla phi|}")
    print("  Domain: 2D torus (periodic BCs)")
    print("  Measurement: CF tension to anchors (1:2, 2:3, 3:4)")
    print("=" * 70)

    analyzer = TorusAnisotropyAnalyzer()
    results = analyzer.scan_aspect_ratios(base_N=80, T=300)

    # --- Visualization ---
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    labels = list(results.keys())
    clusterings = [results[l]['analysis']['anchor_clustering'] for l in labels]
    grad_cvs = [results[l]['analysis']['gradient_cv'] for l in labels]
    grad_ratios = [results[l]['analysis']['gradient_ratio'] for l in labels]
    anchor_anisos = [results[l]['analysis']['total_anchor_anisotropy'] for l in labels]

    colors = []
    for l in labels:
        if 'phi' in l:
            colors.append('#D4AF37')  # Gold for phi-harmonic
        else:
            colors.append('#4A90D9')  # Blue for control

    anchor_colors = {'octave': '#4A90D9', 'fifth': '#7BC47F', 'fourth': '#D94A4A'}

    # 1. Anchor Clustering Strength
    ax = axes[0, 0]
    bars = ax.bar(labels, clusterings, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('Anchor Clustering Strength (x)')
    ax.set_title('Crystallization Anchor Clustering\n(Higher = stronger anchor preference)')
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='Random')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, clusterings):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.1f}x', ha='center', va='bottom', fontsize=9)

    # 2. Gradient Conservation
    ax = axes[0, 1]
    bars = ax.bar(labels, grad_cvs, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('CV of ||nabla phi||^2')
    ax.set_title('Gradient Norm Conservation\n(Lower = better geodesic flow)')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, grad_cvs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.3f}', ha='center', va='bottom', fontsize=9)

    # 3. Gradient Ratio x/y
    ax = axes[0, 2]
    bars = ax.bar(labels, grad_ratios, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('||d phi/dx||^2 / ||d phi/dy||^2')
    ax.set_title('Directional Gradient Ratio\n(=1 isotropic, !=1 anisotropic)')
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, grad_ratios):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val:.3f}', ha='center', va='bottom', fontsize=9)

    # 4. Anchor Basin Anisotropy
    ax = axes[1, 0]
    bars = ax.bar(labels, anchor_anisos, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('Total Anchor Anisotropy')
    ax.set_title('Crystallization Anisotropy (x vs y)\n(Difference in anchor basin fractions)')
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Anchor distribution for phi case (x vs y)
    ax = axes[1, 1]
    phi_key = '1:phi' if '1:phi' in results else labels[0]
    a = results[phi_key]['analysis']
    x_pos = np.arange(4)
    width = 0.35
    anchor_order = ['octave', 'fifth', 'fourth', 'transitional']
    x_vals = [a['anchor_x'].get(n, 0) for n in anchor_order]
    y_vals = [a['anchor_y'].get(n, 0) for n in anchor_order]

    b1 = ax.bar(x_pos - width/2, x_vals, width, color='#4A90D9', edgecolor='black',
                label='x-direction', alpha=0.8)
    b2 = ax.bar(x_pos + width/2, y_vals, width, color='#D4AF37', edgecolor='black',
                label='y-direction', alpha=0.8)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Octave\n(1:2)', 'Fifth\n(2:3)', 'Fourth\n(3:4)', 'Trans-\nitional'])
    ax.set_ylabel('Fraction')
    ax.set_title(f'Anchor Basin Distribution ({phi_key} torus)\nDepth-12 crystallization anchors')
    ax.axhline(1/3, color='gray', linestyle='--', alpha=0.5, label='1/3')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Final field snapshot for phi case
    ax = axes[1, 2]
    final_phi = results[phi_key]['simulation']['final_phi']
    im = ax.imshow(final_phi.T, cmap='RdBu_r', origin='lower', aspect='auto')
    ax.set_xlabel('x (periodic)')
    ax.set_ylabel('y (periodic)')
    Nx = results[phi_key]['simulation']['Nx']
    Ny = results[phi_key]['simulation']['Ny']
    ax.set_title(f'phi-field on {phi_key} torus ({Nx}x{Ny})\nPeriodic BCs = T^2')
    plt.colorbar(im, ax=ax, label='phi')

    plt.suptitle(
        f'Torus Anisotropy — Depth-{CRYSTALLIZATION_DEPTH} Crystallization Framework\n'
        f'Gold = phi-harmonic, Blue = control | Anchors: 1:2, 2:3, 3:4',
        fontsize=12, fontweight='bold', y=1.02
    )
    plt.tight_layout()

    out_path = os.path.join(save_dir, 'torus_anisotropy.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\n  Saved: {out_path}")
    plt.close()

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  RESULTS SUMMARY")
    print("=" * 70)

    print(f"\n  {'Ratio':<8} {'Clustering':>10} {'Grad CV':>10} "
          f"{'Grad x/y':>10} {'Aniso':>10}")
    print("  " + "-" * 52)
    for l in labels:
        a = results[l]['analysis']
        marker = " <-" if 'phi' in l else ""
        print(f"  {l:<8} {a['anchor_clustering']:>10.2f} "
              f"{a['gradient_cv']:>10.4f} "
              f"{a['gradient_ratio']:>10.4f} "
              f"{a['total_anchor_anisotropy']:>10.4f}{marker}")

    # Return summary for runner
    summary = {}
    for l in labels:
        a = results[l]['analysis']
        summary[l] = {
            'ratio': results[l]['ratio'],
            'sb_clustering': a['anchor_clustering'],
            'gradient_cv': a['gradient_cv'],
            'gradient_ratio': a['gradient_ratio'],
            'regime_anisotropy': a['total_anchor_anisotropy'],
            'anchor_x': {n: a['anchor_x'][n] for n in ANCHORS},
            'anchor_y': {n: a['anchor_y'][n] for n in ANCHORS},
        }

    return summary


if __name__ == '__main__':
    run_analysis()
