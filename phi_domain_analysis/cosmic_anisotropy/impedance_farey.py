#!/usr/bin/env python3
"""
Impedance Crystallization Analysis — Depth-12 Triple Torus

Analyzes impedance Z = |nabla phi|/|dphi/dt| from the actual phi-equation
using the three crystallization anchors at Farey depth 12:

    Octave  (1:2) — Loop via divisor 6
    Fifth   (2:3) — Loop via divisor 4
    Fourth  (3:4) — Loop via divisor 3

MEASUREMENT: CF tension via composition.
    tension_to_anchor(Z, p/q) = len(CF(Z * q/p))
    When Z = p/q: composition = 1, CF = [1], tension = 1 (minimum).

CLASSIFICATION: nearest anchor by minimum CF tension.
    Three basins of attraction = three loops of the triple torus.

Z is a RATIO of spatial frequency to temporal frequency.
It is a standing wave navigating a curved, discrete crystal.
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
    continued_fraction, farey_depth, tension,
    tension_to_anchor, classify_by_anchor,
    classify_array_by_anchor, anchor_tension_profile,
    anchor_clustering_strength,
    nearest_sb_ratio, generate_sb_ratios,
)


class ImpedanceCrystallizationAnalyzer:
    """
    Analyze impedance from phi-equation using depth-12 crystallization anchors.
    """

    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx

    def collect_impedance(self, Nx=200, T=200, seed=42):
        """
        Run 1D phi-equation and collect impedance values.
        """
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )

        np.random.seed(seed)
        solver.phi = 0.5 * np.random.randn(Nx)

        impedances = []
        n_steps = int(T / 0.1)

        for i in range(n_steps):
            phi_old = solver.phi.copy()
            t_old = solver.time
            solver.step()
            dt = solver.time - t_old

            if i % 10 == 0 and i > 0 and dt > 1e-12:
                dphi_dt = (solver.phi - phi_old) / dt
                grad_phi = np.gradient(solver.phi, self.dx)
                Z = np.abs(grad_phi) / (np.abs(dphi_dt) + 1e-10)
                impedances.append(Z)

        return np.array(impedances)

    def analyze_crystallization(self, impedances, n_samples=3000):
        """
        Full crystallization anchor analysis of impedance values.
        """
        Z_flat = impedances.flatten()
        Z_flat = Z_flat[np.isfinite(Z_flat) & (Z_flat > 0)]

        if len(Z_flat) > n_samples:
            rng = np.random.default_rng(0)
            Z_sample = rng.choice(Z_flat, n_samples, replace=False)
        else:
            Z_sample = Z_flat

        # 1. Anchor classification (depth-12 triple torus basins)
        anchor_cls = classify_array_by_anchor(Z_flat)

        # 2. Tension profiles to each anchor
        profiles = anchor_tension_profile(Z_sample)

        # 3. Anchor clustering strength
        clustering, mean_obs, mean_rand = anchor_clustering_strength(Z_flat)

        # 4. Per-sample classification with tensions
        sample_anchors = []
        sample_tensions = {'octave': [], 'fifth': [], 'fourth': []}
        for z in Z_sample[:1000]:
            nearest, tensions = classify_by_anchor(z)
            sample_anchors.append(nearest)
            for name, t in tensions.items():
                sample_tensions[name].append(t)

        # 5. Continued fraction structure of compositions
        #    For each anchor, what does CF(Z * q/p) look like?
        cf_stats = {}
        for name, (num, den) in ANCHORS.items():
            comps = Z_sample * den / num
            comps = comps[np.isfinite(comps) & (comps > 0)]
            cf_lengths = [len(continued_fraction(c)) for c in comps[:1000]]
            cf_lengths = np.array(cf_lengths)
            cf_stats[name] = {
                'mean_cf_len': np.mean(cf_lengths),
                'median_cf_len': np.median(cf_lengths),
                'min_cf_len': np.min(cf_lengths),
                'cf_len_distribution': cf_lengths,
            }

        # 6. Pairwise tension between impedance values
        n_pairs = min(500, len(Z_sample))
        pair_tensions = []
        rng = np.random.default_rng(1)
        indices = rng.choice(len(Z_sample), (n_pairs, 2), replace=True)
        for i, j in indices:
            t = tension(Z_sample[i], Z_sample[j])
            pair_tensions.append(t)
        pair_tensions = np.array(pair_tensions)

        return {
            'anchor_classification': anchor_cls,
            'tension_profiles': profiles,
            'anchor_clustering': clustering,
            'mean_anchor_tension': mean_obs,
            'random_anchor_tension': mean_rand,
            'sample_tensions': {k: np.array(v) for k, v in sample_tensions.items()},
            'cf_stats': cf_stats,
            'pair_tensions': pair_tensions,
            'mean_pair_tension': np.mean(pair_tensions),
            'Z_sample': Z_sample,
        }


def run_analysis(save_dir='.'):
    """Run the full impedance crystallization analysis."""
    print("=" * 70)
    print("  IMPEDANCE CRYSTALLIZATION ANALYSIS — Depth-12 Triple Torus")
    print("  Z = |nabla phi|/|dphi/dt| is a RATIO on the SB tree")
    print("  Anchors: Octave (1:2), Fifth (2:3), Fourth (3:4)")
    print("  Measurement: CF tension via composition Z*q/p")
    print("=" * 70)

    analyzer = ImpedanceCrystallizationAnalyzer()

    print("\n  Collecting impedance from phi-equation (1D, T=300)...")
    t0 = time.time()
    impedances = analyzer.collect_impedance(Nx=200, T=300)
    print(f"  Collected {impedances.shape[0]} snapshots x {impedances.shape[1]} points "
          f"in {time.time()-t0:.1f}s")

    print("\n  Analyzing crystallization structure...")
    result = analyzer.analyze_crystallization(impedances)

    # Print results
    ac = result['anchor_classification']
    trans = ac.get('transitional', 0)
    cryst = ac.get('crystallized_fraction', 1 - trans)
    print(f"\n  Crystallization Status:")
    print(f"    Crystallized:  {100*cryst:.1f}%")
    print(f"    Transitional:  {100*trans:.1f}% (equidistant from all anchors)")

    print(f"\n  Anchor Basin Distribution (of crystallized values):")
    if cryst > 0:
        print(f"    Octave (1:2): {100*ac['octave']/cryst:.1f}% of crystallized")
        print(f"    Fifth  (2:3): {100*ac['fifth']/cryst:.1f}% of crystallized")
        print(f"    Fourth (3:4): {100*ac['fourth']/cryst:.1f}% of crystallized")
    else:
        print(f"    (No crystallized values)")

    print(f"\n  Raw Anchor Fractions (of all values):")
    print(f"    Octave (1:2): {100*ac['octave']:.1f}%")
    print(f"    Fifth  (2:3): {100*ac['fifth']:.1f}%")
    print(f"    Fourth (3:4): {100*ac['fourth']:.1f}%")

    print(f"\n  Mean Tensions to Anchors:")
    mt = ac['mean_tensions']
    for name in ['octave', 'fifth', 'fourth']:
        print(f"    {name:>8}: {mt[name]:.2f}")

    print(f"\n  Anchor Clustering: {result['anchor_clustering']:.2f}x "
          f"(obs={result['mean_anchor_tension']:.4f}, "
          f"rand={result['random_anchor_tension']:.4f})")

    # CF composition statistics
    print(f"\n  CF Composition Statistics (len(CF(Z*q/p))):")
    for name in ['octave', 'fifth', 'fourth']:
        cs = result['cf_stats'][name]
        num, den = ANCHORS[name]
        print(f"    {name:>8} (Z*{den}/{num}): "
              f"mean={cs['mean_cf_len']:.1f} "
              f"median={cs['median_cf_len']:.0f} "
              f"min={cs['min_cf_len']:.0f}")

    # Raw Z distribution for context
    Z_all = impedances.flatten()
    Z_all = Z_all[np.isfinite(Z_all) & (Z_all > 0)]
    print(f"\n  Raw Z Distribution:")
    print(f"    Median Z: {np.median(Z_all):.4f}")
    print(f"    Mean Z:   {np.mean(Z_all):.4f}")
    print(f"    p25:      {np.percentile(Z_all, 25):.4f}")
    print(f"    p75:      {np.percentile(Z_all, 75):.4f}")

    print(f"\n  Pairwise Tension: mean={result['mean_pair_tension']:.1f}")

    # --- Visualization ---
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    anchor_colors = {'octave': '#4A90D9', 'fifth': '#7BC47F', 'fourth': '#D94A4A'}

    # 1. Impedance distribution with anchor positions
    ax = axes[0, 0]
    Z_sample = result['Z_sample']
    Z_plot = Z_sample[Z_sample < 5]
    ax.hist(Z_plot, bins=80, alpha=0.7, edgecolor='none', color='purple', density=True)
    for name, (num, den) in ANCHORS.items():
        val = num / den
        ax.axvline(val, color=anchor_colors[name], linewidth=2.5,
                   linestyle='-', label=f'{name} ({num}/{den})')
    ax.set_xlabel('Impedance Z')
    ax.set_ylabel('Density')
    ax.set_title('Impedance Distribution\nwith crystallization anchors')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    # 2. Crystallized vs transitional + anchor basin breakdown
    ax = axes[0, 1]
    anchor_names = ['Octave\n(1:2)', 'Fifth\n(2:3)', 'Fourth\n(3:4)', 'Trans-\nitional']
    fracs = [ac['octave'], ac['fifth'], ac['fourth'], ac.get('transitional', 0)]
    colors_list = [anchor_colors['octave'], anchor_colors['fifth'],
                   anchor_colors['fourth'], '#AAAAAA']
    bars = ax.bar(anchor_names, fracs, color=colors_list, edgecolor='black', alpha=0.8)
    ax.set_ylabel('Fraction')
    ax.set_title('Crystallization Basin Fractions\n(Depth-12 triple torus anchors)')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, fracs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{100*val:.1f}%', ha='center', va='bottom', fontsize=10)

    # 3. Tension profiles to each anchor
    ax = axes[0, 2]
    profiles = result['tension_profiles']
    for name in ['octave', 'fifth', 'fourth']:
        t_vals = profiles[name]
        max_t = int(min(t_vals.max(), 20))
        ax.hist(t_vals, bins=range(1, max_t + 2), alpha=0.5,
                edgecolor='black', color=anchor_colors[name],
                label=f'{name}', align='left', density=True)
    ax.set_xlabel('CF Tension to Anchor')
    ax.set_ylabel('Density')
    ax.set_title('Tension Distribution to Each Anchor\nlen(CF(Z*q/p))')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 4. CF composition length distributions
    ax = axes[1, 0]
    for name in ['octave', 'fifth', 'fourth']:
        cf_lens = result['cf_stats'][name]['cf_len_distribution']
        max_cf = int(min(cf_lens.max(), 20))
        ax.hist(cf_lens, bins=range(1, max_cf + 2), alpha=0.5,
                edgecolor='black', color=anchor_colors[name],
                label=f'{name} (mean={np.mean(cf_lens):.1f})',
                align='left', density=True)
    ax.set_xlabel('CF Length of Composition Z*q/p')
    ax.set_ylabel('Density')
    ax.set_title('Continued Fraction Composition\n(Shorter = closer to anchor)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Pairwise tension distribution
    ax = axes[1, 1]
    pair_t = result['pair_tensions']
    max_pt = int(min(pair_t.max(), 20))
    ax.hist(pair_t, bins=range(0, max_pt + 2), alpha=0.7,
            edgecolor='black', color='coral', align='left')
    ax.set_xlabel('Pairwise Tension (CF length of ratio)')
    ax.set_ylabel('Count')
    ax.set_title(f'Hyperbolic Distance Distribution\nMean pairwise tension = {result["mean_pair_tension"]:.1f}')
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Impedance evolution heatmap
    ax = axes[1, 2]
    n_show = min(50, impedances.shape[0])
    Z_show = impedances[-n_show:]
    Z_clipped = np.clip(Z_show, 0, np.percentile(Z_show, 95))
    im = ax.imshow(Z_clipped, aspect='auto', cmap='hot', origin='lower')
    ax.set_xlabel('Position')
    ax.set_ylabel('Time step')
    ax.set_title('Impedance Z Evolution\n(from phi-equation dynamics)')
    plt.colorbar(im, ax=ax, label='Z')

    plt.suptitle(
        f'Impedance Crystallization Analysis\n'
        f'Depth-{CRYSTALLIZATION_DEPTH} Triple Torus: '
        f'Octave (1:2), Fifth (2:3), Fourth (3:4)',
        fontsize=12, fontweight='bold', y=1.02
    )
    plt.tight_layout()

    out_path = os.path.join(save_dir, 'impedance_farey.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\n  Saved: {out_path}")
    plt.close()

    return {
        'anchor_classification': ac,
        'anchor_clustering': result['anchor_clustering'],
        'mean_anchor_tension': result['mean_anchor_tension'],
        'mean_pair_tension': result['mean_pair_tension'],
        'crystallized_fraction': ac.get('crystallized_fraction', 0),
        'cf_stats': {n: result['cf_stats'][n]['mean_cf_len'] for n in ANCHORS},
    }


if __name__ == '__main__':
    run_analysis()
