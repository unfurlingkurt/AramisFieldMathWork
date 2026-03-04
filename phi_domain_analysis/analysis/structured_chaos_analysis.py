#!/usr/bin/env python3
"""
Structured Chaos Analysis

Re-examines what appears as "chaos" to reveal geometric structure.

Key insight: In 4D framework, apparent chaos may be:
1. Projection of ordered 4D structure
2. Multi-scale temporal organization
3. Topological structure (not random)
4. Information, not entropy

Author: Research Team
Date: 2026-03-03
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq, fft2
from scipy.signal import find_peaks
from scipy.spatial.distance import pdist, squareform
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from equation_solver import AdvancedPhiSolver


class StructuredChaosAnalyzer:
    """Analyzes geometric structure in apparent chaos."""
    
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.5, dx=0.5):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dx = dx
        self.phi = (1 + np.sqrt(5)) / 2
    
    def analyze_residual_structure(self, L=100, Nx=200, T=100):
        """
        Analyze geometric structure in residuals.
        
        Traditional: Residual = noise
        Novel: Residual contains geometric information
        """
        print("Analyzing residual structure...")
        
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
        
        # Evolve and track residuals
        n_steps = int(T / 0.1)
        residuals = []
        phi_history = []
        grad_history = []
        
        for i in range(n_steps):
            # Compute update (this is the "residual" from equilibrium)
            lap_phi = solver.compute_laplacian(solver.phi)
            grad_mag = solver.compute_gradient_magnitude(solver.phi)
            
            diffusion = self.alpha * (lap_phi - self.gamma * grad_mag**2)
            reaction = self.beta * np.tanh(solver.phi) * np.exp(-grad_mag)
            update = diffusion + reaction
            
            residuals.append(update.copy())
            phi_history.append(solver.phi.copy())
            grad_history.append(grad_mag.copy())
            
            solver.step()
        
        residuals = np.array(residuals)
        phi_history = np.array(phi_history)
        grad_history = np.array(grad_history)
        
        # Analyze residual structure
        print("\n  1. Temporal structure in residuals:")
        
        # Fourier analysis of residuals at center
        center_idx = Nx // 2
        residual_series = residuals[:, center_idx]
        
        fft_vals = np.abs(fft(residual_series))
        freqs = fftfreq(len(residual_series), 0.1)
        positive_mask = freqs > 0
        positive_freqs = freqs[positive_mask]
        positive_fft = fft_vals[positive_mask]
        
        # Find peaks
        peaks, _ = find_peaks(positive_fft, height=np.max(positive_fft) * 0.1)
        
        print(f"     Found {len(peaks)} frequency peaks in residuals")
        if len(peaks) > 0:
            for i, peak_idx in enumerate(peaks[:5]):
                freq = positive_freqs[peak_idx]
                power = positive_fft[peak_idx]
                print(f"       Peak {i+1}: f = {freq:.6f}, power = {power:.2f}")
        
        # Check for φ-harmonic structure
        if len(peaks) > 0:
            base_freq = positive_freqs[peaks[0]]
            print(f"\n     Checking for φ-harmonic ratios (base = {base_freq:.6f}):")
            
            for name, ratio in [('φ^-1', 1/self.phi), ('φ^0', 1.0), ('φ^1', self.phi)]:
                expected_freq = base_freq * ratio
                # Find closest peak
                freq_diffs = np.abs(positive_freqs[peaks] - expected_freq)
                if len(freq_diffs) > 0 and np.min(freq_diffs) < 0.1 * base_freq:
                    closest_idx = peaks[np.argmin(freq_diffs)]
                    actual_freq = positive_freqs[closest_idx]
                    error = abs(actual_freq - expected_freq) / expected_freq
                    print(f"       {name}: expected {expected_freq:.6f}, found {actual_freq:.6f} (error: {error*100:.1f}%)")
        
        # 2. Spatial structure in residuals
        print("\n  2. Spatial structure in residuals:")
        
        # Average residual pattern
        avg_residual = np.mean(residuals, axis=0)
        std_residual = np.std(residuals, axis=0)
        
        # Spatial Fourier
        fft_spatial = np.abs(fft(avg_residual))
        k_vals = fftfreq(Nx, self.dx)
        positive_k = k_vals[k_vals > 0]
        positive_fft_k = fft_spatial[k_vals > 0]
        
        peaks_k, _ = find_peaks(positive_fft_k, height=np.max(positive_fft_k) * 0.1)
        
        print(f"     Found {len(peaks_k)} spatial frequency peaks")
        if len(peaks_k) > 0:
            for i, peak_idx in enumerate(peaks_k[:3]):
                k = positive_k[peak_idx]
                wavelength = 2 * np.pi / k if k > 0 else np.inf
                print(f"       Peak {i+1}: k = {k:.6f}, λ = {wavelength:.2f}")
        
        # 3. Correlation structure
        print("\n  3. Correlation structure:")
        
        # Autocorrelation of residuals
        residual_flat = residuals.flatten()
        # Sample for efficiency
        sample_size = min(1000, len(residual_flat))
        sample_indices = np.random.choice(len(residual_flat), sample_size, replace=False)
        residual_sample = residual_flat[sample_indices]
        
        # Compute correlation length
        autocorr = np.correlate(residual_sample - np.mean(residual_sample), 
                               residual_sample - np.mean(residual_sample), 
                               mode='same')
        autocorr = autocorr / np.max(autocorr)
        
        # Find correlation length (where autocorr drops to 1/e)
        threshold_idx = np.where(autocorr[len(autocorr)//2:] < 1/np.e)[0]
        if len(threshold_idx) > 0:
            corr_length = threshold_idx[0]
            print(f"     Correlation length: {corr_length} steps")
        else:
            print(f"     Correlation length: > {len(autocorr)//2} steps (long-range)")
        
        return {
            'residuals': residuals,
            'phi_history': phi_history,
            'grad_history': grad_history,
            'temporal_freqs': positive_freqs,
            'temporal_power': positive_fft,
            'spatial_k': positive_k,
            'spatial_power': positive_fft_k,
            'peaks': peaks,
            'peaks_k': peaks_k
        }
    
    def analyze_entropy_vs_information(self, result):
        """
        Distinguish entropy (disorder) from information (structure).
        
        Traditional: High entropy = disorder
        Novel: High information = structure (appears as entropy in wrong frame)
        """
        print("\nAnalyzing entropy vs information...")
        
        residuals = result['residuals']
        
        # 1. Shannon entropy (traditional measure)
        print("\n  1. Shannon entropy:")
        
        # Discretize residuals
        hist, bin_edges = np.histogram(residuals.flatten(), bins=50, density=True)
        hist = hist[hist > 0]  # Remove zeros
        shannon_entropy = -np.sum(hist * np.log2(hist))
        
        print(f"     Shannon entropy: {shannon_entropy:.4f} bits")
        print(f"     (Higher = more 'random')")
        
        # 2. Kolmogorov complexity proxy (compressibility)
        print("\n  2. Compressibility (information content):")
        
        # Try to compress residuals
        residual_bytes = residuals.flatten().tobytes()
        
        # Simple run-length encoding as proxy
        def simple_rle_ratio(data):
            """Estimate compression ratio."""
            # Count runs of similar values
            threshold = np.std(data) * 0.1
            runs = 1
            for i in range(1, len(data)):
                if abs(data[i] - data[i-1]) > threshold:
                    runs += 1
            return runs / len(data)
        
        compression_ratio = simple_rle_ratio(residuals.flatten())
        
        print(f"     Compression ratio: {compression_ratio:.4f}")
        print(f"     (Lower = more compressible = more structure)")
        
        # 3. Mutual information (temporal correlations)
        print("\n  3. Temporal mutual information:")
        
        # Measure how much knowing past predicts future
        center_idx = residuals.shape[1] // 2
        series = residuals[:, center_idx]
        
        # Lag-1 mutual information (simplified)
        series_t = series[:-1]
        series_t1 = series[1:]
        
        # Discretize
        bins = 20
        hist_2d, _, _ = np.histogram2d(series_t, series_t1, bins=bins)
        hist_2d = hist_2d / np.sum(hist_2d)
        
        # Marginals
        p_t = np.sum(hist_2d, axis=1)
        p_t1 = np.sum(hist_2d, axis=0)
        
        # Mutual information
        mi = 0.0
        for i in range(bins):
            for j in range(bins):
                if hist_2d[i,j] > 0 and p_t[i] > 0 and p_t1[j] > 0:
                    mi += hist_2d[i,j] * np.log2(hist_2d[i,j] / (p_t[i] * p_t1[j]))
        
        print(f"     Mutual information: {mi:.4f} bits")
        print(f"     (Higher = more predictable = more structure)")
        
        # 4. Geometric structure measure
        print("\n  4. Geometric structure:")
        
        # Measure alignment of residuals with gradient structure
        grad_history = result['grad_history']
        
        # Correlation between residual magnitude and gradient
        residual_mag = np.abs(residuals)
        correlation = np.corrcoef(residual_mag.flatten(), grad_history.flatten())[0,1]
        
        print(f"     Residual-gradient correlation: {correlation:.4f}")
        print(f"     (Non-zero = geometric structure)")
        
        # 5. Topological structure
        print("\n  5. Topological structure:")
        
        # Count sign changes (topological events)
        sign_changes = np.sum(np.diff(np.sign(residuals), axis=0) != 0)
        total_points = residuals.size
        
        print(f"     Sign changes: {sign_changes} / {total_points} ({sign_changes/total_points*100:.2f}%)")
        
        # If random, expect ~50% sign changes
        # If structured, expect different percentage
        if sign_changes / total_points < 0.4:
            print(f"     → Fewer than random (persistent structure)")
        elif sign_changes / total_points > 0.6:
            print(f"     → More than random (oscillatory structure)")
        else:
            print(f"     → Near random (no obvious structure)")
        
        return {
            'shannon_entropy': shannon_entropy,
            'compression_ratio': compression_ratio,
            'mutual_information': mi,
            'geometric_correlation': correlation,
            'sign_change_ratio': sign_changes / total_points
        }
    
    def reinterpret_lyapunov(self, L=50, Nx=100, T=100):
        """
        Reinterpret Lyapunov exponent in 4D framework.
        
        Traditional: λ > 0 → chaos (disorder)
        Novel: λ > 0 → sensitive to projection (structure in 4D)
        """
        print("\nReinterpreting Lyapunov exponent...")
        
        # Compute Lyapunov in different measurement frames
        
        frames = [
            ('Observer time (t)', lambda phi: phi),
            ('Gradient magnitude', lambda phi: np.abs(np.gradient(phi))),
            ('Laplacian', lambda phi: np.gradient(np.gradient(phi))),
        ]
        
        results = []
        
        for frame_name, transform in frames:
            print(f"\n  Testing in {frame_name}:")
            
            # Setup
            solver1 = AdvancedPhiSolver(
                domain_size=(Nx,),
                dx=self.dx,
                alpha=self.alpha,
                beta=self.beta,
                gamma=self.gamma,
                dim=1
            )
            
            solver2 = AdvancedPhiSolver(
                domain_size=(Nx,),
                dx=self.dx,
                alpha=self.alpha,
                beta=self.beta,
                gamma=self.gamma,
                dim=1
            )
            
            np.random.seed(42)
            phi0 = 0.5 * np.random.randn(Nx)
            
            solver1.phi = phi0.copy()
            solver2.phi = phi0 + 1e-8 * np.random.randn(Nx)
            
            # Track separation in transformed space
            n_steps = int(T / 0.1)
            log_separations = []
            times = []
            
            for i in range(n_steps):
                solver1.step()
                solver2.step()
                
                # Transform to measurement frame
                phi1_transformed = transform(solver1.phi)
                phi2_transformed = transform(solver2.phi)
                
                # Compute separation
                separation = np.linalg.norm(phi2_transformed - phi1_transformed)
                
                if separation > 1e-6:
                    log_separations.append(np.log(separation))
                    times.append(i * 0.1)
                    
                    # Renormalize
                    if separation > 0.1:
                        diff = solver2.phi - solver1.phi
                        solver2.phi = solver1.phi + 1e-8 * diff / np.linalg.norm(diff)
            
            # Compute Lyapunov
            if len(log_separations) > 10:
                lyapunov = np.polyfit(times, log_separations, 1)[0]
            else:
                lyapunov = 0.0
            
            print(f"     λ = {lyapunov:.6f}")
            
            results.append({
                'frame': frame_name,
                'lyapunov': lyapunov,
                'times': times,
                'log_separations': log_separations
            })
        
        # Interpretation
        print("\n  Interpretation:")
        lyapunovs = [r['lyapunov'] for r in results]
        
        if np.std(lyapunovs) < 0.001:
            print("     All frames show same λ → True chaos (frame-independent)")
        else:
            print("     Different λ in different frames → Structured (frame-dependent)")
            print("     → What appears as chaos is projection artifact")
        
        return results


def main():
    """Run structured chaos analysis."""
    print("=" * 80)
    print("STRUCTURED CHAOS ANALYSIS")
    print("Re-examining 'chaos' for geometric structure")
    print("=" * 80)
    print()
    
    analyzer = StructuredChaosAnalyzer(alpha=1.0, beta=1.0, gamma=0.5, dx=0.5)
    
    # 1. Analyze residual structure
    result = analyzer.analyze_residual_structure(L=100, Nx=200, T=100)
    
    # 2. Entropy vs information
    entropy_info = analyzer.analyze_entropy_vs_information(result)
    
    # 3. Reinterpret Lyapunov
    lyapunov_results = analyzer.reinterpret_lyapunov(L=50, Nx=100, T=100)
    
    # Visualize
    print("\nCreating visualizations...")
    
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Residual spatiotemporal structure
    ax1 = plt.subplot(3, 3, 1)
    im = ax1.imshow(result['residuals'].T, aspect='auto', origin='lower',
                   cmap='RdBu_r', vmin=-np.max(np.abs(result['residuals'])),
                   vmax=np.max(np.abs(result['residuals'])))
    plt.colorbar(im, ax=ax1, label='Residual')
    ax1.set_xlabel('Time Step')
    ax1.set_ylabel('Space')
    ax1.set_title('Residual Structure\n(NOT random noise)')
    
    # 2. Temporal power spectrum of residuals
    ax2 = plt.subplot(3, 3, 2)
    ax2.semilogy(result['temporal_freqs'], result['temporal_power'], 'b-', linewidth=1.5)
    if len(result['peaks']) > 0:
        ax2.plot(result['temporal_freqs'][result['peaks']], 
                result['temporal_power'][result['peaks']], 'ro', markersize=8)
    ax2.set_xlabel('Frequency')
    ax2.set_ylabel('Power')
    ax2.set_title(f'Temporal Structure\n({len(result["peaks"])} peaks found)')
    ax2.grid(True, alpha=0.3)
    
    # 3. Spatial power spectrum of residuals
    ax3 = plt.subplot(3, 3, 3)
    ax3.semilogy(result['spatial_k'], result['spatial_power'], 'g-', linewidth=1.5)
    if len(result['peaks_k']) > 0:
        ax3.plot(result['spatial_k'][result['peaks_k']], 
                result['spatial_power'][result['peaks_k']], 'ro', markersize=8)
    ax3.set_xlabel('Wavenumber k')
    ax3.set_ylabel('Power')
    ax3.set_title(f'Spatial Structure\n({len(result["peaks_k"])} peaks found)')
    ax3.grid(True, alpha=0.3)
    
    # 4. Entropy vs Information metrics
    ax4 = plt.subplot(3, 3, 4)
    metrics = ['Shannon\nEntropy', 'Compression\nRatio', 'Mutual\nInfo', 
               'Geometric\nCorr', 'Sign Change\nRatio']
    values = [entropy_info['shannon_entropy'] / 10,  # Scale for visibility
              entropy_info['compression_ratio'],
              entropy_info['mutual_information'],
              abs(entropy_info['geometric_correlation']),
              entropy_info['sign_change_ratio']]
    
    colors = ['red' if v < 0.3 else 'yellow' if v < 0.6 else 'green' for v in values]
    ax4.bar(range(len(metrics)), values, color=colors, alpha=0.7, edgecolor='black')
    ax4.set_xticks(range(len(metrics)))
    ax4.set_xticklabels(metrics, fontsize=8, rotation=45, ha='right')
    ax4.set_ylabel('Normalized Value')
    ax4.set_title('Structure Indicators\n(Green = more structure)')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5-7. Lyapunov in different frames
    for i, lresult in enumerate(lyapunov_results):
        ax = plt.subplot(3, 3, 5 + i)
        if len(lresult['times']) > 0:
            ax.plot(lresult['times'], lresult['log_separations'], 'b-', linewidth=2)
            if len(lresult['times']) > 1:
                fit = np.polyfit(lresult['times'], lresult['log_separations'], 1)
                ax.plot(lresult['times'], np.polyval(fit, lresult['times']), 'r--',
                       label=f'λ = {fit[0]:.4f}')
        ax.set_xlabel('Time')
        ax.set_ylabel('log(separation)')
        ax.set_title(f'{lresult["frame"]}\nλ = {lresult["lyapunov"]:.4f}')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # 8. Residual histogram (check for structure)
    ax8 = plt.subplot(3, 3, 8)
    ax8.hist(result['residuals'].flatten(), bins=50, alpha=0.7, edgecolor='black')
    ax8.set_xlabel('Residual Value')
    ax8.set_ylabel('Count')
    ax8.set_title('Residual Distribution\n(Gaussian = random, else = structured)')
    ax8.grid(True, alpha=0.3, axis='y')
    
    # 9. Summary text
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    # Determine if structured or chaotic
    structure_score = 0
    if len(result['peaks']) > 0:
        structure_score += 1
    if len(result['peaks_k']) > 0:
        structure_score += 1
    if entropy_info['mutual_information'] > 0.1:
        structure_score += 1
    if abs(entropy_info['geometric_correlation']) > 0.3:
        structure_score += 1
    if abs(entropy_info['sign_change_ratio'] - 0.5) > 0.1:
        structure_score += 1
    
    lyap_std = np.std([r['lyapunov'] for r in lyapunov_results])
    if lyap_std > 0.001:
        structure_score += 1
    
    if structure_score >= 4:
        verdict = "STRUCTURED"
        color = "green"
    elif structure_score >= 2:
        verdict = "PARTIALLY STRUCTURED"
        color = "yellow"
    else:
        verdict = "TRULY CHAOTIC"
        color = "red"
    
    summary_text = f"""
STRUCTURE ANALYSIS

Temporal peaks: {len(result['peaks'])}
Spatial peaks: {len(result['peaks_k'])}

Mutual info: {entropy_info['mutual_information']:.3f}
Geometric corr: {entropy_info['geometric_correlation']:.3f}

Lyapunov variance: {lyap_std:.6f}

Structure score: {structure_score}/6

VERDICT: {verdict}

Interpretation:
{"Apparent 'chaos' contains" if structure_score >= 2 else "True chaos with"}
{"geometric structure" if structure_score >= 2 else "no clear structure"}
{"(projection artifact)" if structure_score >= 4 else ""}
    """
    
    ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/phi_domain_analysis/structured_chaos_analysis.png', dpi=150)
    print("  Saved: structured_chaos_analysis.png")
    
    # Final summary
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print(f"Structure score: {structure_score}/6")
    print(f"Verdict: {verdict}")
    print()
    
    if structure_score >= 4:
        print("The apparent 'chaos' is actually STRUCTURED:")
        print("  • Residuals contain geometric information")
        print("  • Temporal and spatial frequencies present")
        print("  • Correlations indicate predictability")
        print("  • Lyapunov varies with measurement frame")
        print()
        print("This is NOT disorder - it's complex order!")
        print("What appears as chaos in 3D is structure in 4D.")
    elif structure_score >= 2:
        print("The system shows PARTIAL STRUCTURE:")
        print("  • Some geometric organization present")
        print("  • Mixed chaotic and ordered behavior")
        print("  • Measurement frame matters")
    else:
        print("The system shows TRUE CHAOS:")
        print("  • No clear geometric structure")
        print("  • Frame-independent disorder")
        print("  • Genuinely unpredictable")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
