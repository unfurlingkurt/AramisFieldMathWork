#!/usr/bin/env python3
"""
Stern-Brocot Harmonic Analyzer for BAO

The φ-framework predicts that ratios of scales in the baryon acoustic
oscillation (BAO) signal should show Stern-Brocot tree structure:

1. BAO peak position ratios cluster at SB tree nodes
2. Galaxy correlation function shows excess power at SB-harmonic separations
3. The ratio of BAO scale to torus circumference is a Farey fraction

This tool analyzes BAO measurements for SB-harmonic signatures,
working with either:
- Real DESI/SDSS BAO measurements
- Synthetic BAO data generated from models
"""

import numpy as np
from scipy.signal import find_peaks, argrelextrema
from scipy.interpolate import interp1d
from scipy.stats import ks_2samp
from fractions import Fraction
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

PHI = (1 + np.sqrt(5)) / 2


class SBHarmonicAnalyzer:
    """
    Analyze BAO correlation function for Stern-Brocot harmonic structure.
    """

    def __init__(self, max_sb_depth=8):
        """
        Parameters
        ----------
        max_sb_depth : int
            Maximum depth of Stern-Brocot tree to generate.
        """
        self.max_sb_depth = max_sb_depth
        self.sb_ratios = self._generate_stern_brocot(max_sb_depth)
        self.sb_values = self._get_sb_values()
        self.phi_harmonics = self._generate_phi_harmonics()

    def _generate_stern_brocot(self, max_depth):
        """Generate Stern-Brocot tree nodes up to given depth."""
        ratios = []

        def recurse(a, b, c, d, depth):
            if depth > max_depth:
                return
            m_num, m_den = a + c, b + d
            ratios.append((m_num, m_den, depth))
            recurse(a, b, m_num, m_den, depth + 1)
            recurse(m_num, m_den, c, d, depth + 1)

        ratios.append((0, 1, 0))
        ratios.append((1, 1, 1))

        recurse(0, 1, 1, 1, 2)
        recurse(1, 1, 1, 0, 2)

        return ratios

    def _get_sb_values(self, max_value=5.0):
        """Get sorted list of SB ratio values in [0, max_value]."""
        values = set()
        for num, den, depth in self.sb_ratios:
            if den > 0:
                val = num / den
                if 0 < val <= max_value:
                    values.add(val)
        return sorted(values)

    def _generate_phi_harmonics(self, n_harmonics=10):
        """
        Generate φ-harmonic scales.

        These are the predicted characteristic scales from the
        φ-equation framework:
            s_n = s_0 * φ^n  for integer n
        """
        harmonics = []
        for n in range(-n_harmonics, n_harmonics + 1):
            harmonics.append(PHI**n)
        return sorted(harmonics)

    def generate_synthetic_bao(self, r_bao=105.0, n_points=200,
                                r_max=200.0, seed=42):
        """
        Generate synthetic BAO correlation function.

        ξ(r) = A * sin(2π r / r_bao) * exp(-r/r_decay) / r²
               + noise

        Parameters
        ----------
        r_bao : float
            BAO scale in Mpc/h (standard: ~105 Mpc/h).
        n_points : int
            Number of separation bins.
        r_max : float
            Maximum separation in Mpc/h.
        seed : int
            Random seed.

        Returns
        -------
        r : ndarray
            Separations in Mpc/h.
        xi : ndarray
            Correlation function values.
        xi_err : ndarray
            Uncertainties.
        """
        np.random.seed(seed)

        r = np.linspace(5.0, r_max, n_points)
        r_decay = 150.0

        # BAO oscillation
        xi_bao = (0.01 * np.sin(2 * np.pi * r / r_bao) *
                  np.exp(-r / r_decay) / (r / 50)**2)

        # Smooth component (power-law)
        xi_smooth = 0.1 * (r / 50)**(-1.8)

        # Add φ-harmonic modulation (the signal we're looking for)
        phi_mod = 0.0
        for n in range(-3, 4):
            r_phi = r_bao * PHI**n
            if 5 < r_phi < r_max:
                phi_mod += 0.001 * np.exp(-0.5 * ((r - r_phi) / 5)**2)

        xi = xi_smooth + xi_bao + phi_mod

        # Realistic noise
        xi_err = 0.002 * np.ones_like(r) + 0.001 * r / r_max
        xi += np.random.randn(n_points) * xi_err

        return r, xi, xi_err

    def find_bao_peaks(self, r, xi, xi_err=None, min_prominence=None):
        """
        Find peaks and troughs in the BAO correlation function.

        Parameters
        ----------
        r : ndarray
            Separations.
        xi : ndarray
            Correlation function.
        xi_err : ndarray, optional
            Uncertainties.

        Returns
        -------
        peaks : dict
            Peak positions, heights, and ratios.
        """
        from scipy.ndimage import gaussian_filter1d

        # Work with r²ξ(r) which shows the BAO bump more clearly
        xi_weighted = xi * r**2
        xi_smooth = gaussian_filter1d(xi_weighted, sigma=2)

        # Detrend: remove smooth power-law background to isolate oscillations
        # Fit a simple polynomial to the smooth envelope
        from numpy.polynomial import polynomial as P
        mask = np.isfinite(xi_smooth)
        coeffs = P.polyfit(r[mask], xi_smooth[mask], deg=3)
        background = P.polyval(r, coeffs)
        xi_detrended = xi_smooth - background

        # Find peaks in detrended signal
        prom = min_prominence or np.std(xi_detrended[mask]) * 0.2
        peak_idx, _ = find_peaks(xi_detrended, prominence=prom, distance=3)
        trough_idx, _ = find_peaks(-xi_detrended, prominence=prom, distance=3)

        # If no peaks found in detrended, try local extrema on original
        if len(peak_idx) == 0:
            peak_idx = argrelextrema(xi_smooth, np.greater, order=5)[0]
        if len(trough_idx) == 0:
            trough_idx = argrelextrema(xi_smooth, np.less, order=5)[0]

        # All extrema
        extrema_idx = sorted(np.concatenate([peak_idx, trough_idx]))
        extrema_r = r[extrema_idx] if len(extrema_idx) > 0 else np.array([])

        # Compute ratios between consecutive extrema positions
        ratios = []
        for i in range(len(extrema_r) - 1):
            if extrema_r[i] > 0:
                ratio = extrema_r[i + 1] / extrema_r[i]
                ratios.append(ratio)

        # Identify main BAO peak: highest peak in r > 50 Mpc/h range
        if len(peak_idx) > 0:
            far_peaks = peak_idx[r[peak_idx] > 50]
            if len(far_peaks) > 0:
                main_peak_idx = far_peaks[np.argmax(xi_smooth[far_peaks])]
            else:
                main_peak_idx = peak_idx[np.argmax(xi_smooth[peak_idx])]
            r_bao = r[main_peak_idx]
        else:
            r_bao = 105.0  # fallback to fiducial

        bao_ratios = []
        for r_ext in extrema_r:
            if r_bao > 0:
                bao_ratios.append(r_ext / r_bao)

        return {
            'peak_positions': r[peak_idx] if len(peak_idx) > 0 else np.array([]),
            'peak_heights': xi_smooth[peak_idx] if len(peak_idx) > 0 else np.array([]),
            'trough_positions': r[trough_idx] if len(trough_idx) > 0 else np.array([]),
            'extrema_positions': extrema_r,
            'consecutive_ratios': np.array(ratios) if ratios else np.array([1.0]),
            'bao_ratios': np.array(bao_ratios) if bao_ratios else np.array([1.0]),
            'r_bao': r_bao,
        }

    def test_sb_clustering(self, ratios, n_random_trials=1000):
        """
        Test if observed ratios cluster at Stern-Brocot nodes.

        Compares the distance to nearest SB ratio for observed data
        vs random uniform data.

        Parameters
        ----------
        ratios : ndarray
            Observed scale ratios.
        n_random_trials : int
            Number of random comparison sets.

        Returns
        -------
        results : dict
            Clustering strength, p-value, nearest SB ratios.
        """
        if len(ratios) < 3:
            return {
                'clustering_strength': 1.0,
                'p_value': 1.0,
                'nearest_sb': [],
                'mean_observed_distance': 0.0,
                'mean_random_distance': 0.0,
                'observed_distances': [],
                'ratios': ratios,
            }

        # Distance to nearest SB ratio for observed data
        observed_distances = []
        nearest_sb = []
        for r in ratios:
            min_dist = float('inf')
            nearest = None
            for sb_val in self.sb_values:
                dist = abs(r - sb_val)
                if dist < min_dist:
                    min_dist = dist
                    nearest = sb_val
            observed_distances.append(min_dist)
            nearest_sb.append(nearest)

        mean_obs_dist = np.mean(observed_distances)

        # Random baseline
        random_distances = []
        for _ in range(n_random_trials):
            random_ratios = np.random.uniform(
                min(ratios) * 0.5,
                max(ratios) * 1.5,
                len(ratios)
            )
            rand_dists = []
            for r in random_ratios:
                min_dist = float('inf')
                for sb_val in self.sb_values:
                    dist = abs(r - sb_val)
                    if dist < min_dist:
                        min_dist = dist
                rand_dists.append(min_dist)
            random_distances.append(np.mean(rand_dists))

        random_distances = np.array(random_distances)
        mean_random_dist = np.mean(random_distances)

        # Clustering strength
        clustering = mean_random_dist / (mean_obs_dist + 1e-10)

        # P-value: fraction of random trials with smaller mean distance
        p_value = np.mean(random_distances <= mean_obs_dist)

        return {
            'clustering_strength': clustering,
            'p_value': p_value,
            'mean_observed_distance': mean_obs_dist,
            'mean_random_distance': mean_random_dist,
            'observed_distances': observed_distances,
            'nearest_sb': nearest_sb,
            'ratios': ratios,
        }

    def test_phi_harmonic_clustering(self, peak_positions, r_bao):
        """
        Test if peak positions cluster at φ-harmonic multiples of r_bao.

        r_peak / r_bao should be close to φ^n for some integer n.

        Parameters
        ----------
        peak_positions : ndarray
            Positions of peaks/features in Mpc/h.
        r_bao : float
            BAO scale in Mpc/h.

        Returns
        -------
        results : dict
        """
        if len(peak_positions) == 0 or r_bao <= 0:
            return {'clustering_strength': 1.0, 'p_value': 1.0}

        ratios_to_bao = peak_positions / r_bao

        # Distance to nearest φ-harmonic
        phi_distances = []
        nearest_phi = []
        for r in ratios_to_bao:
            if r > 0:
                # log_φ(r) should be close to an integer
                log_phi_r = np.log(r) / np.log(PHI)
                nearest_n = round(log_phi_r)
                distance = abs(log_phi_r - nearest_n)
                phi_distances.append(distance)
                nearest_phi.append(PHI**nearest_n)

        if len(phi_distances) == 0:
            return {'clustering_strength': 1.0, 'p_value': 1.0}

        mean_phi_dist = np.mean(phi_distances)

        # Random baseline
        random_phi_dists = []
        for _ in range(1000):
            random_ratios = np.random.uniform(0.1, 3.0, len(ratios_to_bao))
            rand_dists = []
            for r in random_ratios:
                if r > 0:
                    log_phi_r = np.log(r) / np.log(PHI)
                    nearest_n = round(log_phi_r)
                    rand_dists.append(abs(log_phi_r - nearest_n))
            random_phi_dists.append(np.mean(rand_dists))

        random_phi_dists = np.array(random_phi_dists)

        clustering = np.mean(random_phi_dists) / (mean_phi_dist + 1e-10)
        p_value = np.mean(random_phi_dists <= mean_phi_dist)

        return {
            'clustering_strength': clustering,
            'p_value': p_value,
            'ratios_to_bao': ratios_to_bao,
            'phi_distances': phi_distances,
            'nearest_phi_harmonics': nearest_phi,
        }

    def test_torus_circumference_ratio(self, r_bao, L_min_estimates):
        """
        Test if r_bao / L_torus is a Farey fraction.

        Parameters
        ----------
        r_bao : float
            BAO scale (Mpc/h).
        L_min_estimates : array-like
            Possible torus circumferences to test.

        Returns
        -------
        results : dict
            For each L_min, the nearest Farey fraction and distance.
        """
        results = []

        for L_min in L_min_estimates:
            ratio = r_bao / L_min

            # Find nearest Farey fraction
            best_frac = None
            best_dist = float('inf')

            for max_den in range(1, 20):
                for num in range(max_den + 1):
                    from math import gcd
                    if gcd(num, max_den) == 1:
                        frac_val = num / max_den
                        dist = abs(ratio - frac_val)
                        if dist < best_dist:
                            best_dist = dist
                            best_frac = Fraction(num, max_den)

            results.append({
                'L_min': L_min,
                'ratio': ratio,
                'nearest_farey': str(best_frac),
                'farey_value': float(best_frac),
                'distance': best_dist,
            })

        return results


def run_analysis(save_dir=None):
    """
    Run complete SB-harmonic BAO analysis.
    """
    import matplotlib.pyplot as plt

    if save_dir is None:
        save_dir = '.'

    print("=" * 70)
    print("STERN-BROCOT HARMONIC ANALYZER FOR BAO")
    print("Testing: BAO peak ratios cluster at SB tree nodes")
    print("=" * 70)

    analyzer = SBHarmonicAnalyzer(max_sb_depth=8)

    # Step 1: Generate synthetic BAO data
    print("\n[1] Generating synthetic BAO correlation function...")

    r_bao_fid = 105.0  # Mpc/h (fiducial BAO scale)
    r, xi, xi_err = analyzer.generate_synthetic_bao(r_bao=r_bao_fid, seed=42)
    print(f"    BAO scale: {r_bao_fid} Mpc/h")
    print(f"    Separation range: {r[0]:.0f} - {r[-1]:.0f} Mpc/h")

    # Step 2: Find peaks and extrema
    print("\n[2] Finding BAO peaks and extrema...")

    peaks = analyzer.find_bao_peaks(r, xi)

    print(f"    Main BAO peak: {peaks['r_bao']:.1f} Mpc/h")
    print(f"    Peak positions: {peaks['peak_positions']}")
    print(f"    Trough positions: {peaks['trough_positions']}")
    print(f"    Consecutive ratios: {peaks['consecutive_ratios']}")

    # Step 3: Test SB clustering of consecutive ratios
    print("\n[3] Testing Stern-Brocot clustering of peak ratios...")

    sb_results = analyzer.test_sb_clustering(peaks['consecutive_ratios'])

    print(f"    Mean distance to nearest SB ratio: "
          f"{sb_results['mean_observed_distance']:.4f}")
    print(f"    Random baseline: {sb_results['mean_random_distance']:.4f}")
    print(f"    Clustering strength: {sb_results['clustering_strength']:.2f}x")
    print(f"    P-value: {sb_results['p_value']:.4f}")

    if sb_results['clustering_strength'] > 1.5:
        print(f"    STRONG SB clustering detected!")
    elif sb_results['clustering_strength'] > 1.2:
        print(f"    Moderate SB clustering detected")
    else:
        print(f"    No significant SB clustering")

    # Step 4: Test φ-harmonic clustering
    print("\n[4] Testing φ-harmonic clustering of peak positions...")

    all_positions = np.concatenate([peaks['peak_positions'],
                                     peaks['trough_positions']])
    phi_results = analyzer.test_phi_harmonic_clustering(
        all_positions, peaks['r_bao']
    )

    print(f"    φ-harmonic clustering strength: "
          f"{phi_results['clustering_strength']:.2f}x")
    print(f"    P-value: {phi_results['p_value']:.4f}")

    if phi_results.get('ratios_to_bao') is not None:
        print(f"    Peak/BAO ratios:")
        for ratio, phi_h in zip(phi_results['ratios_to_bao'],
                                 phi_results.get('nearest_phi_harmonics', [])):
            n = round(np.log(phi_h) / np.log(PHI))
            print(f"      r/r_bao = {ratio:.3f} → nearest φ^{n} = {phi_h:.3f}")

    # Step 5: Test torus circumference ratio
    print("\n[5] Testing r_bao / L_torus as Farey fraction...")

    chi_rec = 14000.0 / 0.674  # Mpc/h
    L_min_estimates = np.array([0.3, 0.4, 0.5, 0.6, 0.7]) * chi_rec

    farey_results = analyzer.test_torus_circumference_ratio(
        r_bao_fid, L_min_estimates
    )

    for fr in farey_results:
        print(f"    L_min = {fr['L_min']:.0f} Mpc/h: "
              f"r_bao/L = {fr['ratio']:.6f} ≈ {fr['nearest_farey']} "
              f"(dist = {fr['distance']:.6f})")

    # Step 6: Multi-redshift analysis
    print("\n[6] Multi-redshift BAO analysis...")

    # DESI-like BAO measurements at different redshifts
    # (r_bao evolves with redshift through D_V(z))
    desi_data = [
        {'z': 0.30, 'DV': 1270.0, 'r_bao': 7.93},   # DV/rd
        {'z': 0.51, 'DV': 1870.0, 'r_bao': 11.77},
        {'z': 0.70, 'DV': 2430.0, 'r_bao': 15.28},
        {'z': 0.93, 'DV': 2990.0, 'r_bao': 18.80},
        {'z': 1.32, 'DV': 3770.0, 'r_bao': 23.68},
    ]

    print(f"    Analyzing DESI-like BAO scale ratios:")
    dv_values = [d['DV'] for d in desi_data]
    dv_ratios = []
    for i in range(len(dv_values) - 1):
        ratio = dv_values[i + 1] / dv_values[i]
        dv_ratios.append(ratio)
        # Check if close to φ
        phi_n = round(np.log(ratio) / np.log(PHI))
        phi_val = PHI**phi_n
        dist = abs(ratio - phi_val)
        print(f"      z={desi_data[i]['z']:.2f}→{desi_data[i+1]['z']:.2f}: "
              f"DV ratio = {ratio:.4f}, nearest φ^{phi_n} = {phi_val:.4f}, "
              f"dist = {dist:.4f}")

    dv_ratios = np.array(dv_ratios)
    dv_sb_results = analyzer.test_sb_clustering(dv_ratios)
    print(f"\n    DV ratio SB clustering: {dv_sb_results['clustering_strength']:.2f}x")

    # Visualization
    print("\n[7] Creating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    # 1. BAO correlation function
    ax = axes[0, 0]
    ax.errorbar(r, xi * r**2, yerr=xi_err * r**2, fmt='k.', markersize=3,
                alpha=0.5, label='ξ(r)·r²')
    for rp in peaks['peak_positions']:
        ax.axvline(rp, color='r', alpha=0.3, linestyle='-')
    for rt in peaks['trough_positions']:
        ax.axvline(rt, color='b', alpha=0.3, linestyle='--')

    # Mark φ-harmonic positions
    for n in range(-2, 4):
        r_phi = r_bao_fid * PHI**n
        if 5 < r_phi < 200:
            ax.axvline(r_phi, color='gold', alpha=0.4, linewidth=2,
                       linestyle=':')
            ax.text(r_phi, ax.get_ylim()[1] * 0.9, f'φ^{n}',
                    fontsize=7, ha='center', color='goldenrod')

    ax.set_xlabel('r (Mpc/h)')
    ax.set_ylabel('ξ(r) · r²')
    ax.set_title('BAO Correlation Function\nRed=peaks, Blue=troughs, Gold=φ-harmonics')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 2. Peak ratios vs SB ratios
    ax = axes[0, 1]
    if len(peaks['consecutive_ratios']) > 0:
        ax.scatter(range(len(peaks['consecutive_ratios'])),
                   peaks['consecutive_ratios'],
                   color='red', s=50, zorder=5, label='Observed')

        # Mark SB ratios in range
        ratio_min = min(peaks['consecutive_ratios']) * 0.8
        ratio_max = max(peaks['consecutive_ratios']) * 1.2
        for sb_val in analyzer.sb_values:
            if ratio_min < sb_val < ratio_max:
                ax.axhline(sb_val, color='blue', alpha=0.2, linewidth=1)

    ax.set_xlabel('Peak Pair Index')
    ax.set_ylabel('Consecutive Peak Ratio')
    ax.set_title(f'Peak Ratios vs SB Nodes\nClustering: '
                 f'{sb_results["clustering_strength"]:.2f}x')
    ax.grid(True, alpha=0.3)

    # 3. φ-harmonic test
    ax = axes[0, 2]
    if phi_results.get('ratios_to_bao') is not None and len(phi_results['ratios_to_bao']) > 0:
        log_ratios = np.log(phi_results['ratios_to_bao']) / np.log(PHI)
        ax.scatter(phi_results['ratios_to_bao'], log_ratios,
                   color='red', s=50, zorder=5)
        # Mark integer lines (φ-harmonics)
        for n in range(-3, 5):
            ax.axhline(n, color='gold', alpha=0.3, linewidth=2)
            ax.text(0.05, n + 0.1, f'n={n}', fontsize=8, color='goldenrod')
    ax.set_xlabel('r_peak / r_bao')
    ax.set_ylabel('log_φ(r_peak / r_bao)')
    ax.set_title(f'φ-Harmonic Test\nClustering: '
                 f'{phi_results["clustering_strength"]:.2f}x')
    ax.grid(True, alpha=0.3)

    # 4. SB distance histogram
    ax = axes[1, 0]
    if len(sb_results.get('observed_distances', [])) > 0:
        ax.hist(sb_results['observed_distances'], bins=15, alpha=0.7,
                color='red', edgecolor='black', label='Observed', density=True)
    # Random baseline distribution
    random_baseline_dists = []
    for _ in range(1000):
        rr = np.random.uniform(1.0, 2.0, max(10, len(peaks['consecutive_ratios'])))
        for r_val in rr:
            min_d = min(abs(r_val - sb) for sb in analyzer.sb_values if sb > 0)
            random_baseline_dists.append(min_d)
    ax.hist(random_baseline_dists, bins=30, alpha=0.3, color='blue',
            edgecolor='black', label='Random', density=True)
    ax.set_xlabel('Distance to Nearest SB Ratio')
    ax.set_ylabel('Density')
    ax.set_title('SB Clustering: Observed vs Random')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 5. DESI DV ratios
    ax = axes[1, 1]
    z_pairs = [f'{desi_data[i]["z"]:.1f}-{desi_data[i+1]["z"]:.1f}'
               for i in range(len(dv_ratios))]
    ax.bar(z_pairs, dv_ratios, alpha=0.7, color='purple', edgecolor='black')
    ax.axhline(PHI, color='gold', linestyle='--', linewidth=2, label=f'φ = {PHI:.3f}')
    ax.axhline(1.0, color='gray', linestyle=':', alpha=0.5)
    ax.set_xlabel('Redshift Pair')
    ax.set_ylabel('DV Ratio')
    ax.set_title(f'DESI-like DV Ratios\nSB clustering: '
                 f'{dv_sb_results["clustering_strength"]:.2f}x')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Summary
    ax = axes[1, 2]
    ax.axis('off')
    summary = (
        f"SB-HARMONIC BAO ANALYSIS\n"
        f"{'='*40}\n\n"
        f"φ-framework predictions:\n"
        f"  Peak ratios → SB tree nodes\n"
        f"  Peak positions → φ^n × r_bao\n"
        f"  r_bao/L_torus → Farey fraction\n\n"
        f"Results:\n"
        f"  BAO scale: {peaks['r_bao']:.1f} Mpc/h\n"
        f"  Peaks found: {len(peaks['peak_positions'])}\n"
        f"  Troughs found: {len(peaks['trough_positions'])}\n\n"
        f"SB clustering:\n"
        f"  Strength: {sb_results['clustering_strength']:.2f}x\n"
        f"  P-value: {sb_results['p_value']:.4f}\n\n"
        f"φ-harmonic clustering:\n"
        f"  Strength: {phi_results['clustering_strength']:.2f}x\n"
        f"  P-value: {phi_results['p_value']:.4f}\n\n"
        f"DESI DV ratios:\n"
        f"  SB clustering: {dv_sb_results['clustering_strength']:.2f}x"
    )
    ax.text(0.05, 0.95, summary, fontsize=9, family='monospace',
            verticalalignment='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    save_path = f'{save_dir}/sb_harmonic_bao_analysis.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {save_path}")

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")

    return {
        'peaks': peaks,
        'sb_results': sb_results,
        'phi_results': phi_results,
        'farey_results': farey_results,
        'dv_sb_results': dv_sb_results,
    }


if __name__ == '__main__':
    results = run_analysis(
        save_dir='phi_equation_investigation/phi_domain_analysis/cosmic_anisotropy'
    )
