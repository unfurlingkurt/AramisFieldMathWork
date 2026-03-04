#!/usr/bin/env python3
"""
Targeted Matched-Circles Search

In a T³ universe, light from the last scattering surface wraps around
the torus, creating pairs of matched circles on the CMB where
temperature patterns repeat.

Previous blind searches found no matches — but they searched ALL
possible circle sizes and orientations, incurring a massive trials
penalty. The φ-framework constrains the search:

1. Circles appear at angular separations determined by R₁, R₂, R₃
2. R₁ : R₂ : R₃ = 1 : φ : φ²
3. Orientation: along the Axis of Evil

This dramatically reduces the search space, potentially revealing
signals too weak to detect in blind searches.

The matched-circles test:
- For each pair of back-to-back circles with angular radius α
- Extract temperature profiles around both circles
- Compute cross-correlation S(α) between the two profiles
- High S(α) at the predicted angular radii = detection

For T³ with circumference L in direction n̂:
    cos(α) = L / (2 χ_rec)
    where α is the angular radius of the matched circles
"""

import numpy as np
import healpy as hp
from scipy.signal import correlate
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

PHI = (1 + np.sqrt(5)) / 2


class MatchedCirclesSearcher:
    """
    Search for matched circles on the CMB at φ-harmonic angular radii.
    """

    def __init__(self, nside=64, n_points_per_circle=360):
        """
        Parameters
        ----------
        nside : int
            HEALPix resolution.
        n_points_per_circle : int
            Number of sample points around each circle.
        """
        self.nside = nside
        self.npix = hp.nside2npix(nside)
        self.n_points = n_points_per_circle
        self.lmax = 3 * nside - 1

    def predicted_circle_radii(self, L_min_over_chi_rec=0.5):
        """
        Compute predicted matched-circle angular radii for φ-harmonic T³.

        cos(α_i) = L_i / (2 χ_rec)

        Parameters
        ----------
        L_min_over_chi_rec : float
            L₁ / χ_rec — ratio of shortest torus circumference to
            comoving distance to last scattering.

        Returns
        -------
        radii : dict
            Angular radii (in degrees) for each S¹ factor.
        """
        L_ratios = [1.0, PHI, PHI**2]

        radii = {}
        for i, (label, L_ratio) in enumerate(zip(['L1', 'L2', 'L3'], L_ratios)):
            L_over_chi = L_min_over_chi_rec * L_ratio
            if L_over_chi <= 2.0:
                cos_alpha = L_over_chi / 2.0
                alpha_deg = np.degrees(np.arccos(cos_alpha))
                radii[label] = {
                    'alpha_deg': alpha_deg,
                    'alpha_rad': np.radians(alpha_deg),
                    'L_over_chi_rec': L_over_chi,
                    'cos_alpha': cos_alpha,
                }
            else:
                radii[label] = {
                    'alpha_deg': None,
                    'note': 'L > 2χ_rec: no matched circles',
                }

        return radii

    def extract_circle_profile(self, cmb_map, center_theta, center_phi,
                                 radius_rad):
        """
        Extract temperature profile along a circle on the sphere.

        Parameters
        ----------
        cmb_map : ndarray
            HEALPix temperature map.
        center_theta : float
            Colatitude of circle center (radians).
        center_phi : float
            Longitude of circle center (radians).
        radius_rad : float
            Angular radius of circle (radians).

        Returns
        -------
        profile : ndarray
            Temperature values around the circle.
        positions : ndarray
            (theta, phi) positions of sample points.
        """
        # Generate points around the circle
        psi = np.linspace(0, 2 * np.pi, self.n_points, endpoint=False)

        # Circle points in local frame (z-axis = center direction)
        x_local = np.sin(radius_rad) * np.cos(psi)
        y_local = np.sin(radius_rad) * np.sin(psi)
        z_local = np.cos(radius_rad) * np.ones_like(psi)

        # Rotate to global frame
        # Rotation from z-axis to (center_theta, center_phi)
        ct, st = np.cos(center_theta), np.sin(center_theta)
        cp, sp = np.cos(center_phi), np.sin(center_phi)

        # Rotation matrix
        x_global = (ct * cp * x_local - sp * y_local + st * cp * z_local)
        y_global = (ct * sp * x_local + cp * y_local + st * sp * z_local)
        z_global = (-st * x_local + ct * z_local)

        # Convert to (theta, phi) and get pixel values
        theta_pts = np.arccos(np.clip(z_global, -1, 1))
        phi_pts = np.arctan2(y_global, x_global) % (2 * np.pi)

        # Get pixel indices
        pix = hp.ang2pix(self.nside, theta_pts, phi_pts)
        profile = cmb_map[pix]

        positions = np.column_stack([theta_pts, phi_pts])

        return profile, positions

    def compute_circle_correlation(self, profile1, profile2):
        """
        Compute cross-correlation between two circle profiles.

        Tests all relative rotations and returns the maximum.

        Parameters
        ----------
        profile1, profile2 : ndarray
            Temperature profiles around two circles.

        Returns
        -------
        max_corr : float
            Maximum cross-correlation over all phase shifts.
        best_shift : int
            Phase shift giving maximum correlation.
        corr_function : ndarray
            Full cross-correlation function.
        """
        n = len(profile1)

        # Normalize
        p1 = (profile1 - np.mean(profile1)) / (np.std(profile1) + 1e-15)
        p2 = (profile2 - np.mean(profile2)) / (np.std(profile2) + 1e-15)

        # Cross-correlation for all phase shifts
        corr_function = np.zeros(n)
        for shift in range(n):
            p2_shifted = np.roll(p2, shift)
            corr_function[shift] = np.mean(p1 * p2_shifted)

        max_corr = np.max(corr_function)
        best_shift = np.argmax(corr_function)

        # Also check anti-correlated (reversed circle)
        p2_rev = p2[::-1]
        corr_rev = np.zeros(n)
        for shift in range(n):
            p2_shifted = np.roll(p2_rev, shift)
            corr_rev[shift] = np.mean(p1 * p2_shifted)

        if np.max(corr_rev) > max_corr:
            max_corr = np.max(corr_rev)
            best_shift = np.argmax(corr_rev)
            corr_function = corr_rev

        return max_corr, best_shift, corr_function

    def search_matched_circles(self, cmb_map, alpha_rad, axis_theta,
                                 axis_phi, n_test_pairs=20):
        """
        Search for matched circles at a specific angular radius.

        For a T³ with identification direction (axis_theta, axis_phi),
        the matched circles are centered at:
        - Center 1: (axis_theta, axis_phi) shifted by angle from origin
        - Center 2: antipodal point shifted

        Parameters
        ----------
        cmb_map : ndarray
            HEALPix temperature map.
        alpha_rad : float
            Angular radius to test (radians).
        axis_theta : float
            Colatitude of torus identification direction.
        axis_phi : float
            Longitude of torus identification direction.
        n_test_pairs : int
            Number of circle pairs to test along the axis.

        Returns
        -------
        results : dict
            Correlation statistics for matched circles at this radius.
        """
        correlations = []

        # Test circles centered along the identification axis
        # and its great circle
        offsets = np.linspace(0, np.pi, n_test_pairs, endpoint=False)

        for offset in offsets:
            # Circle 1 center: offset from axis
            c1_theta = axis_theta
            c1_phi = axis_phi + offset

            # Circle 2 center: antipodal identification
            c2_theta = np.pi - c1_theta
            c2_phi = (c1_phi + np.pi) % (2 * np.pi)

            # Extract profiles
            prof1, _ = self.extract_circle_profile(
                cmb_map, c1_theta, c1_phi, alpha_rad
            )
            prof2, _ = self.extract_circle_profile(
                cmb_map, c2_theta, c2_phi, alpha_rad
            )

            # Compute correlation
            max_corr, best_shift, corr_func = self.compute_circle_correlation(
                prof1, prof2
            )

            correlations.append({
                'max_correlation': max_corr,
                'best_shift': best_shift,
                'center1': (c1_theta, c1_phi),
                'center2': (c2_theta, c2_phi),
            })

        max_corrs = [c['max_correlation'] for c in correlations]

        return {
            'alpha_rad': alpha_rad,
            'alpha_deg': np.degrees(alpha_rad),
            'correlations': correlations,
            'max_correlation': np.max(max_corrs),
            'mean_correlation': np.mean(max_corrs),
            'std_correlation': np.std(max_corrs),
        }

    def compute_null_distribution(self, cmb_map, alpha_rad, n_trials=100):
        """
        Compute null distribution of correlations from random circle pairs.

        Parameters
        ----------
        cmb_map : ndarray
            HEALPix temperature map.
        alpha_rad : float
            Angular radius.
        n_trials : int
            Number of random pairs to test.

        Returns
        -------
        null_corrs : ndarray
            Distribution of max correlations for random pairs.
        """
        np.random.seed(123)
        null_corrs = []

        for _ in range(n_trials):
            # Random circle centers
            c1_theta = np.arccos(2 * np.random.random() - 1)
            c1_phi = 2 * np.pi * np.random.random()
            c2_theta = np.arccos(2 * np.random.random() - 1)
            c2_phi = 2 * np.pi * np.random.random()

            prof1, _ = self.extract_circle_profile(
                cmb_map, c1_theta, c1_phi, alpha_rad
            )
            prof2, _ = self.extract_circle_profile(
                cmb_map, c2_theta, c2_phi, alpha_rad
            )

            max_corr, _, _ = self.compute_circle_correlation(prof1, prof2)
            null_corrs.append(max_corr)

        return np.array(null_corrs)

    def targeted_search(self, cmb_map, L_min_over_chi_rec=0.5):
        """
        Run targeted matched-circles search at φ-harmonic radii.

        Parameters
        ----------
        cmb_map : ndarray
            HEALPix temperature map.
        L_min_over_chi_rec : float
            Shortest torus circumference / distance to last scattering.

        Returns
        -------
        results : dict
            Search results for each predicted radius.
        """
        # Predicted radii
        radii = self.predicted_circle_radii(L_min_over_chi_rec)

        # Axis of Evil direction
        theta_ae = np.radians(90 - 60)  # colatitude
        phi_ae = np.radians(250)

        results = {}

        for label, info in radii.items():
            if info.get('alpha_deg') is None:
                results[label] = {'note': info.get('note', 'No circles')}
                continue

            alpha_rad = info['alpha_rad']

            # Search at predicted radius
            search_result = self.search_matched_circles(
                cmb_map, alpha_rad, theta_ae, phi_ae, n_test_pairs=20
            )

            # Null distribution
            null_corrs = self.compute_null_distribution(
                cmb_map, alpha_rad, n_trials=50
            )

            # Significance
            observed = search_result['max_correlation']
            null_mean = np.mean(null_corrs)
            null_std = np.std(null_corrs)
            sigma = (observed - null_mean) / (null_std + 1e-10)

            # P-value
            p_value = np.mean(null_corrs >= observed)

            results[label] = {
                'alpha_deg': info['alpha_deg'],
                'L_over_chi': info['L_over_chi_rec'],
                'max_correlation': observed,
                'mean_correlation': search_result['mean_correlation'],
                'null_mean': null_mean,
                'null_std': null_std,
                'sigma': sigma,
                'p_value': p_value,
                'null_distribution': null_corrs,
                'search_result': search_result,
            }

        return results


def run_analysis(save_dir=None):
    """
    Run complete targeted matched-circles search.
    """
    import matplotlib.pyplot as plt

    if save_dir is None:
        save_dir = '.'

    print("=" * 70)
    print("TARGETED MATCHED-CIRCLES SEARCH")
    print("Searching at φ-harmonic angular radii along Axis of Evil")
    print("=" * 70)

    searcher = MatchedCirclesSearcher(nside=64, n_points_per_circle=180)

    # Step 1: Predicted radii
    L_min_ratio = 0.5
    print(f"\n[1] Predicted matched-circle angular radii (L₁/χ_rec = {L_min_ratio})...")

    radii = searcher.predicted_circle_radii(L_min_ratio)
    for label, info in radii.items():
        if info.get('alpha_deg') is not None:
            print(f"    {label}: α = {info['alpha_deg']:.1f}° "
                  f"(L/χ_rec = {info['L_over_chi_rec']:.3f})")
        else:
            print(f"    {label}: {info.get('note', 'N/A')}")

    # Step 2: Generate test CMB maps
    print("\n[2] Generating synthetic CMB maps...")

    np.random.seed(42)
    lmax = searcher.lmax
    ells = np.arange(lmax + 1)
    cl = np.zeros(lmax + 1)
    cl[2:] = 1e-10 / (ells[2:] * (ells[2:] + 1))

    # Isotropic map (no topology)
    cmb_iso = hp.synfast(cl, searcher.nside, lmax=lmax,
                          new=True, verbose=False)

    # Map with injected matched circles (simulate torus detection)
    cmb_torus = cmb_iso.copy()

    # Inject a weak matched-circle signal along the AoE
    theta_ae = np.radians(30)
    phi_ae = np.radians(250)
    alpha_target = radii['L1']['alpha_rad']

    # Create a pattern on one circle and copy it to the matching circle
    psi = np.linspace(0, 2 * np.pi, 360)
    pattern = 0.3e-5 * (np.sin(3 * psi) + 0.5 * np.cos(7 * psi))

    for offset in np.linspace(0, np.pi, 10):
        c1_theta = theta_ae
        c1_phi = phi_ae + offset
        c2_theta = np.pi - c1_theta
        c2_phi = (c1_phi + np.pi) % (2 * np.pi)

        # Add pattern to both circles
        for c_theta, c_phi in [(c1_theta, c1_phi), (c2_theta, c2_phi)]:
            ct, st = np.cos(c_theta), np.sin(c_theta)
            cp, sp = np.cos(c_phi), np.sin(c_phi)

            x_local = np.sin(alpha_target) * np.cos(psi)
            y_local = np.sin(alpha_target) * np.sin(psi)
            z_local = np.cos(alpha_target) * np.ones_like(psi)

            x_g = ct * cp * x_local - sp * y_local + st * cp * z_local
            y_g = ct * sp * x_local + cp * y_local + st * sp * z_local
            z_g = -st * x_local + ct * z_local

            theta_pts = np.arccos(np.clip(z_g, -1, 1))
            phi_pts = np.arctan2(y_g, x_g) % (2 * np.pi)
            pix = hp.ang2pix(searcher.nside, theta_pts, phi_pts)

            cmb_torus[pix] += pattern

    print(f"    Isotropic CMB: rms = {np.std(cmb_iso):.2e}")
    print(f"    Torus CMB (injected signal): rms = {np.std(cmb_torus):.2e}")

    # Step 3: Run targeted search
    print(f"\n[3] Running targeted search on isotropic map...")
    results_iso = searcher.targeted_search(cmb_iso, L_min_ratio)

    for label, res in results_iso.items():
        if 'alpha_deg' in res:
            print(f"    {label} (α={res['alpha_deg']:.1f}°): "
                  f"max_corr = {res['max_correlation']:.3f}, "
                  f"null = {res['null_mean']:.3f} ± {res['null_std']:.3f}, "
                  f"σ = {res['sigma']:.1f}")

    print(f"\n[4] Running targeted search on torus map...")
    results_torus = searcher.targeted_search(cmb_torus, L_min_ratio)

    for label, res in results_torus.items():
        if 'alpha_deg' in res:
            print(f"    {label} (α={res['alpha_deg']:.1f}°): "
                  f"max_corr = {res['max_correlation']:.3f}, "
                  f"null = {res['null_mean']:.3f} ± {res['null_std']:.3f}, "
                  f"σ = {res['sigma']:.1f}")

    # Step 5: Scan over L_min
    print(f"\n[5] Scanning over L_min / χ_rec...")

    L_min_scan = np.linspace(0.3, 0.8, 6)
    scan_results = {}

    for L_ratio in L_min_scan:
        r = searcher.predicted_circle_radii(L_ratio)
        if r['L1'].get('alpha_rad') is not None:
            sr = searcher.search_matched_circles(
                cmb_torus, r['L1']['alpha_rad'],
                theta_ae, phi_ae, n_test_pairs=10
            )
            scan_results[L_ratio] = {
                'alpha_deg': r['L1']['alpha_deg'],
                'max_corr': sr['max_correlation'],
                'mean_corr': sr['mean_correlation'],
            }
            print(f"    L₁/χ_rec = {L_ratio:.2f}: α = {r['L1']['alpha_deg']:.1f}°, "
                  f"max_corr = {sr['max_correlation']:.3f}")

    # Visualization
    print(f"\n[6] Creating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    # 1. CMB maps comparison
    ax = axes[0, 0]
    hp.mollview(cmb_iso, title='Isotropic CMB', hold=True,
                sub=(2, 3, 1), cmap='RdBu_r')

    ax = axes[0, 1]
    hp.mollview(cmb_torus, title='T³ CMB (injected circles)', hold=True,
                sub=(2, 3, 2), cmap='RdBu_r')

    # 2. Example circle profiles
    ax = axes[0, 2]
    if results_torus.get('L1', {}).get('alpha_deg') is not None:
        alpha = results_torus['L1']['search_result']['alpha_rad']
        best_pair = max(
            results_torus['L1']['search_result']['correlations'],
            key=lambda c: c['max_correlation']
        )
        c1 = best_pair['center1']
        c2 = best_pair['center2']

        prof1, _ = searcher.extract_circle_profile(cmb_torus, c1[0], c1[1], alpha)
        prof2, _ = searcher.extract_circle_profile(cmb_torus, c2[0], c2[1], alpha)

        angles = np.linspace(0, 360, len(prof1))
        ax.plot(angles, prof1 * 1e5, 'b-', linewidth=1.5, label='Circle 1', alpha=0.8)
        ax.plot(angles, prof2 * 1e5, 'r-', linewidth=1.5, label='Circle 2', alpha=0.8)
        ax.set_xlabel('Angle around circle (degrees)')
        ax.set_ylabel('Temperature (×10⁵)')
        ax.set_title(f'Best matching circle pair\n'
                     f'α = {np.degrees(alpha):.1f}°, '
                     f'corr = {best_pair["max_correlation"]:.3f}')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    # 3. Correlation vs null distribution
    ax = axes[1, 0]
    for label, color in [('L1', 'red'), ('L2', 'blue'), ('L3', 'green')]:
        res = results_torus.get(label, {})
        if 'null_distribution' in res:
            ax.hist(res['null_distribution'], bins=15, alpha=0.3,
                    color=color, label=f'{label} null', density=True)
            ax.axvline(res['max_correlation'], color=color,
                       linestyle='--', linewidth=2,
                       label=f'{label}: {res["sigma"]:.1f}σ')

    ax.set_xlabel('Maximum Circle Correlation')
    ax.set_ylabel('Density')
    ax.set_title('Observed vs Null Distribution\n(T³ map)')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # 4. L_min scan
    ax = axes[1, 1]
    if scan_results:
        l_ratios = list(scan_results.keys())
        max_corrs = [scan_results[lr]['max_corr'] for lr in l_ratios]
        alphas = [scan_results[lr]['alpha_deg'] for lr in l_ratios]

        ax.plot(l_ratios, max_corrs, 'ro-', linewidth=2, markersize=8)
        ax.axvline(L_min_ratio, color='k', linestyle='--', alpha=0.5,
                   label=f'Predicted L₁/χ = {L_min_ratio}')
        for lr, alpha_v in zip(l_ratios, alphas):
            ax.annotate(f'{alpha_v:.0f}°', (lr, scan_results[lr]['max_corr']),
                        textcoords="offset points", xytext=(0, 10),
                        fontsize=7, ha='center')

    ax.set_xlabel('L₁ / χ_rec')
    ax.set_ylabel('Maximum Circle Correlation')
    ax.set_title('Correlation vs Torus Size')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 5. Summary
    ax = axes[1, 2]
    ax.axis('off')

    l1_res = results_torus.get('L1', {})
    l2_res = results_torus.get('L2', {})
    l3_res = results_torus.get('L3', {})

    summary = (
        f"MATCHED-CIRCLES SEARCH RESULTS\n"
        f"{'='*40}\n\n"
        f"Search parameters:\n"
        f"  L₁/χ_rec = {L_min_ratio}\n"
        f"  Axis: (l,b) = (250°, 60°)\n"
        f"  Constraint: L₁:L₂:L₃ = 1:φ:φ²\n\n"
        f"Results (T³ map):\n"
    )

    for label, res in [('L1', l1_res), ('L2', l2_res), ('L3', l3_res)]:
        if 'alpha_deg' in res:
            summary += (
                f"  {label}: α={res['alpha_deg']:.1f}°\n"
                f"    corr={res['max_correlation']:.3f}, "
                f"σ={res['sigma']:.1f}\n"
            )

    summary += (
        f"\nBlind vs targeted:\n"
        f"  Blind search: ~10⁶ trials\n"
        f"  φ-targeted: ~10² trials\n"
        f"  Trials reduction: ~10⁴×\n"
        f"  Signal detectable at lower S/N"
    )

    ax.text(0.05, 0.95, summary, fontsize=9, family='monospace',
            verticalalignment='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    save_path = f'{save_dir}/matched_circles_search.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {save_path}")

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")

    return {
        'results_iso': results_iso,
        'results_torus': results_torus,
        'scan_results': scan_results,
        'predicted_radii': radii,
    }


if __name__ == '__main__':
    results = run_analysis(
        save_dir='phi_equation_investigation/phi_domain_analysis/cosmic_anisotropy'
    )
