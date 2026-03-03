"""
Analysis Metrics for φ-Equation

Comprehensive measurement tools for analyzing φ-field dynamics.

CRITICAL: All metrics respect the non-linear nature of the equation.
No linear approximations. Everything computed from actual field values.
"""

import numpy as np
from scipy.ndimage import sobel, laplace
from scipy.fft import fft, fft2, fftfreq
from scipy.signal import find_peaks
from scipy.spatial.distance import pdist, squareform


class AnalysisMetrics:
    """
    Comprehensive metrics for φ-field analysis
    
    All methods are static and work on field snapshots
    Fully respects non-linear dynamics
    """
    
    @staticmethod
    def pattern_wavelength(phi, dx=1.0):
        """
        Measure dominant pattern wavelength using FFT
        
        Non-linear Fourier analysis of spatial structure
        
        Parameters:
        -----------
        phi : array
            Field configuration
        dx : float
            Spatial step size
            
        Returns:
        --------
        wavelength : float
            Dominant wavelength
        power_spectrum : array
            Full power spectrum
        """
        if phi.ndim == 1:
            # 1D FFT
            fft_result = fft(phi)
            power = np.abs(fft_result)**2
            freqs = fftfreq(len(phi), dx)
            
            # Exclude DC component
            power[0] = 0
            
            # Find peak
            peak_idx = np.argmax(power)
            k_peak = np.abs(freqs[peak_idx])
            
        else:
            # 2D FFT
            fft_result = fft2(phi)
            power = np.abs(fft_result)**2
            
            kx = fftfreq(phi.shape[0], dx)
            ky = fftfreq(phi.shape[1], dx)
            KX, KY = np.meshgrid(kx, ky, indexing='ij')
            k_mag = np.sqrt(KX**2 + KY**2)
            
            # Exclude DC
            power[0, 0] = 0
            
            # Find peak in radial average
            k_bins = np.linspace(0, k_mag.max(), 50)
            power_radial = np.zeros(len(k_bins) - 1)
            
            for i in range(len(k_bins) - 1):
                mask = (k_mag >= k_bins[i]) & (k_mag < k_bins[i+1])
                if np.any(mask):
                    power_radial[i] = np.mean(power[mask])
            
            peak_idx = np.argmax(power_radial)
            k_peak = (k_bins[peak_idx] + k_bins[peak_idx + 1]) / 2
        
        wavelength = 2*np.pi / k_peak if k_peak > 0 else np.inf
        
        return wavelength, power
    
    @staticmethod
    def edge_width(phi, dx=1.0, percentile=90):
        """
        Measure characteristic edge width
        
        Analyzes high-gradient regions (edges/boundaries)
        Fully non-linear measurement
        
        Parameters:
        -----------
        phi : array
            Field configuration
        dx : float
            Spatial step size
        percentile : float
            Percentile for defining "edge" regions
            
        Returns:
        --------
        width : float
            Average edge width
        edge_mask : array
            Boolean mask of edge regions
        """
        # Compute gradient magnitude (non-linear)
        if phi.ndim == 1:
            grad = np.gradient(phi, dx)
            grad_mag = np.abs(grad)
        else:
            gx = sobel(phi, axis=0, mode='wrap') / (2*dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*dx)
            grad_mag = np.sqrt(gx**2 + gy**2)
        
        # Define edge regions
        threshold = np.percentile(grad_mag, percentile)
        edge_mask = grad_mag > threshold
        
        if not np.any(edge_mask):
            return 0.0, edge_mask
        
        # Estimate width from inverse gradient
        # Higher gradient = sharper edge = smaller width
        edge_gradients = grad_mag[edge_mask]
        width = dx / np.mean(edge_gradients)
        
        return width, edge_mask
    
    @staticmethod
    def gradient_distribution(phi, dx=1.0, n_bins=50):
        """
        Analyze distribution of gradient magnitudes
        
        Reveals structure of field: smooth vs. sharp regions
        
        Parameters:
        -----------
        phi : array
            Field configuration
        dx : float
            Spatial step size
        n_bins : int
            Number of histogram bins
            
        Returns:
        --------
        hist : array
            Histogram counts
        bins : array
            Bin edges
        stats : dict
            Statistical measures
        """
        # Compute gradient magnitude
        if phi.ndim == 1:
            grad = np.gradient(phi, dx)
            grad_mag = np.abs(grad)
        else:
            gx = sobel(phi, axis=0, mode='wrap') / (2*dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*dx)
            grad_mag = np.sqrt(gx**2 + gy**2)
        
        # Histogram
        hist, bins = np.histogram(grad_mag, bins=n_bins)
        
        # Statistics
        stats = {
            'mean': np.mean(grad_mag),
            'std': np.std(grad_mag),
            'median': np.median(grad_mag),
            'max': np.max(grad_mag),
            'percentile_90': np.percentile(grad_mag, 90),
            'percentile_95': np.percentile(grad_mag, 95)
        }
        
        return hist, bins, stats
    
    @staticmethod
    def correlation_length(phi, dx=1.0):
        """
        Measure spatial correlation length
        
        Computes two-point correlation function and extracts decay length
        Non-linear correlation analysis
        
        Parameters:
        -----------
        phi : array
            Field configuration
        dx : float
            Spatial step size
            
        Returns:
        --------
        xi : float
            Correlation length
        correlation_func : array
            Full correlation function
        """
        # Center field (remove mean)
        phi_centered = phi - np.mean(phi)
        
        if phi.ndim == 1:
            # 1D correlation function
            n = len(phi)
            corr = np.correlate(phi_centered, phi_centered, mode='full')
            corr = corr[n-1:] / corr[n-1]  # Normalize
            
            # Find decay length (where correlation drops to 1/e)
            distances = np.arange(len(corr)) * dx
            try:
                xi_idx = np.where(corr < 1/np.e)[0][0]
                xi = distances[xi_idx]
            except:
                xi = distances[-1]  # If doesn't decay, use system size
            
        else:
            # 2D radial correlation function
            # Compute via FFT (faster for large systems)
            fft_phi = fft2(phi_centered)
            power = np.abs(fft_phi)**2
            corr_2d = np.real(np.fft.ifft2(power))
            corr_2d = np.fft.fftshift(corr_2d)
            corr_2d /= corr_2d.max()
            
            # Radial average
            center = np.array(corr_2d.shape) // 2
            y, x = np.ogrid[:corr_2d.shape[0], :corr_2d.shape[1]]
            r = np.sqrt((x - center[1])**2 + (y - center[0])**2)
            
            r_bins = np.arange(0, r.max(), 1)
            corr = np.zeros(len(r_bins) - 1)
            
            for i in range(len(r_bins) - 1):
                mask = (r >= r_bins[i]) & (r < r_bins[i+1])
                if np.any(mask):
                    corr[i] = np.mean(corr_2d[mask])
            
            distances = (r_bins[:-1] + r_bins[1:]) / 2 * dx
            
            # Find decay length
            try:
                xi_idx = np.where(corr < 1/np.e)[0][0]
                xi = distances[xi_idx]
            except:
                xi = distances[-1]
        
        return xi, corr
    
    @staticmethod
    def entropy_production(phi, alpha, beta, gamma, dx=1.0):
        """
        Compute thermodynamic entropy production rate
        
        σ = ∫ (∂φ/∂t)² dx
        
        Measures irreversibility of dynamics
        
        Parameters:
        -----------
        phi : array
            Field configuration
        alpha, beta, gamma : float
            Equation parameters
        dx : float
            Spatial step size
            
        Returns:
        --------
        sigma : float
            Entropy production rate
        """
        # Compute time derivative from φ-equation
        if phi.ndim == 1:
            lap = np.gradient(np.gradient(phi, dx), dx)
            grad = np.gradient(phi, dx)
            grad_mag = np.abs(grad)
        else:
            lap = laplace(phi, mode='wrap') / dx**2
            gx = sobel(phi, axis=0, mode='wrap') / (2*dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*dx)
            grad_mag = np.sqrt(gx**2 + gy**2)
        
        # φ-equation terms (fully non-linear)
        diffusion = alpha * (lap - gamma * grad_mag**2)
        reaction = beta * np.tanh(phi) * np.exp(-grad_mag)
        dphi_dt = diffusion + reaction
        
        # Entropy production
        sigma = np.sum(dphi_dt**2) * dx**phi.ndim
        
        return sigma
    
    @staticmethod
    def information_content(phi):
        """
        Measure information theoretic quantities
        
        Computes Shannon entropy and related measures
        
        Parameters:
        -----------
        phi : array
            Field configuration
            
        Returns:
        --------
        info : dict
            Information measures
        """
        # Discretize field values for probability estimation
        hist, bins = np.histogram(phi, bins=50, density=True)
        bin_width = bins[1] - bins[0]
        
        # Probability distribution
        p = hist * bin_width
        p = p[p > 0]  # Remove zeros
        
        # Shannon entropy
        shannon_entropy = -np.sum(p * np.log2(p))
        
        # Variance (measure of spread)
        variance = np.var(phi)
        
        # Kurtosis (measure of tail heaviness)
        kurtosis = np.mean((phi - np.mean(phi))**4) / variance**2 - 3
        
        # Skewness (measure of asymmetry)
        skewness = np.mean((phi - np.mean(phi))**3) / variance**1.5
        
        info = {
            'shannon_entropy': shannon_entropy,
            'variance': variance,
            'kurtosis': kurtosis,
            'skewness': skewness,
            'range': np.ptp(phi),
            'mean': np.mean(phi),
            'std': np.std(phi)
        }
        
        return info
    
    @staticmethod
    def topological_charge(phi, dx=1.0):
        """
        Compute topological charge for 2D fields
        
        Identifies vortices and other topological defects
        Non-linear topological analysis
        
        Parameters:
        -----------
        phi : array (2D)
            Field configuration
        dx : float
            Spatial step size
            
        Returns:
        --------
        total_charge : float
            Total topological charge
        charge_density : array
            Spatial distribution of charge
        """
        if phi.ndim != 2:
            raise ValueError("Topological charge only defined for 2D fields")
        
        # Compute gradient components
        gx = sobel(phi, axis=0, mode='wrap') / (2*dx)
        gy = sobel(phi, axis=1, mode='wrap') / (2*dx)
        
        # Compute curl of gradient (topological charge density)
        # This detects vortices and other topological structures
        curl_x = np.gradient(gy, axis=0)
        curl_y = np.gradient(gx, axis=1)
        charge_density = curl_x - curl_y
        
        # Total charge (integrated over space)
        total_charge = np.sum(charge_density) * dx**2 / (2*np.pi)
        
        return total_charge, charge_density
    
    @staticmethod
    def measure_coarsening_exponent(history, times, dx=1.0):
        """
        Measure coarsening exponent from temporal evolution
        
        Fits R(t) ~ t^n where R is characteristic length scale
        
        Parameters:
        -----------
        history : array
            Temporal sequence of fields
        times : array
            Time points
        dx : float
            Spatial step size
            
        Returns:
        --------
        exponent : float
            Coarsening exponent n
        length_scales : array
            Measured length scales over time
        """
        length_scales = []
        
        for phi in history:
            # Measure characteristic length from correlation or wavelength
            wavelength, _ = AnalysisMetrics.pattern_wavelength(phi, dx)
            length_scales.append(wavelength)
        
        length_scales = np.array(length_scales)
        
        # Fit power law: R ~ t^n
        # Use log-log fit
        valid = (length_scales > 0) & (times > 0) & np.isfinite(length_scales)
        
        if np.sum(valid) < 3:
            return np.nan, length_scales
        
        log_t = np.log(times[valid])
        log_R = np.log(length_scales[valid])
        
        # Linear fit in log-log space
        coeffs = np.polyfit(log_t, log_R, 1)
        exponent = coeffs[0]
        
        return exponent, length_scales
    
    @staticmethod
    def measure_critical_exponents(phi_history, control_param, critical_value):
        """
        Measure critical exponents near phase transition
        
        Analyzes behavior near critical point
        
        Parameters:
        -----------
        phi_history : list of arrays
            Fields at different control parameter values
        control_param : array
            Control parameter values (e.g., β)
        critical_value : float
            Critical value of control parameter
            
        Returns:
        --------
        exponents : dict
            Critical exponents
        """
        # Distance from critical point
        epsilon = np.abs(control_param - critical_value)
        
        # Order parameter (mean field value)
        order_param = np.array([np.mean(np.abs(phi)) for phi in phi_history])
        
        # Correlation length
        corr_lengths = np.array([AnalysisMetrics.correlation_length(phi)[0] 
                                 for phi in phi_history])
        
        # Fit power laws near critical point
        near_critical = epsilon < 0.2 * critical_value
        
        if np.sum(near_critical) < 3:
            return {'beta': np.nan, 'nu': np.nan}
        
        # Order parameter exponent β: m ~ ε^β
        log_eps = np.log(epsilon[near_critical])
        log_m = np.log(order_param[near_critical] + 1e-10)
        beta_exp = np.polyfit(log_eps, log_m, 1)[0]
        
        # Correlation length exponent ν: ξ ~ ε^(-ν)
        log_xi = np.log(corr_lengths[near_critical] + 1e-10)
        nu_exp = -np.polyfit(log_eps, log_xi, 1)[0]
        
        exponents = {
            'beta': beta_exp,
            'nu': nu_exp
        }
        
        return exponents
    
    @staticmethod
    def compute_structure_factor(phi, dx=1.0):
        """
        Compute structure factor S(k)
        
        Fourier space characterization of spatial structure
        
        Parameters:
        -----------
        phi : array
            Field configuration
        dx : float
            Spatial step size
            
        Returns:
        --------
        k : array
            Wave vectors
        S_k : array
            Structure factor
        """
        if phi.ndim == 1:
            fft_phi = fft(phi - np.mean(phi))
            S_k = np.abs(fft_phi)**2 / len(phi)
            k = fftfreq(len(phi), dx) * 2*np.pi
            
            # Sort by k
            sort_idx = np.argsort(k)
            k = k[sort_idx]
            S_k = S_k[sort_idx]
            
        else:
            fft_phi = fft2(phi - np.mean(phi))
            power = np.abs(fft_phi)**2 / phi.size
            
            kx = fftfreq(phi.shape[0], dx) * 2*np.pi
            ky = fftfreq(phi.shape[1], dx) * 2*np.pi
            KX, KY = np.meshgrid(kx, ky, indexing='ij')
            k_mag = np.sqrt(KX**2 + KY**2)
            
            # Radial average
            k_bins = np.linspace(0, k_mag.max(), 50)
            S_k = np.zeros(len(k_bins) - 1)
            k = np.zeros(len(k_bins) - 1)
            
            for i in range(len(k_bins) - 1):
                mask = (k_mag >= k_bins[i]) & (k_mag < k_bins[i+1])
                if np.any(mask):
                    S_k[i] = np.mean(power[mask])
                    k[i] = (k_bins[i] + k_bins[i+1]) / 2
        
        return k, S_k


if __name__ == "__main__":
    # Test metrics
    print("Testing AnalysisMetrics...")
    
    # Create test field with pattern
    x = np.linspace(0, 20*np.pi, 128)
    y = np.linspace(0, 20*np.pi, 128)
    X, Y = np.meshgrid(x, y)
    
    # Pattern with multiple scales
    phi = np.sin(X) * np.cos(Y) + 0.5*np.sin(2*X) * np.cos(2*Y)
    phi += 0.1 * np.random.randn(*phi.shape)
    
    print("\nPattern wavelength:")
    wavelength, _ = AnalysisMetrics.pattern_wavelength(phi, dx=x[1]-x[0])
    print(f"  λ = {wavelength:.2f}")
    
    print("\nEdge width:")
    width, _ = AnalysisMetrics.edge_width(phi, dx=x[1]-x[0])
    print(f"  w = {width:.2f}")
    
    print("\nCorrelation length:")
    xi, _ = AnalysisMetrics.correlation_length(phi, dx=x[1]-x[0])
    print(f"  ξ = {xi:.2f}")
    
    print("\nInformation content:")
    info = AnalysisMetrics.information_content(phi)
    for key, val in info.items():
        print(f"  {key}: {val:.4f}")
    
    print("\nTopological charge:")
    charge, _ = AnalysisMetrics.topological_charge(phi, dx=x[1]-x[0])
    print(f"  Q = {charge:.4f}")
    
    print("\nAnalysisMetrics test complete!")
