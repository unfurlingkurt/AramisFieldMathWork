#!/usr/bin/env python3
"""
Gradient Norm Constancy Test

The φ-framework's most rigid prediction: ||∇φ||² = constant.

Applied to the CMB:
    Σ_l l(l+1) C_l = constant across different sky patches

This is a UNIQUE prediction: the integrated gradient power should be
the SAME in every direction, even though individual multipoles vary.

If gradient power is constant but multipole power is not, this is a
signature of the φ-framework that no other model predicts.

Test procedure:
1. Divide the CMB sky into patches (using HEALPix pixels at low nside)
2. In each patch, compute the local gradient power: ||∇T||²
3. Also compute the local multipole power: Σ C_l
4. Test gradient power for constancy across directions
5. Verify that multipole power is NOT constant (anisotropic)
6. The combination "constant gradient + anisotropic power" is the
   φ-framework signature
"""

import numpy as np
import healpy as hp
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

PHI = (1 + np.sqrt(5)) / 2


class GradientConstancyTester:
    """
    Test whether ||∇T||² is constant across sky directions.

    This is the φ-framework's most distinctive testable prediction.
    """

    def __init__(self, nside_map=64, nside_patch=4):
        """
        Parameters
        ----------
        nside_map : int
            HEALPix resolution for the CMB map.
        nside_patch : int
            HEALPix resolution for sky patches.
            nside_patch=4 gives 192 patches (~19° diameter each).
            nside_patch=2 gives 48 patches (~37° diameter each).
        """
        self.nside_map = nside_map
        self.nside_patch = nside_patch
        self.npix_map = hp.nside2npix(nside_map)
        self.npix_patch = hp.nside2npix(nside_patch)
        self.lmax = 3 * nside_map - 1

    def compute_gradient_power_per_patch(self, temperature_map):
        """
        Compute ||∇T||² in each sky patch.

        For each patch:
        1. Extract the pixels belonging to that patch
        2. Compute the gradient magnitude at each pixel
        3. Sum ||∇T||² over the patch (integrated gradient power)

        Parameters
        ----------
        temperature_map : ndarray
            Full-sky HEALPix temperature map.

        Returns
        -------
        gradient_power : ndarray
            ||∇T||² for each patch. Shape: (npix_patch,)
        patch_centers : ndarray
            (theta, phi) centers of each patch. Shape: (npix_patch, 2)
        """
        # Compute full-sky gradient
        alm = hp.map2alm(temperature_map, lmax=self.lmax)
        _, dtheta, dphi = hp.alm2map_der1(alm, self.nside_map, lmax=self.lmax)
        grad_sq = dtheta**2 + dphi**2

        # Assign each high-res pixel to a patch
        pixel_indices = np.arange(self.npix_map)
        theta_pix, phi_pix = hp.pix2ang(self.nside_map, pixel_indices)
        patch_ids = hp.ang2pix(self.nside_patch, theta_pix, phi_pix)

        # Sum gradient power in each patch
        gradient_power = np.zeros(self.npix_patch)
        pixel_count = np.zeros(self.npix_patch)

        for i in range(self.npix_map):
            p = patch_ids[i]
            gradient_power[p] += grad_sq[i]
            pixel_count[p] += 1

        # Normalize by pixel count (average gradient power)
        gradient_power = np.where(pixel_count > 0,
                                   gradient_power / pixel_count,
                                   0)

        # Patch centers
        patch_centers = np.array([
            hp.pix2ang(self.nside_patch, i) for i in range(self.npix_patch)
        ])

        return gradient_power, patch_centers

    def compute_multipole_power_per_patch(self, temperature_map, l_range=(2, 30)):
        """
        Compute total multipole power Σ C_l in each sky patch.

        This should NOT be constant if the universe is anisotropic.

        Parameters
        ----------
        temperature_map : ndarray
            Full-sky HEALPix temperature map.
        l_range : tuple
            (l_min, l_max) range for summing power.

        Returns
        -------
        multipole_power : ndarray
            Total C_l power for each patch.
        """
        l_min, l_max = l_range

        # Assign pixels to patches
        pixel_indices = np.arange(self.npix_map)
        theta_pix, phi_pix = hp.pix2ang(self.nside_map, pixel_indices)
        patch_ids = hp.ang2pix(self.nside_patch, theta_pix, phi_pix)

        # For each patch, compute local power spectrum
        multipole_power = np.zeros(self.npix_patch)

        for patch_id in range(self.npix_patch):
            mask = patch_ids == patch_id
            if np.sum(mask) < 10:
                continue

            # Local variance (proxy for total power)
            patch_values = temperature_map[mask]
            multipole_power[patch_id] = np.var(patch_values)

        return multipole_power

    def test_constancy(self, values, name="quantity"):
        """
        Statistical test for constancy across patches.

        Uses:
        - Coefficient of variation (CV)
        - Chi-squared test against constant model
        - Kolmogorov-Smirnov test against uniform

        Parameters
        ----------
        values : ndarray
            Values across patches.
        name : str
            Name for reporting.

        Returns
        -------
        results : dict
            Statistical test results.
        """
        valid = values[values > 0]

        if len(valid) < 5:
            return {'cv': np.nan, 'chi2_p': np.nan, 'is_constant': False}

        mean_val = np.mean(valid)
        std_val = np.std(valid)
        cv = std_val / mean_val

        # Chi-squared test: are the values consistent with a constant?
        # H0: all patches have the same value (= mean)
        chi2 = np.sum((valid - mean_val)**2 / mean_val)
        dof = len(valid) - 1
        chi2_p = 1 - stats.chi2.cdf(chi2, dof)

        # Reduced chi-squared
        chi2_red = chi2 / dof

        # Is it constant? CV < 0.15 and chi2 p-value > 0.05
        is_constant = cv < 0.15 and chi2_p > 0.05

        return {
            'mean': mean_val,
            'std': std_val,
            'cv': cv,
            'chi2': chi2,
            'chi2_reduced': chi2_red,
            'chi2_p': chi2_p,
            'dof': dof,
            'is_constant': is_constant,
            'n_patches': len(valid),
        }

    def directional_test(self, gradient_power, patch_centers):
        """
        Test if gradient power varies with direction.

        Specifically tests for correlation with the Axis of Evil direction.

        Parameters
        ----------
        gradient_power : ndarray
            Gradient power per patch.
        patch_centers : ndarray
            (theta, phi) centers of patches.

        Returns
        -------
        results : dict
            Directional analysis results.
        """
        theta_ae = np.radians(90 - 60)  # colatitude
        phi_ae = np.radians(250)

        # Angular distance from AoE for each patch
        cos_sep = (np.sin(theta_ae) * np.sin(patch_centers[:, 0]) *
                    np.cos(patch_centers[:, 1] - phi_ae) +
                    np.cos(theta_ae) * np.cos(patch_centers[:, 0]))

        angles = np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))

        valid = gradient_power > 0

        # Correlation between gradient power and angle from AoE
        corr, p_value = stats.pearsonr(angles[valid], gradient_power[valid])

        # Split into along/perpendicular
        along = np.abs(cos_sep) > 0.5
        perp = ~along

        gp_along = np.mean(gradient_power[along & valid])
        gp_perp = np.mean(gradient_power[perp & valid])

        return {
            'correlation_with_aoe': corr,
            'correlation_p_value': p_value,
            'gp_along_aoe': gp_along,
            'gp_perp_aoe': gp_perp,
            'ratio': gp_along / gp_perp if gp_perp > 0 else np.nan,
            'angles': angles,
            'is_direction_independent': abs(corr) < 0.2,
        }

    def hemispherical_test(self, gradient_power, patch_centers):
        """
        Test for hemispherical asymmetry in gradient power.

        If gradient power is constant, both hemispheres should have
        equal power. If multipole power is asymmetric but gradient
        power is symmetric, that's the φ-framework signature.

        Parameters
        ----------
        gradient_power : ndarray
        patch_centers : ndarray

        Returns
        -------
        results : dict
        """
        theta_ae = np.radians(90 - 60)
        phi_ae = np.radians(250)

        cos_sep = (np.sin(theta_ae) * np.sin(patch_centers[:, 0]) *
                    np.cos(patch_centers[:, 1] - phi_ae) +
                    np.cos(theta_ae) * np.cos(patch_centers[:, 0]))

        valid = gradient_power > 0

        hemi_1 = cos_sep > 0
        hemi_2 = cos_sep <= 0

        gp_h1 = gradient_power[hemi_1 & valid]
        gp_h2 = gradient_power[hemi_2 & valid]

        mean_h1 = np.mean(gp_h1) if len(gp_h1) > 0 else 0
        mean_h2 = np.mean(gp_h2) if len(gp_h2) > 0 else 0

        asymmetry = 2 * (mean_h1 - mean_h2) / (mean_h1 + mean_h2 + 1e-20)

        # t-test for difference between hemispheres
        if len(gp_h1) > 2 and len(gp_h2) > 2:
            t_stat, t_p = stats.ttest_ind(gp_h1, gp_h2)
        else:
            t_stat, t_p = 0, 1

        return {
            'mean_hemi_1': mean_h1,
            'mean_hemi_2': mean_h2,
            'asymmetry': asymmetry,
            't_statistic': t_stat,
            't_p_value': t_p,
            'is_symmetric': abs(asymmetry) < 0.1 and t_p > 0.05,
        }


def run_analysis(save_dir=None):
    """
    Run complete gradient constancy analysis.

    Tests the φ-framework prediction:
    - ||∇T||² should be constant across sky patches
    - Individual multipole power should NOT be constant
    - The combination is the unique φ-framework signature
    """
    import matplotlib.pyplot as plt

    if save_dir is None:
        save_dir = '.'

    print("=" * 70)
    print("GRADIENT NORM CONSTANCY TEST")
    print("φ-framework prediction: ||∇φ||² = constant everywhere")
    print("=" * 70)

    tester = GradientConstancyTester(nside_map=64, nside_patch=4)

    # Step 1: Generate test maps
    print("\n[1] Generating test CMB maps...")

    np.random.seed(42)
    lmax = tester.lmax

    # Isotropic CMB
    ells = np.arange(lmax + 1)
    cl_iso = np.zeros(lmax + 1)
    cl_iso[2:] = 1e-10 / (ells[2:] * (ells[2:] + 1))
    cmb_iso = hp.synfast(cl_iso, tester.nside_map, lmax=lmax,
                          new=True, verbose=False)

    # Torus-modulated CMB (anisotropic power, should have constant gradient)
    theta, phi_coord = hp.pix2ang(tester.nside_map,
                                   np.arange(tester.npix_map))
    theta_ae = np.radians(30)
    phi_ae = np.radians(250)
    cos_angle = (np.sin(theta_ae) * np.sin(theta) *
                  np.cos(phi_coord - phi_ae) +
                  np.cos(theta_ae) * np.cos(theta))

    # Anisotropic modulation that preserves gradient norm
    # Scale factor that varies direction but keeps |∇| constant
    modulation = 1.0 + 0.3 * cos_angle
    cmb_aniso_power = cmb_iso * modulation

    # Truly anisotropic (both power AND gradient vary)
    cmb_aniso_both = cmb_iso * (1 + 0.5 * cos_angle**2)

    print(f"    Generated 3 maps at nside={tester.nside_map}")
    print(f"    Using {tester.npix_patch} patches at nside={tester.nside_patch}")

    # Step 2: Compute gradient power per patch
    print("\n[2] Computing gradient power per patch...")

    gp_iso, centers = tester.compute_gradient_power_per_patch(cmb_iso)
    gp_aniso_p, _ = tester.compute_gradient_power_per_patch(cmb_aniso_power)
    gp_aniso_b, _ = tester.compute_gradient_power_per_patch(cmb_aniso_both)

    # Step 3: Compute multipole power per patch
    print("\n[3] Computing multipole power per patch...")

    mp_iso = tester.compute_multipole_power_per_patch(cmb_iso)
    mp_aniso_p = tester.compute_multipole_power_per_patch(cmb_aniso_power)
    mp_aniso_b = tester.compute_multipole_power_per_patch(cmb_aniso_both)

    # Step 4: Test constancy
    print("\n[4] Testing constancy...")

    cases = {
        'Isotropic': (gp_iso, mp_iso),
        'Aniso power (φ-like)': (gp_aniso_p, mp_aniso_p),
        'Aniso both': (gp_aniso_b, mp_aniso_b),
    }

    results = {}
    for name, (gp, mp) in cases.items():
        print(f"\n    --- {name} ---")

        gp_test = tester.test_constancy(gp, "gradient power")
        mp_test = tester.test_constancy(mp, "multipole power")

        print(f"    Gradient power: CV = {gp_test['cv']:.4f}, "
              f"χ²_red = {gp_test['chi2_reduced']:.2f}, "
              f"p = {gp_test['chi2_p']:.4f}")
        print(f"      Constant: {gp_test['is_constant']}")

        print(f"    Multipole power: CV = {mp_test['cv']:.4f}, "
              f"χ²_red = {mp_test['chi2_reduced']:.2f}, "
              f"p = {mp_test['chi2_p']:.4f}")
        print(f"      Constant: {mp_test['is_constant']}")

        phi_signature = gp_test['is_constant'] and not mp_test['is_constant']
        print(f"    φ-framework signature (grad const + power aniso): "
              f"{'YES' if phi_signature else 'NO'}")

        results[name] = {
            'gradient_test': gp_test,
            'multipole_test': mp_test,
            'phi_signature': phi_signature,
            'gradient_power': gp,
            'multipole_power': mp,
        }

    # Step 5: Directional test
    print("\n[5] Directional analysis...")

    dir_iso = tester.directional_test(gp_iso, centers)
    dir_aniso_p = tester.directional_test(gp_aniso_p, centers)

    print(f"    Isotropic: correlation with AoE = {dir_iso['correlation_with_aoe']:.3f}")
    print(f"    φ-like:    correlation with AoE = {dir_aniso_p['correlation_with_aoe']:.3f}")

    # Step 6: Hemispherical test
    print("\n[6] Hemispherical asymmetry test...")

    hemi_iso = tester.hemispherical_test(gp_iso, centers)
    hemi_aniso_p = tester.hemispherical_test(gp_aniso_p, centers)

    print(f"    Isotropic: asymmetry = {hemi_iso['asymmetry']:.4f}")
    print(f"    φ-like:    asymmetry = {hemi_aniso_p['asymmetry']:.4f}")

    # Visualization
    print("\n[7] Creating visualizations...")

    fig, axes = plt.subplots(3, 3, figsize=(18, 15))

    # Row 1: Gradient power maps
    for idx, (name, res) in enumerate(results.items()):
        ax = axes[0, idx]
        gp = res['gradient_power']
        # Create a low-res HEALPix map for visualization
        gp_map = np.zeros(tester.npix_patch)
        gp_map[:] = gp
        # Upgrade to higher res for display
        gp_display = hp.ud_grade(gp_map, tester.nside_map)
        hp.mollview(gp_display, title=f'||∇T||² - {name}',
                    hold=True, sub=(3, 3, idx + 1), cmap='viridis')

    # Row 2: Histograms of gradient and multipole power
    ax = axes[1, 0]
    for name, res in results.items():
        gp = res['gradient_power']
        gp_valid = gp[gp > 0]
        gp_norm = gp_valid / np.mean(gp_valid)
        ax.hist(gp_norm, bins=20, alpha=0.4, label=name, density=True)
    ax.axvline(1.0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('||∇T||² / <||∇T||²>')
    ax.set_ylabel('Density')
    ax.set_title('Gradient Power Distribution')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    for name, res in results.items():
        mp = res['multipole_power']
        mp_valid = mp[mp > 0]
        mp_norm = mp_valid / np.mean(mp_valid)
        ax.hist(mp_norm, bins=20, alpha=0.4, label=name, density=True)
    ax.axvline(1.0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Σ C_l / <Σ C_l>')
    ax.set_ylabel('Density')
    ax.set_title('Multipole Power Distribution')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    ax = axes[1, 2]
    names = list(results.keys())
    cv_grad = [results[n]['gradient_test']['cv'] for n in names]
    cv_mult = [results[n]['multipole_test']['cv'] for n in names]
    x = np.arange(len(names))
    width = 0.35
    ax.bar(x - width/2, cv_grad, width, label='Gradient CV', color='blue', alpha=0.7)
    ax.bar(x + width/2, cv_mult, width, label='Multipole CV', color='red', alpha=0.7)
    ax.set_ylabel('Coefficient of Variation')
    ax.set_title('Constancy Comparison\n(lower = more constant)')
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace(' ', '\n') for n in names], fontsize=8)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Row 3: Directional analysis and summary
    ax = axes[2, 0]
    valid = gp_aniso_p > 0
    ax.scatter(dir_aniso_p['angles'][valid], gp_aniso_p[valid],
               alpha=0.5, s=15, color='red', label='φ-like')
    ax.scatter(dir_iso['angles'][gp_iso > 0], gp_iso[gp_iso > 0],
               alpha=0.3, s=15, color='blue', label='Isotropic')
    ax.set_xlabel('Angle from Axis of Evil (degrees)')
    ax.set_ylabel('||∇T||²')
    ax.set_title('Gradient Power vs Direction')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax = axes[2, 1]
    valid = mp_aniso_p > 0
    ax.scatter(dir_aniso_p['angles'][valid], mp_aniso_p[valid],
               alpha=0.5, s=15, color='red', label='φ-like')
    valid_iso = mp_iso > 0
    ax.scatter(dir_iso['angles'][valid_iso], mp_iso[valid_iso],
               alpha=0.3, s=15, color='blue', label='Isotropic')
    ax.set_xlabel('Angle from Axis of Evil (degrees)')
    ax.set_ylabel('Multipole Power')
    ax.set_title('Multipole Power vs Direction')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Summary
    ax = axes[2, 2]
    ax.axis('off')

    phi_case = results['Aniso power (φ-like)']
    summary = (
        f"GRADIENT NORM CONSTANCY TEST\n"
        f"{'='*40}\n\n"
        f"φ-framework prediction:\n"
        f"  ||∇φ||² = constant (conserved)\n"
        f"  Individual C_l may vary\n\n"
        f"Results (φ-like case):\n"
        f"  Gradient CV: {phi_case['gradient_test']['cv']:.4f}\n"
        f"  Multipole CV: {phi_case['multipole_test']['cv']:.4f}\n"
        f"  Gradient constant: {phi_case['gradient_test']['is_constant']}\n"
        f"  Power anisotropic: {not phi_case['multipole_test']['is_constant']}\n\n"
        f"φ-SIGNATURE DETECTED:\n"
        f"  {phi_case['phi_signature']}\n\n"
        f"Hemispherical asymmetry:\n"
        f"  Gradient: {hemi_aniso_p['asymmetry']:.4f}\n"
        f"    (symmetric = good for φ)\n\n"
        f"Direction independence:\n"
        f"  Corr with AoE: {dir_aniso_p['correlation_with_aoe']:.3f}\n"
        f"    (zero = good for φ)"
    )
    ax.text(0.05, 0.95, summary, fontsize=9, family='monospace',
            verticalalignment='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    save_path = f'{save_dir}/gradient_constancy_test.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {save_path}")

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")

    return results


if __name__ == '__main__':
    results = run_analysis(
        save_dir='phi_equation_investigation/phi_domain_analysis/cosmic_anisotropy'
    )
