#!/usr/bin/env python3
"""
Impedance Map Generator for CMB

Applies the φ-equation impedance definition to the CMB temperature field:

    Z(θ,φ) = |∇T(θ,φ)| / |dT/dt(θ,φ)|

On a sphere, the gradient is computed from spherical harmonic coefficients.
The temporal derivative is estimated from multi-frequency spectral
distortion as a proxy for temporal evolution.

The φ-framework predicts:
- Three regimes: vacuum (33%), light (34%), matter (33%)
- The "matter" (high-Z) regime concentrated along the Axis of Evil
- The impedance distribution has toroidal (not spherical) symmetry

This tool works with both:
- Real Planck HEALPix maps (when available)
- Synthetic CMB realizations (for testing predictions)
"""

import numpy as np
import healpy as hp
from scipy.special import sph_harm
import warnings
warnings.filterwarnings('ignore')

PHI = (1 + np.sqrt(5)) / 2


class CMBImpedanceMapper:
    """
    Compute and analyze impedance maps from CMB temperature fields.

    Impedance Z = |∇T| / |∂T/∂t|

    On the CMB, we use multi-frequency as a proxy for temporal:
    spectral distortions measure how the photon field has evolved.
    For synthetic maps, we use the φ-equation dynamics directly.
    """

    def __init__(self, nside=64):
        """
        Parameters
        ----------
        nside : int
            HEALPix resolution parameter. nside=64 gives 49152 pixels.
        """
        self.nside = nside
        self.npix = hp.nside2npix(nside)
        self.lmax = 3 * nside - 1

    def generate_synthetic_cmb(self, cl_spectrum=None, seed=42):
        """
        Generate a synthetic CMB temperature map.

        If cl_spectrum is provided, uses those C_l values.
        Otherwise generates a standard nearly-scale-invariant spectrum.

        Parameters
        ----------
        cl_spectrum : ndarray, optional
            C_l values starting from l=0.
        seed : int
            Random seed for reproducibility.

        Returns
        -------
        cmb_map : ndarray
            HEALPix map of CMB temperature fluctuations.
        """
        np.random.seed(seed)

        if cl_spectrum is None:
            # Generate standard nearly-scale-invariant spectrum
            ells = np.arange(self.lmax + 1)
            cl = np.zeros(self.lmax + 1)
            # Sachs-Wolfe plateau for l >= 2
            cl[2:] = 1e-10 / (ells[2:] * (ells[2:] + 1))
            cl_spectrum = cl

        cmb_map = hp.synfast(cl_spectrum, self.nside, lmax=self.lmax,
                              new=True, verbose=False)
        return cmb_map

    def generate_torus_modulated_cmb(self, L1_ratio=0.5, seed=42):
        """
        Generate a CMB map with T³ toroidal modulation.

        Suppresses large-scale modes along the shortest torus direction
        and introduces the characteristic anisotropy pattern.

        Parameters
        ----------
        L1_ratio : float
            L₁ / χ_rec — ratio of shortest circumference to last
            scattering distance. Controls strength of topology signal.
        seed : int
            Random seed.

        Returns
        -------
        cmb_map : ndarray
            Toroidally-modulated CMB map.
        modulation : ndarray
            The pure modulation pattern.
        """
        np.random.seed(seed)

        # Start with isotropic CMB
        ells = np.arange(self.lmax + 1)
        cl_iso = np.zeros(self.lmax + 1)
        cl_iso[2:] = 1e-10 / (ells[2:] * (ells[2:] + 1))

        cmb_iso = hp.synfast(cl_iso, self.nside, lmax=self.lmax,
                              new=True, verbose=False)

        # Create toroidal modulation
        # The modulation is a dipolar+quadrupolar pattern aligned with
        # the Axis of Evil direction
        theta, phi_coord = hp.pix2ang(self.nside, np.arange(self.npix))

        # Axis of Evil in galactic coords: (l,b) ≈ (250°, 60°)
        l_ae = np.radians(250.0)
        b_ae = np.radians(60.0)
        theta_ae = np.pi / 2 - b_ae
        phi_ae = l_ae

        # Angular distance from Axis of Evil
        cos_angle = (np.sin(theta_ae) * np.sin(theta) *
                     np.cos(phi_coord - phi_ae) +
                     np.cos(theta_ae) * np.cos(theta))

        # Toroidal modulation: suppresses power along AoE direction
        # The modulation factor encodes the topology
        suppression = 1.0 - (1.0 - L1_ratio) * (1 + cos_angle) / 2.0

        # Quadrupolar component
        quad_mod = 1.0 - 0.3 * (1.0 - L1_ratio) * (3 * cos_angle**2 - 1) / 2.0

        modulation = suppression * quad_mod

        # Apply modulation
        cmb_torus = cmb_iso * modulation

        return cmb_torus, modulation

    def compute_gradient_map(self, temperature_map):
        """
        Compute |∇T| on the sphere using spherical harmonic derivatives.

        Parameters
        ----------
        temperature_map : ndarray
            HEALPix temperature map.

        Returns
        -------
        grad_magnitude : ndarray
            |∇T| at each pixel.
        grad_theta : ndarray
            ∂T/∂θ component.
        grad_phi : ndarray
            (1/sinθ) ∂T/∂φ component.
        """
        # Decompose into spherical harmonics
        alm = hp.map2alm(temperature_map, lmax=self.lmax)

        # Compute derivatives using healpy
        # alm2map_der1 returns (map, dtheta, dphi)
        _, dtheta, dphi = hp.alm2map_der1(alm, self.nside, lmax=self.lmax)

        grad_magnitude = np.sqrt(dtheta**2 + dphi**2)

        return grad_magnitude, dtheta, dphi

    def estimate_temporal_derivative(self, temperature_map, method='gradient_flow'):
        """
        Estimate |∂T/∂t| from the temperature map.

        Several methods:
        - 'gradient_flow': Use φ-equation dynamics as proxy
        - 'spectral': Use spectral distortion (requires multi-freq)
        - 'laplacian': Use Laplacian as diffusion rate proxy

        Parameters
        ----------
        temperature_map : ndarray
            HEALPix temperature map.
        method : str
            Method for estimating temporal derivative.

        Returns
        -------
        dt_magnitude : ndarray
            |∂T/∂t| at each pixel.
        """
        if method == 'laplacian':
            # ∂T/∂t ≈ α ΔT (diffusion approximation)
            alm = hp.map2alm(temperature_map, lmax=self.lmax)

            # Laplacian in spherical harmonics: ΔY_lm = -l(l+1)Y_lm
            ells_alm = hp.Alm.getlm(self.lmax)[0]
            alm_lap = alm * (-ells_alm * (ells_alm + 1))

            laplacian_map = hp.alm2map(alm_lap, self.nside,
                                        lmax=self.lmax, verbose=False)
            dt_magnitude = np.abs(laplacian_map)

        elif method == 'gradient_flow':
            # Use full φ-equation: ∂T/∂t = α(ΔT - γ|∇T|²) + β·tanh(T)·e^{-|∇T|}
            alpha, beta, gamma = 1.0, 1.0, 0.5

            alm = hp.map2alm(temperature_map, lmax=self.lmax)
            ells_alm = hp.Alm.getlm(self.lmax)[0]
            alm_lap = alm * (-ells_alm * (ells_alm + 1))
            laplacian = hp.alm2map(alm_lap, self.nside,
                                    lmax=self.lmax, verbose=False)

            grad_mag, _, _ = self.compute_gradient_map(temperature_map)

            diffusion = alpha * (laplacian - gamma * grad_mag**2)
            reaction = beta * np.tanh(temperature_map) * np.exp(-grad_mag)
            dt_map = diffusion + reaction

            dt_magnitude = np.abs(dt_map)

        elif method == 'spectral':
            # Spectral distortion proxy: y-type distortion
            # In absence of real multi-frequency data, approximate as
            # proportional to local power spectrum slope
            alm = hp.map2alm(temperature_map, lmax=self.lmax)
            cl = hp.alm2cl(alm, lmax=self.lmax)

            # Reconstruct with modified weights (spectral slope)
            ells_alm = hp.Alm.getlm(self.lmax)[0]
            weight = np.ones_like(ells_alm, dtype=float)
            weight[ells_alm > 0] = np.log(ells_alm[ells_alm > 0] + 1)
            alm_weighted = alm * weight

            weighted_map = hp.alm2map(alm_weighted, self.nside,
                                       lmax=self.lmax, verbose=False)
            dt_magnitude = np.abs(weighted_map - temperature_map)

        else:
            raise ValueError(f"Unknown method: {method}")

        # Regularize to avoid division by zero
        dt_magnitude = np.maximum(dt_magnitude, 1e-15)

        return dt_magnitude

    def compute_impedance_map(self, temperature_map, method='gradient_flow'):
        """
        Compute impedance map Z = |∇T| / |∂T/∂t|.

        Parameters
        ----------
        temperature_map : ndarray
            HEALPix temperature map.
        method : str
            Method for temporal derivative estimation.

        Returns
        -------
        impedance : ndarray
            Z at each pixel.
        grad_mag : ndarray
            |∇T| at each pixel.
        dt_mag : ndarray
            |∂T/∂t| at each pixel.
        """
        grad_mag, _, _ = self.compute_gradient_map(temperature_map)
        dt_mag = self.estimate_temporal_derivative(temperature_map, method)

        impedance = grad_mag / dt_mag

        return impedance, grad_mag, dt_mag

    def classify_regimes(self, impedance):
        """
        Classify pixels into vacuum/light/matter regimes.

        Uses percentile-based thresholds (33rd and 67th percentiles)
        following the φ-framework prediction of exact thirds.

        Parameters
        ----------
        impedance : ndarray
            Impedance map.

        Returns
        -------
        regimes : dict
            Masks and statistics for each regime.
        """
        p33 = np.percentile(impedance, 33.33)
        p67 = np.percentile(impedance, 66.67)

        vacuum_mask = impedance < p33
        light_mask = (impedance >= p33) & (impedance < p67)
        matter_mask = impedance >= p67

        n_total = len(impedance)

        return {
            'vacuum_mask': vacuum_mask,
            'light_mask': light_mask,
            'matter_mask': matter_mask,
            'thresholds': (p33, p67),
            'fractions': {
                'vacuum': np.sum(vacuum_mask) / n_total,
                'light': np.sum(light_mask) / n_total,
                'matter': np.sum(matter_mask) / n_total,
            },
            'mean_Z': {
                'vacuum': np.mean(impedance[vacuum_mask]),
                'light': np.mean(impedance[light_mask]),
                'matter': np.mean(impedance[matter_mask]),
            }
        }

    def test_axis_alignment(self, impedance, regime='matter'):
        """
        Test if the matter regime is concentrated along the Axis of Evil.

        Computes the dipole and quadrupole of the matter distribution
        and checks alignment with (l,b) ≈ (250°, 60°).

        Parameters
        ----------
        impedance : ndarray
            Impedance map.
        regime : str
            Which regime to test alignment for.

        Returns
        -------
        alignment : dict
            Dipole direction, quadrupole alignment, angular separation
            from Axis of Evil.
        """
        regimes = self.classify_regimes(impedance)
        mask = regimes[f'{regime}_mask']

        # Create regime density map
        regime_map = np.zeros(self.npix)
        regime_map[mask] = impedance[mask]

        # Compute dipole direction
        alm = hp.map2alm(regime_map, lmax=10)

        # Dipole: l=1 components
        a10 = alm[hp.Alm.getidx(10, 1, 0)]
        a11 = alm[hp.Alm.getidx(10, 1, 1)]

        # Dipole direction in spherical coords
        dipole_theta = np.arccos(np.real(a10) /
                                  np.sqrt(np.abs(a10)**2 + 2*np.abs(a11)**2 + 1e-20))
        dipole_phi = np.angle(a11)

        # Convert to galactic (l, b)
        dipole_l = np.degrees(dipole_phi)
        dipole_b = 90.0 - np.degrees(dipole_theta)

        # Axis of Evil direction
        aoe_l, aoe_b = 250.0, 60.0

        # Angular separation
        cos_sep = (np.sin(np.radians(dipole_b)) * np.sin(np.radians(aoe_b)) +
                   np.cos(np.radians(dipole_b)) * np.cos(np.radians(aoe_b)) *
                   np.cos(np.radians(dipole_l - aoe_l)))
        angular_sep = np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))

        # Quadrupole alignment
        a20 = alm[hp.Alm.getidx(10, 2, 0)]
        a21 = alm[hp.Alm.getidx(10, 2, 1)]
        a22 = alm[hp.Alm.getidx(10, 2, 2)]

        # Quadrupole power direction (simplified)
        quad_power = np.abs(a20)**2 + 2*np.abs(a21)**2 + 2*np.abs(a22)**2

        return {
            'dipole_direction': (dipole_l, dipole_b),
            'aoe_direction': (aoe_l, aoe_b),
            'angular_separation': angular_sep,
            'aligned': angular_sep < 30.0,
            'quadrupole_power': quad_power,
        }


def run_analysis(save_dir=None):
    """
    Run complete impedance map analysis.
    """
    import matplotlib.pyplot as plt

    if save_dir is None:
        save_dir = '.'

    print("=" * 70)
    print("CMB IMPEDANCE MAP GENERATOR")
    print("Z = |∇T| / |∂T/∂t|")
    print("=" * 70)

    mapper = CMBImpedanceMapper(nside=64)

    # Step 1: Generate synthetic CMB maps
    print("\n[1] Generating synthetic CMB maps...")

    # Isotropic CMB
    cmb_iso = mapper.generate_synthetic_cmb(seed=42)
    print(f"    Isotropic CMB: rms = {np.std(cmb_iso):.2e}")

    # Torus-modulated CMB
    cmb_torus, modulation = mapper.generate_torus_modulated_cmb(
        L1_ratio=0.5, seed=42
    )
    print(f"    Torus CMB:     rms = {np.std(cmb_torus):.2e}")

    # Step 2: Compute impedance maps
    print("\n[2] Computing impedance maps...")

    Z_iso, grad_iso, dt_iso = mapper.compute_impedance_map(cmb_iso)
    Z_torus, grad_torus, dt_torus = mapper.compute_impedance_map(cmb_torus)

    print(f"    Isotropic: Z_mean = {np.mean(Z_iso):.3f}, "
          f"Z_std = {np.std(Z_iso):.3f}")
    print(f"    Torus:     Z_mean = {np.mean(Z_torus):.3f}, "
          f"Z_std = {np.std(Z_torus):.3f}")

    # Step 3: Classify regimes
    print("\n[3] Classifying impedance regimes...")

    regimes_iso = mapper.classify_regimes(Z_iso)
    regimes_torus = mapper.classify_regimes(Z_torus)

    print(f"    Isotropic regimes:")
    for name, frac in regimes_iso['fractions'].items():
        print(f"      {name:8s}: {100*frac:.1f}%")

    print(f"    Torus regimes:")
    for name, frac in regimes_torus['fractions'].items():
        print(f"      {name:8s}: {100*frac:.1f}%")

    # Step 4: Test Axis of Evil alignment
    print("\n[4] Testing Axis of Evil alignment...")

    align_iso = mapper.test_axis_alignment(Z_iso, regime='matter')
    align_torus = mapper.test_axis_alignment(Z_torus, regime='matter')

    print(f"    Isotropic matter dipole: (l,b) = "
          f"({align_iso['dipole_direction'][0]:.0f}°, "
          f"{align_iso['dipole_direction'][1]:.0f}°)")
    print(f"      Angular sep from AoE: {align_iso['angular_separation']:.0f}°")
    print(f"      Aligned: {align_iso['aligned']}")

    print(f"    Torus matter dipole: (l,b) = "
          f"({align_torus['dipole_direction'][0]:.0f}°, "
          f"{align_torus['dipole_direction'][1]:.0f}°)")
    print(f"      Angular sep from AoE: {align_torus['angular_separation']:.0f}°")
    print(f"      Aligned: {align_torus['aligned']}")

    # Step 5: Directional impedance analysis
    print("\n[5] Directional impedance analysis...")

    theta, phi_coord = hp.pix2ang(mapper.nside, np.arange(mapper.npix))

    # Axis of Evil direction
    theta_ae = np.radians(90 - 60)
    phi_ae = np.radians(250)
    cos_angle_ae = (np.sin(theta_ae) * np.sin(theta) *
                     np.cos(phi_coord - phi_ae) +
                     np.cos(theta_ae) * np.cos(theta))

    # Split into "along AoE" and "perpendicular to AoE"
    along_ae = np.abs(cos_angle_ae) > 0.5
    perp_ae = ~along_ae

    Z_along = np.mean(Z_torus[along_ae])
    Z_perp = np.mean(Z_torus[perp_ae])
    anisotropy = (Z_along - Z_perp) / (Z_along + Z_perp)

    print(f"    Mean Z along Axis of Evil:  {Z_along:.4f}")
    print(f"    Mean Z perpendicular:       {Z_perp:.4f}")
    print(f"    Impedance anisotropy:       {anisotropy:.4f}")
    print(f"    {'Anisotropic' if abs(anisotropy) > 0.01 else 'Isotropic'} "
          f"impedance distribution")

    # Visualization
    print("\n[6] Creating visualizations...")

    fig = plt.figure(figsize=(18, 16))

    # Row 1: Temperature maps
    ax = fig.add_subplot(3, 3, 1)
    hp.mollview(cmb_iso, title='Isotropic CMB', hold=True,
                sub=(3, 3, 1), cmap='RdBu_r', min=-3e-5, max=3e-5)

    ax = fig.add_subplot(3, 3, 2)
    hp.mollview(cmb_torus, title='T³-modulated CMB', hold=True,
                sub=(3, 3, 2), cmap='RdBu_r', min=-3e-5, max=3e-5)

    ax = fig.add_subplot(3, 3, 3)
    hp.mollview(modulation, title='Toroidal Modulation', hold=True,
                sub=(3, 3, 3), cmap='viridis')

    # Row 2: Impedance maps
    Z_iso_clipped = np.clip(Z_iso, 0, np.percentile(Z_iso, 95))
    Z_torus_clipped = np.clip(Z_torus, 0, np.percentile(Z_torus, 95))

    ax = fig.add_subplot(3, 3, 4)
    hp.mollview(Z_iso_clipped, title='Impedance (Isotropic)', hold=True,
                sub=(3, 3, 4), cmap='hot')

    ax = fig.add_subplot(3, 3, 5)
    hp.mollview(Z_torus_clipped, title='Impedance (T³)', hold=True,
                sub=(3, 3, 5), cmap='hot')

    # Regime map for torus
    regime_map = np.zeros(mapper.npix)
    regime_map[regimes_torus['vacuum_mask']] = 0
    regime_map[regimes_torus['light_mask']] = 1
    regime_map[regimes_torus['matter_mask']] = 2

    ax = fig.add_subplot(3, 3, 6)
    hp.mollview(regime_map, title='Three Regimes (T³)\nBlue=Vacuum, Green=Light, Red=Matter',
                hold=True, sub=(3, 3, 6), cmap='RdYlBu_r', min=0, max=2)

    # Row 3: Analysis
    ax = fig.add_subplot(3, 3, 7)
    Z_flat_iso = Z_iso[np.isfinite(Z_iso) & (Z_iso > 0)]
    Z_flat_torus = Z_torus[np.isfinite(Z_torus) & (Z_torus > 0)]
    ax.hist(np.log10(Z_flat_iso), bins=50, alpha=0.5, color='blue',
            label='Isotropic', density=True)
    ax.hist(np.log10(Z_flat_torus), bins=50, alpha=0.5, color='red',
            label='T³', density=True)
    ax.set_xlabel('log₁₀(Z)')
    ax.set_ylabel('Density')
    ax.set_title('Impedance Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = fig.add_subplot(3, 3, 8)
    # Directional analysis: impedance vs angle from AoE
    angle_bins = np.linspace(0, 180, 20)
    angles = np.degrees(np.arccos(np.clip(cos_angle_ae, -1, 1)))
    Z_by_angle = []
    angle_centers = []
    for i in range(len(angle_bins) - 1):
        mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        if np.sum(mask) > 10:
            Z_by_angle.append(np.mean(Z_torus[mask]))
            angle_centers.append((angle_bins[i] + angle_bins[i+1]) / 2)

    ax.plot(angle_centers, Z_by_angle, 'ro-', linewidth=2, markersize=5)
    ax.set_xlabel('Angle from Axis of Evil (degrees)')
    ax.set_ylabel('Mean Impedance Z')
    ax.set_title('Impedance vs Direction (T³)\nShould show anisotropy')
    ax.grid(True, alpha=0.3)

    # Summary
    ax = fig.add_subplot(3, 3, 9)
    ax.axis('off')
    summary = (
        f"CMB IMPEDANCE MAP ANALYSIS\n"
        f"{'='*40}\n\n"
        f"Z = |∇T| / |∂T/∂t|\n\n"
        f"Three Regimes (T³ map):\n"
        f"  Vacuum: {100*regimes_torus['fractions']['vacuum']:.1f}%\n"
        f"  Light:  {100*regimes_torus['fractions']['light']:.1f}%\n"
        f"  Matter: {100*regimes_torus['fractions']['matter']:.1f}%\n\n"
        f"Axis of Evil Alignment:\n"
        f"  Matter dipole: ({align_torus['dipole_direction'][0]:.0f}°, "
        f"{align_torus['dipole_direction'][1]:.0f}°)\n"
        f"  AoE direction: (250°, 60°)\n"
        f"  Separation: {align_torus['angular_separation']:.0f}°\n"
        f"  Aligned: {align_torus['aligned']}\n\n"
        f"Impedance Anisotropy:\n"
        f"  Z_along / Z_perp = {Z_along/Z_perp:.3f}\n"
        f"  Anisotropy = {anisotropy:.4f}"
    )
    ax.text(0.05, 0.95, summary, fontsize=9, family='monospace',
            verticalalignment='top', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.tight_layout()
    save_path = f'{save_dir}/impedance_map_analysis.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    Saved: {save_path}")

    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")

    return {
        'Z_iso': Z_iso,
        'Z_torus': Z_torus,
        'regimes_iso': regimes_iso,
        'regimes_torus': regimes_torus,
        'alignment_iso': align_iso,
        'alignment_torus': align_torus,
        'anisotropy': anisotropy,
    }


if __name__ == '__main__':
    results = run_analysis(
        save_dir='phi_equation_investigation/phi_domain_analysis/cosmic_anisotropy'
    )
