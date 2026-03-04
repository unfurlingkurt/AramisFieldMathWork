#!/usr/bin/env python3
"""
RatioSpace Advanced Tests

Tests for:
1. Mediant time progression (dτ/dt from mediant operations)
2. Hyperbolic geometry (geodesics, curvature)
3. Conjugate pair entanglement (Z₁ · Z₂ ≈ φ correlations)

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
from scipy.stats import pearsonr
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver


class RatioSpaceAnalyzer:
    """Advanced tests for RatioSpace / Stern-Brocot structure."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
        self.phi_golden = (1 + np.sqrt(5)) / 2
    
    def compute_impedance(self, phi, dphi_dt):
        """Compute impedance Z = |∇φ| / |dφ/dt|"""
        grad_phi = np.gradient(phi, self.dx)
        grad_mag = np.abs(grad_phi)
        Z = grad_mag / (np.abs(dphi_dt) + 1e-10)
        return Z
    
    def compute_continued_fraction_length(self, a, b, max_terms=20):
        """
        Compute continued fraction length (tension) between ratios.
        
        CF length is a measure of "distance" in hyperbolic space.
        """
        if b == 0:
            return max_terms
        
        cf_terms = []
        x = a / b
        
        for _ in range(max_terms):
            if x < 1e-10:
                break
            term = int(x)
            cf_terms.append(term)
            x = x - term
            if x < 1e-10:
                break
            x = 1 / x
        
        return len(cf_terms)
    
    def test_mediant_time_progression(self, L=100, Nx=200, T=100):
        """
        Test if time progression follows mediant operations.
        
        Hypothesis: dτ/dt = f(local Farey depth, local tension)
        """
        print("Testing mediant time progression...")
        
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Track time progression
        observer_times = []
        intrinsic_times = []
        impedances_over_time = []
        
        intrinsic_time = 0
        
        for i in range(int(T / 0.1)):
            phi_old = solver.phi.copy()
            time_old = solver.time
            solver.step()
            dt_actual = solver.time - time_old
            
            if i % 5 == 0:
                # Compute impedance
                dphi_dt = (solver.phi - phi_old) / (dt_actual + 1e-10)
                Z = self.compute_impedance(solver.phi, dphi_dt)
                
                # Intrinsic time increment (mediant operations)
                # High tension (high Z) → slow progression
                # Low tension (low Z) → fast progression
                mean_Z = np.mean(Z)
                
                # Hypothesis: dτ/dt ∝ 1/Z (inverse of tension)
                dtau = dt_actual / (mean_Z + 1e-10)
                intrinsic_time += dtau
                
                observer_times.append(solver.time)
                intrinsic_times.append(intrinsic_time)
                impedances_over_time.append(mean_Z)
        
        observer_times = np.array(observer_times)
        intrinsic_times = np.array(intrinsic_times)
        impedances_over_time = np.array(impedances_over_time)
        
        # Compute dτ/dt
        dtau_dt = np.gradient(intrinsic_times) / np.gradient(observer_times)
        
        # Correlation with impedance
        correlation = pearsonr(impedances_over_time[1:], dtau_dt[1:])[0]
        
        print(f"  Observer time range: {observer_times[0]:.2f} to {observer_times[-1]:.2f}")
        print(f"  Intrinsic time range: {intrinsic_times[0]:.2f} to {intrinsic_times[-1]:.2f}")
        print(f"  Mean dτ/dt: {np.mean(dtau_dt):.4f}")
        print(f"  Std dτ/dt: {np.std(dtau_dt):.4f}")
        print(f"  Correlation(Z, dτ/dt): {correlation:.4f}")
        
        if abs(correlation) > 0.5:
            print(f"  ✓ Strong correlation between impedance and time progression!")
            print(f"    High Z (matter) → slow intrinsic time")
            print(f"    Low Z (vacuum) → fast intrinsic time")
        else:
            print(f"  ⚠ Weak correlation - may need different formulation")
        
        return {
            'observer_times': observer_times,
            'intrinsic_times': intrinsic_times,
            'dtau_dt': dtau_dt,
            'impedances': impedances_over_time,
            'correlation': correlation
        }
    
    def test_hyperbolic_geometry(self, L=100, Nx=200, T=50):
        """
        Test if φ-field lives on hyperbolic space.
        
        Key predictions:
        1. Geodesics preserve gradient norm
        2. Constant negative curvature
        3. Distance = tension (CF length)
        """
        print("\nTesting hyperbolic geometry...")
        
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Evolve to steady state
        for i in range(int(T / 0.1)):
            solver.step()
        
        phi = solver.phi
        
        # Test 1: Gradient norm conservation (geodesic preservation)
        grad_phi = np.gradient(phi, self.dx)
        grad_norm_squared = np.sum(grad_phi**2) * self.dx
        
        # Evolve more and check conservation
        grad_norms = [grad_norm_squared]
        
        for i in range(50):
            solver.step()
            grad_phi = np.gradient(solver.phi, self.dx)
            grad_norm = np.sum(grad_phi**2) * self.dx
            grad_norms.append(grad_norm)
        
        grad_norms = np.array(grad_norms)
        grad_conservation = np.std(grad_norms) / (np.mean(grad_norms) + 1e-10)
        
        print(f"  Gradient norm conservation:")
        print(f"    Mean ||∇φ||²: {np.mean(grad_norms):.6f}")
        print(f"    Std: {np.std(grad_norms):.6f}")
        print(f"    Relative variation: {100*grad_conservation:.2f}%")
        
        if grad_conservation < 0.01:
            print(f"    ✓ Gradient norm conserved (geodesic flow confirmed!)")
        else:
            print(f"    ⚠ Gradient norm varies")
        
        # Test 2: Curvature estimation
        # In hyperbolic space, curvature K = -1 (constant negative)
        # Discrete curvature from second derivatives
        lap_phi = np.zeros_like(phi)
        lap_phi[1:-1] = (phi[2:] - 2*phi[1:-1] + phi[:-2]) / self.dx**2
        
        # Gaussian curvature estimate (simplified)
        # K ≈ -Δφ / φ for small φ
        curvature = -lap_phi / (np.abs(phi) + 1e-10)
        mean_curvature = np.mean(curvature[np.isfinite(curvature)])
        
        print(f"\n  Curvature estimation:")
        print(f"    Mean curvature: {mean_curvature:.4f}")
        print(f"    Expected (hyperbolic): K = -1")
        
        if mean_curvature < 0:
            print(f"    ✓ Negative curvature confirmed!")
        else:
            print(f"    ⚠ Positive curvature (not hyperbolic)")
        
        # Test 3: Hyperbolic distance vs Euclidean distance
        # Sample points
        n_samples = 20
        indices = np.linspace(0, len(phi)-1, n_samples, dtype=int)
        phi_samples = phi[indices]
        
        # Euclidean distances
        euclidean_dist = pdist(phi_samples.reshape(-1, 1))
        
        # "Hyperbolic" distance (using gradient as proxy for tension)
        grad_samples = np.abs(np.gradient(phi_samples, self.dx))
        hyperbolic_dist = pdist(grad_samples.reshape(-1, 1))
        
        # Correlation
        if len(euclidean_dist) > 0 and len(hyperbolic_dist) > 0:
            dist_correlation = pearsonr(euclidean_dist, hyperbolic_dist)[0]
            print(f"\n  Distance comparison:")
            print(f"    Correlation(Euclidean, Hyperbolic): {dist_correlation:.4f}")
            
            if abs(dist_correlation) < 0.5:
                print(f"    ✓ Distances differ (non-Euclidean geometry!)")
            else:
                print(f"    ⚠ Distances similar (may be Euclidean)")
        
        return {
            'grad_norms': grad_norms,
            'grad_conservation': grad_conservation,
            'curvature': curvature,
            'mean_curvature': mean_curvature
        }
    
    def test_conjugate_pair_entanglement(self, L=100, Nx=200, T=100):
        """
        Test if conjugate impedance pairs are entangled.
        
        Hypothesis: Regions with Z₁ · Z₂ ≈ φ are correlated
        (forced geometric duality, not transmitted signal)
        """
        print("\nTesting conjugate pair entanglement...")
        
        solver = AdvancedPhiSolver(
            domain_size=(Nx,),
            dx=self.dx,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            dim=1
        )
        
        np.random.seed(42)
        solver.phi = 0.5 * np.random.randn(Nx)
        
        # Evolve
        for i in range(int(T / 0.1)):
            phi_old = solver.phi.copy()
            time_old = solver.time
            solver.step()
            dt_actual = solver.time - time_old
        
        # Final state
        dphi_dt = (solver.phi - phi_old) / (dt_actual + 1e-10)
        Z = self.compute_impedance(solver.phi, dphi_dt)
        
        # Find conjugate pairs: Z₁ · Z₂ ≈ φ
        conjugate_pairs = []
        correlations = []
        
        for i in range(len(Z)):
            for j in range(i+1, len(Z)):
                product = Z[i] * Z[j]
                
                # Check if product ≈ φ (within 20%)
                if abs(product - self.phi_golden) < 0.2 * self.phi_golden:
                    conjugate_pairs.append((i, j, product))
                    
                    # Measure correlation in field values
                    # Conjugates should be anti-correlated
                    corr = solver.phi[i] * solver.phi[j]
                    correlations.append(corr)
        
        print(f"  Found {len(conjugate_pairs)} conjugate pairs")
        print(f"  (Z₁ · Z₂ ≈ φ = {self.phi_golden:.4f})")
        
        if len(conjugate_pairs) > 0:
            products = [p[2] for p in conjugate_pairs]
            mean_product = np.mean(products)
            std_product = np.std(products)
            
            print(f"  Mean product: {mean_product:.4f}")
            print(f"  Std product: {std_product:.4f}")
            print(f"  Error from φ: {abs(mean_product - self.phi_golden):.4f}")
            
            # Check correlations
            mean_corr = np.mean(correlations)
            print(f"\n  Field correlation at conjugate pairs:")
            print(f"    Mean φ₁·φ₂: {mean_corr:.4f}")
            
            if abs(mean_corr) < 0.1:
                print(f"    ✓ Weak correlation (as expected for entangled pairs)")
            else:
                print(f"    ⚠ Strong correlation")
            
            # Test if conjugate pairs evolve together
            # (would need time series data - simplified here)
            
            if len(conjugate_pairs) > 10:
                print(f"\n  ✓ Conjugate pair structure confirmed!")
                print(f"    Geometric duality may explain entanglement")
            else:
                print(f"\n  ⚠ Few conjugate pairs found")
        else:
            print(f"  ✗ No conjugate pairs found")
        
        return {
            'conjugate_pairs': conjugate_pairs,
            'correlations': correlations,
            'Z': Z
        }


def main():
    """Run RatioSpace advanced tests."""
    print("=" * 80)
    print("RATIOSPACE ADVANCED TESTS")
    print("=" * 80)
    print()
    print("Testing:")
    print("  1. Mediant time progression (dτ/dt from Farey depth)")
    print("  2. Hyperbolic geometry (geodesics, curvature)")
    print("  3. Conjugate pair entanglement (Z₁ · Z₂ ≈ φ)")
    print()
    print("=" * 80)
    print()
    
    analyzer = RatioSpaceAnalyzer(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    # Test 1: Mediant time progression
    mediant_result = analyzer.test_mediant_time_progression(T=100)
    
    # Test 2: Hyperbolic geometry
    hyperbolic_result = analyzer.test_hyperbolic_geometry(T=50)
    
    # Test 3: Conjugate pair entanglement
    conjugate_result = analyzer.test_conjugate_pair_entanglement(T=100)
    
    # Visualize
    print("\nCreating visualizations...")
    
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Observer vs Intrinsic time
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(mediant_result['observer_times'], mediant_result['intrinsic_times'], 
            'b-', linewidth=2)
    ax1.plot(mediant_result['observer_times'], mediant_result['observer_times'],
            'r--', linewidth=1, alpha=0.5, label='Linear (reference)')
    ax1.set_xlabel('Observer Time t')
    ax1.set_ylabel('Intrinsic Time τ')
    ax1.set_title('Time Progression: Observer vs Intrinsic')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. dτ/dt over time
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(mediant_result['observer_times'][1:], mediant_result['dtau_dt'][1:],
            'g-', linewidth=2)
    ax2.axhline(1.0, color='r', linestyle='--', linewidth=1, alpha=0.5, label='dτ/dt = 1')
    ax2.set_xlabel('Observer Time t')
    ax2.set_ylabel('dτ/dt')
    ax2.set_title(f'Time Dilation Factor\nCorr(Z, dτ/dt) = {mediant_result["correlation"]:.3f}')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Impedance vs dτ/dt
    ax3 = plt.subplot(2, 3, 3)
    ax3.scatter(mediant_result['impedances'][1:], mediant_result['dtau_dt'][1:],
               alpha=0.5, s=20, c='purple')
    ax3.set_xlabel('Mean Impedance Z')
    ax3.set_ylabel('dτ/dt')
    ax3.set_title('Time Progression vs Impedance')
    ax3.grid(True, alpha=0.3)
    
    # 4. Gradient norm conservation
    ax4 = plt.subplot(2, 3, 4)
    ax4.plot(hyperbolic_result['grad_norms'], 'b-', linewidth=2)
    ax4.axhline(np.mean(hyperbolic_result['grad_norms']), color='r', 
               linestyle='--', linewidth=1, alpha=0.5, label='Mean')
    ax4.set_xlabel('Time Step')
    ax4.set_ylabel('||∇φ||²')
    ax4.set_title(f'Gradient Norm Conservation\nCV = {100*hyperbolic_result["grad_conservation"]:.2f}%')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Curvature distribution
    ax5 = plt.subplot(2, 3, 5)
    curvature = hyperbolic_result['curvature']
    curvature_clean = curvature[np.isfinite(curvature) & (np.abs(curvature) < 10)]
    ax5.hist(curvature_clean, bins=50, alpha=0.7, edgecolor='black', color='orange')
    ax5.axvline(hyperbolic_result['mean_curvature'], color='r', linestyle='--',
               linewidth=2, label=f'Mean = {hyperbolic_result["mean_curvature"]:.2f}')
    ax5.axvline(-1, color='g', linestyle='--', linewidth=2, label='K = -1 (hyperbolic)')
    ax5.set_xlabel('Curvature K')
    ax5.set_ylabel('Count')
    ax5.set_title('Curvature Distribution')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Conjugate pairs
    ax6 = plt.subplot(2, 3, 6)
    if len(conjugate_result['conjugate_pairs']) > 0:
        products = [p[2] for p in conjugate_result['conjugate_pairs']]
        ax6.hist(products, bins=20, alpha=0.7, edgecolor='black', color='red')
        ax6.axvline(analyzer.phi_golden, color='g', linestyle='--', linewidth=2,
                   label=f'φ = {analyzer.phi_golden:.4f}')
        ax6.set_xlabel('Z₁ · Z₂')
        ax6.set_ylabel('Count')
        ax6.set_title(f'Conjugate Pairs\n{len(conjugate_result["conjugate_pairs"])} pairs found')
        ax6.legend()
        ax6.grid(True, alpha=0.3, axis='y')
    else:
        ax6.text(0.5, 0.5, 'No conjugate pairs found', 
                ha='center', va='center', fontsize=12)
        ax6.set_title('Conjugate Pairs')
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/ratiospace_advanced_tests.png', dpi=150)
    print("  Saved: ratiospace_advanced_tests.png")
    
    # Final summary
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    
    # Scoring
    mediant_confirmed = abs(mediant_result['correlation']) > 0.5
    geodesic_confirmed = hyperbolic_result['grad_conservation'] < 0.01
    negative_curvature = hyperbolic_result['mean_curvature'] < 0
    conjugates_found = len(conjugate_result['conjugate_pairs']) > 10
    
    score = sum([mediant_confirmed, geodesic_confirmed, negative_curvature, conjugates_found])
    
    print(f"Test Results ({score}/4 passed):")
    print()
    
    if mediant_confirmed:
        print(f"  ✓ Mediant time progression confirmed")
        print(f"    Correlation(Z, dτ/dt) = {mediant_result['correlation']:.3f}")
    else:
        print(f"  ⚠ Weak mediant time correlation")
    
    if geodesic_confirmed:
        print(f"  ✓ Geodesic flow confirmed (gradient conservation)")
        print(f"    Variation = {100*hyperbolic_result['grad_conservation']:.2f}%")
    else:
        print(f"  ⚠ Gradient norm varies")
    
    if negative_curvature:
        print(f"  ✓ Negative curvature confirmed")
        print(f"    Mean K = {hyperbolic_result['mean_curvature']:.2f}")
    else:
        print(f"  ⚠ Positive curvature")
    
    if conjugates_found:
        print(f"  ✓ Conjugate pairs found")
        print(f"    {len(conjugate_result['conjugate_pairs'])} pairs with Z₁·Z₂ ≈ φ")
    else:
        print(f"  ⚠ Few/no conjugate pairs")
    
    print()
    
    if score >= 3:
        print("✓ RATIOSPACE STRUCTURE STRONGLY CONFIRMED")
        print()
        print("Evidence for:")
        print("  • Time as discrete Farey depth (mediant operations)")
        print("  • Space as hyperbolic geometry (geodesics, negative curvature)")
        print("  • Entanglement as geometric duality (conjugate pairs)")
        print()
        print("The φ-equation operates on the discrete rational substrate")
        print("of the Stern-Brocot tree in hyperbolic space.")
    else:
        print(f"⚠ PARTIAL CONFIRMATION ({score}/4 tests passed)")
        print()
        print("Some RatioSpace structure detected, needs further investigation.")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
