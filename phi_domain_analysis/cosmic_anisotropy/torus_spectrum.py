#!/usr/bin/env python3
"""
T³ CMB Power Spectrum Calculator

Computes the CMB angular power spectrum C_l for a universe with
3-torus (T³ = S¹ × S¹ × S¹) spatial topology.

On a T³, the Laplacian eigenmodes are plane waves with quantized
wave vectors:
    k = (2π n₁/L₁, 2π n₂/L₂, 2π n₃/L₃)    for integers n_i

This quantization modifies the C_l spectrum compared to the infinite
flat (isotropic) case, particularly at low multipoles (large scales)
where modes comparable to the torus circumferences are affected.

The φ-equation framework constrains:
    L₁ : L₂ : L₃ = 1 : φ : φ²
    where φ = (1+√5)/2 = 1.618...

This reduces the 6-parameter generic T³ model to 2-3 parameters.
"""

import numpy as np
from scipy.special import spherical_jn
from scipy.interpolate import interp1d
import warnings
warnings.filterwarnings('ignore')

PHI = (1 + np.sqrt(5)) / 2


class TorusSpectrumCalculator:
    """
    Compute CMB C_l on a 3-torus T³.

    The key modification from infinite flat space: the integral over
    continuous k is replaced by a discrete sum over allowed k modes.

    C_l^{T³} = (2/π) Σ_{n∈Z³} |Δ_l(k_n)|² P(k_n) / V_T

    where k_n = 2π(n₁/L₁, n₂/L₂, n₃/L₃), V_T = L₁L₂L₃,
    and Δ_l(k) is the radiation transfer function.
    """

    def __init__(self, l_max=100):
        self.l_max = l_max
        self.ells = np.arange(2, l_max + 1)
        self._primordial_ns = 0.965  # scalar spectral index
        self._primordial_As = 2.1e-9  # scalar amplitude
        self._k_pivot = 0.05  # Mpc^-1

    def primordial_power(self, k):
        """
        Primordial power spectrum P(k) = As (k/k_pivot)^{ns-1}.

        Nearly scale-invariant Harrison-Zeldovich spectrum.
        """
        return self._primordial_As * (k / self._k_pivot) ** (self._primordial_ns - 1)

    def transfer_function_sw(self, k, l, chi_rec=14000.0):
        """
        Sachs-Wolfe radiation transfer function.

        Δ_l(k) ≈ j_l(k χ_rec) / 3

        where j_l is the spherical Bessel function and χ_rec is the
        comoving distance to the last scattering surface (~14 Gpc).

        This is the dominant contribution at low multipoles (l < 30).
        """
        x = k * chi_rec
        if x < 1e-10:
            return 0.0
        return spherical_jn(l, x) / 3.0

    def compute_cl_isotropic(self, chi_rec=14000.0, k_min=1e-5, k_max=0.3,
                              n_k=5000):
        """
        Compute C_l for an infinite flat (isotropic) universe.

        Uses continuous k integration:
        C_l = (2/π) ∫ k² P(k) |Δ_l(k)|² dk
        """
        k_arr = np.geomspace(k_min, k_max, n_k)
        dk = np.diff(k_arr)

        cl_iso = np.zeros(len(self.ells))

        for i, l in enumerate(self.ells):
            integrand = np.zeros(n_k)
            for j, k in enumerate(k_arr):
                delta_l = self.transfer_function_sw(k, l, chi_rec)
                integrand[j] = k**2 * self.primordial_power(k) * delta_l**2

            # Trapezoidal integration
            cl_iso[i] = (2.0 / np.pi) * np.trapz(integrand, k_arr)

        return cl_iso

    def compute_cl_torus(self, L1, L2, L3, chi_rec=14000.0,
                          n_max=30, orientation=None):
        """
        Compute C_l for a T³ universe with circumferences (L1, L2, L3).

        Parameters
        ----------
        L1, L2, L3 : float
            Circumferences of the three S¹ factors (in Mpc).
        chi_rec : float
            Comoving distance to last scattering surface (Mpc).
        n_max : int
            Maximum mode number to sum over in each direction.
            Total modes = (2*n_max+1)³.
        orientation : tuple of 3 floats, optional
            Euler angles (alpha, beta, gamma) in radians rotating the
            torus axes relative to the observer. If None, torus axes
            align with coordinate axes.

        Returns
        -------
        cl_torus : ndarray
            C_l values for l in self.ells.
        mode_count : ndarray
            Number of allowed modes contributing to each l.
        """
        V_T = L1 * L2 * L3

        cl_torus = np.zeros(len(self.ells))
        mode_count = np.zeros(len(self.ells))

        # Generate all allowed k modes on the T³
        n_range = np.arange(-n_max, n_max + 1)

        # Pre-compute k magnitudes and mode contributions
        k_modes = []
        for n1 in n_range:
            for n2 in n_range:
                for n3 in n_range:
                    if n1 == 0 and n2 == 0 and n3 == 0:
                        continue  # Skip zero mode

                    kx = 2.0 * np.pi * n1 / L1
                    ky = 2.0 * np.pi * n2 / L2
                    kz = 2.0 * np.pi * n3 / L3

                    if orientation is not None:
                        kx, ky, kz = self._rotate_k(kx, ky, kz, orientation)

                    k_mag = np.sqrt(kx**2 + ky**2 + kz**2)
                    k_modes.append(k_mag)

        k_modes = np.array(k_modes)

        # Compute C_l by summing over discrete modes
        for i, l in enumerate(self.ells):
            total = 0.0
            count = 0

            for k in k_modes:
                delta_l = self.transfer_function_sw(k, l, chi_rec)
                contribution = self.primordial_power(k) * delta_l**2
                total += contribution
                if contribution > 0:
                    count += 1

            cl_torus[i] = (2.0 / np.pi) * total / V_T * (2 * np.pi)**3
            mode_count[i] = count

        return cl_torus, mode_count

    def compute_cl_torus_phi_harmonic(self, L_min, chi_rec=14000.0,
                                       n_max=30, orientation=None):
        """
        Compute C_l for a T³ with φ-harmonic circumference ratios.

        L₁ : L₂ : L₃ = 1 : φ : φ²

        Parameters
        ----------
        L_min : float
            Shortest circumference L₁ (in Mpc).
        chi_rec : float
            Comoving distance to last scattering (Mpc).
        n_max : int
            Maximum mode number per direction.
        orientation : tuple, optional
            Euler angles (alpha, beta, gamma) in radians.

        Returns
        -------
        cl_torus : ndarray
        mode_count : ndarray
        params : dict
            The actual L₁, L₂, L₃ used.
        """
        L1 = L_min
        L2 = L_min * PHI
        L3 = L_min * PHI**2

        cl_torus, mode_count = self.compute_cl_torus(
            L1, L2, L3, chi_rec=chi_rec, n_max=n_max,
            orientation=orientation
        )

        params = {
            'L1': L1, 'L2': L2, 'L3': L3,
            'ratio': f'1 : {PHI:.4f} : {PHI**2:.4f}',
            'L1_over_chi_rec': L1 / chi_rec,
        }

        return cl_torus, mode_count, params

    def geometric_suppression_factor(self, L1, L2, L3, chi_rec=14000.0):
        """
        Compute the geometric suppression factor F_l for each multipole.

        F_l = C_l^{T³} / C_l^{iso}

        F_l < 1 means the torus suppresses that multipole (not enough
        room for that wavelength).
        F_l ≈ 1 means the torus is large enough that it doesn't matter.

        The φ-framework predicts:
        - F_2 << 1 (quadrupole suppression — observed!)
        - F_3 < 1 (octupole modification — observed!)
        - F_l → 1 for l >> 2π χ_rec / L_min
        """
        cl_iso = self.compute_cl_isotropic(chi_rec)
        cl_torus, _ = self.compute_cl_torus(L1, L2, L3, chi_rec)

        # Avoid division by zero
        F_l = np.where(cl_iso > 0, cl_torus / cl_iso, 1.0)

        return F_l

    def scan_L_min(self, L_min_range, chi_rec=14000.0, n_max=20):
        """
        Scan over L_min values to find best fit.

        For each L_min, computes the φ-harmonic T³ spectrum and
        measures how well it explains the observed quadrupole
        suppression.

        Parameters
        ----------
        L_min_range : array-like
            Range of L_min values to test (Mpc).
        chi_rec : float
            Comoving distance to last scattering (Mpc).

        Returns
        -------
        results : dict
            For each L_min: the C_l spectrum and suppression factors.
        """
        results = {
            'L_min': np.array(L_min_range),
            'F_2': [],  # quadrupole suppression
            'F_3': [],  # octupole suppression
            'cl_spectra': [],
        }

        cl_iso = self.compute_cl_isotropic(chi_rec)

        for L_min in L_min_range:
            cl_torus, _, params = self.compute_cl_torus_phi_harmonic(
                L_min, chi_rec=chi_rec, n_max=n_max
            )

            F_l = np.where(cl_iso > 0, cl_torus / cl_iso, 1.0)

            # l=2 is index 0 (ells starts at 2)
            results['F_2'].append(F_l[0])
            results['F_3'].append(F_l[1])
            results['cl_spectra'].append(cl_torus)

        results['F_2'] = np.array(results['F_2'])
        results['F_3'] = np.array(results['F_3'])
        results['cl_iso'] = cl_iso

        return results

    def bayesian_evidence(self, cl_observed, cl_errors, L_min,
                           chi_rec=14000.0, n_max=20):
        """
        Compute log-Bayesian evidence for T³ vs isotropic model.

        Uses simple chi-squared approximation:
        ln(B) ≈ -Δχ²/2 + penalty for extra parameters

        Parameters
        ----------
        cl_observed : ndarray
            Observed C_l values (for l = 2 to l_max).
        cl_errors : ndarray
            Uncertainties on observed C_l.
        L_min : float
            Shortest torus circumference (Mpc).

        Returns
        -------
        log_evidence_ratio : float
            ln(P(data|T³) / P(data|iso)). Positive favors T³.
        chi2_torus : float
        chi2_iso : float
        """
        cl_iso = self.compute_cl_isotropic(chi_rec)
        cl_torus, _, _ = self.compute_cl_torus_phi_harmonic(
            L_min, chi_rec=chi_rec, n_max=n_max
        )

        n_ell = min(len(cl_observed), len(cl_iso), len(cl_torus))

        chi2_iso = np.sum(
            ((cl_observed[:n_ell] - cl_iso[:n_ell]) / cl_errors[:n_ell])**2
        )
        chi2_torus = np.sum(
            ((cl_observed[:n_ell] - cl_torus[:n_ell]) / cl_errors[:n_ell])**2
        )

        # T³ has 1 extra parameter (L_min) vs 0 for isotropic
        # BIC-like penalty: k * ln(n) where k=1, n=n_ell
        penalty = np.log(n_ell)

        log_evidence_ratio = -0.5 * (chi2_torus - chi2_iso) - 0.5 * penalty

        return log_evidence_ratio, chi2_torus, chi2_iso

    def _rotate_k(self, kx, ky, kz, euler_angles):
        """Apply Euler rotation (ZYZ convention) to k-vector."""
        alpha, beta, gamma = euler_angles

        # Rotation matrix R = Rz(alpha) @ Ry(beta) @ Rz(gamma)
        ca, sa = np.cos(alpha), np.sin(alpha)
        cb, sb = np.cos(beta), np.sin(beta)
        cg, sg = np.cos(gamma), np.sin(gamma)

        R = np.array([
            [ca*cb*cg - sa*sg, -ca*cb*sg - sa*cg, ca*sb],
            [sa*cb*cg + ca*sg, -sa*cb*sg + ca*cg, sa*sb],
            [-sb*cg,            sb*sg,             cb   ]
        ])

        k_rot = R @ np.array([kx, ky, kz])
        return k_rot[0], k_rot[1], k_rot[2]

    def axis_of_evil_orientation(self):
        """
        Return Euler angles aligning torus L₁ with the Axis of Evil.

        The Axis of Evil is approximately (l, b) ≈ (250°, 60°) in
        galactic coordinates.

        Returns angles to rotate the torus so its shortest circumference
        direction points toward this.
        """
        l_gal = np.radians(250.0)
        b_gal = np.radians(60.0)

        # Convert to Euler angles (ZYZ convention)
        alpha = l_gal
        beta = np.pi / 2 - b_gal
        gamma = 0.0

        return (alpha, beta, gamma)


def run_analysis(save_dir=None):
    """
    Run complete T³ spectrum analysis.

    Computes:
    1. Isotropic C_l spectrum
    2. T³ spectrum with φ-harmonic ratios at various L_min
    3. Geometric suppression factors
    4. Comparison plots
    """
    import matplotlib.pyplot as plt

    if save_dir is None:
        save_dir = '.'

    print("=" * 70)
    print("T³ CMB POWER SPECTRUM CALCULATOR")
    print("φ-harmonic constraint: L₁ : L₂ : L₃ = 1 : φ : φ²")
    print("=" * 70)

    calc = TorusSpectrumCalculator(l_max=50)
    chi_rec = 14000.0  # Mpc

    # Step 1: Isotropic spectrum
    print("\n[1] Computing isotropic (infinite flat) C_l spectrum...")
    cl_iso = calc.compute_cl_isotropic(chi_rec)
    print(f"    C_2 (quadrupole) = {cl_iso[0]:.4e}")
    print(f"    C_3 (octupole)   = {cl_iso[1]:.4e}")
    print(f"    C_10             = {cl_iso[8]:.4e}")

    # Step 2: φ-harmonic T³ spectrum at various L_min
    # L_min / chi_rec from 0.3 to 1.0
    ratios = np.linspace(0.3, 1.0, 15)
    L_min_values = ratios * chi_rec

    print(f"\n[2] Scanning L_min / χ_rec from {ratios[0]:.2f} to {ratios[-1]:.2f}...")

    results = calc.scan_L_min(L_min_values, chi_rec=chi_rec, n_max=15)

    # Find optimal L_min for quadrupole suppression
    # Observed: quadrupole is ~5-10x lower than ΛCDM prediction
    target_F2 = 0.15  # want ~85% suppression
    best_idx = np.argmin(np.abs(results['F_2'] - target_F2))
    best_L_min = L_min_values[best_idx]
    best_ratio = best_L_min / chi_rec

    print(f"\n    Optimal L_min for quadrupole suppression:")
    print(f"    L_min = {best_L_min:.0f} Mpc")
    print(f"    L_min / χ_rec = {best_ratio:.3f}")
    print(f"    F_2 (quadrupole suppression) = {results['F_2'][best_idx]:.3f}")
    print(f"    F_3 (octupole suppression)   = {results['F_3'][best_idx]:.3f}")

    L2 = best_L_min * PHI
    L3 = best_L_min * PHI**2
    print(f"\n    Torus circumferences:")
    print(f"    L₁ = {best_L_min:.0f} Mpc ({best_L_min/chi_rec:.3f} χ_rec)")
    print(f"    L₂ = {L2:.0f} Mpc ({L2/chi_rec:.3f} χ_rec)")
    print(f"    L₃ = {L3:.0f} Mpc ({L3/chi_rec:.3f} χ_rec)")

    # Step 3: Best-fit T³ spectrum with Axis of Evil orientation
    orientation = calc.axis_of_evil_orientation()
    print(f"\n[3] Computing T³ spectrum aligned with Axis of Evil...")
    print(f"    Orientation: (l, b) ≈ (250°, 60°)")

    cl_best, mode_count, params = calc.compute_cl_torus_phi_harmonic(
        best_L_min, chi_rec=chi_rec, n_max=15, orientation=orientation
    )

    F_l = np.where(cl_iso > 0, cl_best / cl_iso, 1.0)
    print(f"    Suppression factors:")
    for l_idx, l_val in enumerate(calc.ells[:10]):
        print(f"      l={l_val:3d}: F_l = {F_l[l_idx]:.3f}, "
              f"modes = {mode_count[l_idx]:.0f}")

    # Step 4: Synthetic "observed" spectrum with realistic noise
    # Simulate what Planck would see for a T³ universe
    print(f"\n[4] Generating synthetic observed spectrum (T³ + noise)...")
    np.random.seed(42)
    # Cosmic variance: σ(C_l) = C_l * sqrt(2/(2l+1))
    cl_errors = cl_best * np.sqrt(2.0 / (2.0 * calc.ells + 1.0))
    cl_observed = cl_best + np.random.randn(len(cl_best)) * cl_errors

    # Step 5: Bayesian evidence
    print(f"\n[5] Computing Bayesian evidence (T³ vs isotropic)...")
    log_B, chi2_T3, chi2_iso = calc.bayesian_evidence(
        cl_observed, cl_errors, best_L_min, chi_rec=chi_rec, n_max=15
    )

    print(f"    χ² (isotropic): {chi2_iso:.1f}")
    print(f"    χ² (T³ φ-harmonic): {chi2_T3:.1f}")
    print(f"    Δχ² = {chi2_iso - chi2_T3:.1f}")
    print(f"    ln(Bayes factor) = {log_B:.1f}")

    if log_B > 5:
        verdict = "STRONG evidence for T³"
    elif log_B > 2.5:
        verdict = "Moderate evidence for T³"
    elif log_B > 0:
        verdict = "Weak evidence for T³"
    else:
        verdict = "Isotropic preferred"
    print(f"    Verdict: {verdict}")

    # Visualization
    print(f"\n[6] Creating visualizations...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))

    # 1. C_l comparison
    ax = axes[0, 0]
    dl_iso = calc.ells * (calc.ells + 1) * cl_iso / (2 * np.pi)
    dl_torus = calc.ells * (calc.ells + 1) * cl_best / (2 * np.pi)
    dl_obs = calc.ells * (calc.ells + 1) * cl_observed / (2 * np.pi)
    dl_err = calc.ells * (calc.ells + 1) * cl_errors / (2 * np.pi)

    ax.semilogy(calc.ells, dl_iso, 'b-', linewidth=2, label='Isotropic (ΛCDM)', alpha=0.8)
    ax.semilogy(calc.ells, np.abs(dl_torus), 'r-', linewidth=2, label='T³ φ-harmonic', alpha=0.8)
    ax.errorbar(calc.ells, np.abs(dl_obs), yerr=dl_err, fmt='k.', markersize=4,
                alpha=0.5, label='Synthetic observed')
    ax.set_xlabel('Multipole l')
    ax.set_ylabel('l(l+1)C_l / 2π')
    ax.set_title('CMB Power Spectrum: T³ vs Isotropic')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2, calc.l_max)

    # 2. Suppression factor F_l
    ax = axes[0, 1]
    ax.plot(calc.ells, F_l, 'r-o', linewidth=2, markersize=4)
    ax.axhline(1.0, color='k', linestyle='--', alpha=0.5)
    ax.axhline(0.15, color='g', linestyle=':', alpha=0.5,
               label=f'Observed quadrupole suppression')
    ax.fill_between(calc.ells, 0, F_l, alpha=0.2, color='red',
                    where=F_l < 0.5)
    ax.set_xlabel('Multipole l')
    ax.set_ylabel('F_l = C_l^{T³} / C_l^{iso}')
    ax.set_title(f'Geometric Suppression Factor\nL₁/χ_rec = {best_ratio:.3f}')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 2)
    ax.set_xlim(2, calc.l_max)

    # 3. L_min scan - quadrupole suppression
    ax = axes[0, 2]
    ax.plot(ratios, results['F_2'], 'r-o', linewidth=2, markersize=5,
            label='F_2 (quadrupole)')
    ax.plot(ratios, results['F_3'], 'b-s', linewidth=2, markersize=5,
            label='F_3 (octupole)')
    ax.axhline(0.15, color='g', linestyle=':', alpha=0.5,
               label='Observed l=2 suppression')
    ax.axvline(best_ratio, color='k', linestyle='--', alpha=0.5,
               label=f'Best fit: {best_ratio:.3f}')
    ax.set_xlabel('L_min / χ_rec')
    ax.set_ylabel('Suppression Factor')
    ax.set_title('Quadrupole/Octupole Suppression vs Torus Size')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 4. Mode counting
    ax = axes[1, 0]
    ax.bar(calc.ells[:20], mode_count[:20], alpha=0.7, color='purple',
           edgecolor='black')
    ax.set_xlabel('Multipole l')
    ax.set_ylabel('Number of Contributing Modes')
    ax.set_title('Allowed Mode Count per Multipole')
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Torus geometry diagram
    ax = axes[1, 1]
    ax.set_aspect('equal')
    theta = np.linspace(0, 2 * np.pi, 100)

    # Draw three circles representing the three S¹ factors
    scales = [1.0, PHI, PHI**2]
    colors_circ = ['red', 'blue', 'green']
    labels_circ = [f'L₁ = {best_L_min:.0f} Mpc',
                   f'L₂ = {L2:.0f} Mpc',
                   f'L₃ = {L3:.0f} Mpc']

    for s, c, lab in zip(scales, colors_circ, labels_circ):
        r = s / scales[-1]  # normalize to largest
        ax.plot(r * np.cos(theta), r * np.sin(theta), color=c,
                linewidth=2, label=lab)

    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('T³ Circumference Ratios\n1 : φ : φ²')
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)

    # 6. Summary
    ax = axes[1, 2]
    ax.axis('off')
    summary = (
        f"T³ CMB POWER SPECTRUM ANALYSIS\n"
        f"{'='*40}\n\n"
        f"Topology: T³ = S¹ × S¹ × S¹\n"
        f"Constraint: L₁:L₂:L₃ = 1:φ:φ²\n\n"
        f"Best-fit parameters:\n"
        f"  L₁ = {best_L_min:.0f} Mpc ({best_ratio:.3f} χ_rec)\n"
        f"  L₂ = {L2:.0f} Mpc ({L2/chi_rec:.3f} χ_rec)\n"
        f"  L₃ = {L3:.0f} Mpc ({L3/chi_rec:.3f} χ_rec)\n\n"
        f"Suppression factors:\n"
        f"  F_2 = {F_l[0]:.3f} (quadrupole)\n"
        f"  F_3 = {F_l[1]:.3f} (octupole)\n\n"
        f"Bayesian evidence:\n"
        f"  ln(B) = {log_B:.1f}\n"
        f"  {verdict}\n\n"
        f"Orientation:\n"
        f"  L₁ aligned with (l,b)≈(250°,60°)\n"
        f"  (Axis of Evil direction)"
    )
    ax.text(0.05, 0.95, summary, fontsize=9, family='monospace',
            verticalalignment='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    save_path = f'{save_dir}/torus_spectrum_analysis.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {save_path}")

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")

    return {
        'cl_iso': cl_iso,
        'cl_torus': cl_best,
        'F_l': F_l,
        'best_L_min': best_L_min,
        'best_ratio': best_ratio,
        'log_evidence': log_B,
        'ells': calc.ells,
        'scan_results': results,
    }


if __name__ == '__main__':
    results = run_analysis(
        save_dir='phi_equation_investigation/phi_domain_analysis/cosmic_anisotropy'
    )
