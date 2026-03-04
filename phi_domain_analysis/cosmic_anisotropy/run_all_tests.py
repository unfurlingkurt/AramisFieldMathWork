#!/usr/bin/env python3
"""
Cosmic Anisotropy Analysis — Depth-12 Crystallization Framework

All measurements use CF tension to the three crystallization anchors
at Farey depth 12 (triple torus phase transition):

    Octave  (1:2) — Loop via divisor 6
    Fifth   (2:3) — Loop via divisor 4
    Fourth  (3:4) — Loop via divisor 3

Tools:
1. Torus Anisotropy — phi-equation on T^2 with various aspect ratios
2. Impedance Crystallization — Z classified by nearest anchor
3. Gradient Geodesic — ||nabla phi||^2 conservation = geodesic flow

Usage:
    python run_all_tests.py [--tool N] [--save-dir DIR]
"""

import sys
import os
import time
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHI = (1 + np.sqrt(5)) / 2


def run_tool_1(save_dir):
    """Torus Anisotropy Analysis"""
    from torus_anisotropy import run_analysis
    return run_analysis(save_dir=save_dir)


def run_tool_2(save_dir):
    """Impedance Crystallization Analysis"""
    from impedance_farey import run_analysis
    return run_analysis(save_dir=save_dir)


def run_tool_3(save_dir):
    """Gradient Geodesic Flow"""
    from gradient_geodesic import run_analysis
    return run_analysis(save_dir=save_dir)


def print_grand_summary(all_results):
    """Print summary of all crystallization framework results."""
    print("\n")
    print("=" * 70)
    print("  COSMIC ANISOTROPY — CRYSTALLIZATION FRAMEWORK SUMMARY")
    print("  Depth-12 Triple Torus Anchors: 1:2, 2:3, 3:4")
    print("  Measurement: CF tension via composition Z*q/p")
    print("=" * 70)

    print(f"\n  phi = {PHI:.6f}")
    print(f"  phi^2 = {PHI**2:.6f}")
    print()

    if 'torus_anisotropy' in all_results:
        r = all_results['torus_anisotropy']
        print("  [1] TORUS ANISOTROPY (phi-equation on T^2)")
        for label in ['1:1', '1:phi', '1:phi2', '1:2', '1:rt2']:
            if label in r:
                d = r[label]
                marker = " <-" if 'phi' in label else ""
                print(f"      {label}: Clust={d['sb_clustering']:.1f}x "
                      f"GradCV={d['gradient_cv']:.4f} "
                      f"Ratio={d['gradient_ratio']:.3f} "
                      f"Aniso={d['regime_anisotropy']:.4f}{marker}")
        print()

    if 'impedance_farey' in all_results:
        r = all_results['impedance_farey']
        ac = r['anchor_classification']
        print("  [2] IMPEDANCE CRYSTALLIZATION (Z on SB tree)")
        print(f"      Anchor basins: Oct={100*ac['octave']:.1f}% "
              f"5th={100*ac['fifth']:.1f}% 4th={100*ac['fourth']:.1f}%")
        print(f"      Anchor clustering: {r['anchor_clustering']:.1f}x")
        print(f"      Mean pair tension: {r['mean_pair_tension']:.1f}")
        if 'cf_stats' in r:
            cs = r['cf_stats']
            print(f"      CF composition: Oct={cs.get('octave',0):.1f} "
                  f"5th={cs.get('fifth',0):.1f} 4th={cs.get('fourth',0):.1f}")
        print()

    if 'gradient_geodesic' in all_results:
        r = all_results['gradient_geodesic']
        print("  [3] GRADIENT GEODESIC (||nabla phi||^2 conservation)")
        for label in ['1:1', '1:phi', '1:phi^2', '1:2']:
            if label in r:
                d = r[label]
                marker = " <-" if 'phi' in label else ""
                print(f"      {label}: CV={d['total_cv']:.6f} "
                      f"Ratio={d['grad_ratio']:.4f} "
                      f"Expected={d['expected_ratio']:.4f}{marker}")
        print()

    print("=" * 70)
    print("  Framework:")
    print("    phi_{t+1} = phi_t + alpha(Delta phi - gamma|nabla phi|^2) + beta*tanh(phi)*e^{-|nabla phi|}")
    print("    Z = |nabla phi|/|dphi/dt| (SB ratio, standing wave on crystal)")
    print("    ||nabla phi||^2 = const (geodesic flow)")
    print("    Anchors: Octave (1:2), Fifth (2:3), Fourth (3:4)")
    print()
    print("  Prediction: T^3 with circumferences 1 : phi : phi^2")
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Run depth-12 crystallization framework analysis'
    )
    parser.add_argument('--tool', type=int, default=0,
                        help='Run specific tool (1-3), or 0 for all')
    parser.add_argument('--save-dir', type=str, default='.',
                        help='Output directory')
    args = parser.parse_args()

    save_dir = args.save_dir
    os.makedirs(save_dir, exist_ok=True)

    tools = {
        1: ('Torus Anisotropy', 'torus_anisotropy', run_tool_1),
        2: ('Impedance Crystallization', 'impedance_farey', run_tool_2),
        3: ('Gradient Geodesic', 'gradient_geodesic', run_tool_3),
    }

    all_results = {}

    if args.tool > 0:
        tool_ids = [args.tool]
    else:
        tool_ids = [1, 2, 3]

    total_start = time.time()

    for tid in tool_ids:
        name, key, func = tools[tid]
        print(f"\n{'#'*70}")
        print(f"# TOOL {tid}: {name}")
        print(f"{'#'*70}\n")

        start = time.time()
        try:
            result = func(save_dir)
            all_results[key] = result
            elapsed = time.time() - start
            print(f"\n  Tool {tid} completed in {elapsed:.1f}s")
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n  Tool {tid} FAILED after {elapsed:.1f}s: {e}")
            import traceback
            traceback.print_exc()

    total_elapsed = time.time() - total_start
    print(f"\n  Total elapsed: {total_elapsed:.1f}s")

    if len(all_results) > 1:
        print_grand_summary(all_results)

    return all_results


if __name__ == '__main__':
    main()
