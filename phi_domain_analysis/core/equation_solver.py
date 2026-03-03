"""
Enhanced φ-Equation Solver with Advanced Analysis Capabilities

This module provides a comprehensive solver for the φ-equation with tools for:
- Parameter fitting from data
- Conservation law testing
- Fixed point analysis
- Lyapunov exponent computation
- Pattern extraction and characterization
"""

import numpy as np
from scipy.ndimage import laplace, sobel
from scipy.optimize import minimize, fsolve
from scipy.linalg import eig
import warnings
warnings.filterwarnings('ignore')


class AdvancedPhiSolver:
    """
    Enhanced solver for φ-equation with analysis capabilities
    
    Equation: φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
    """
    
    def __init__(self, domain_size, dx, alpha, beta, gamma, dim=2):
        """
        Initialize solver
        
        Parameters:
        -----------
        domain_size : tuple
            Size of domain (Nx,) for 1D or (Nx, Ny) for 2D
        dx : float
            Spatial step size
        alpha : float
            Diffusion coefficient
        beta : float
            Reaction strength
        gamma : float
            Gradient penalty coefficient
        dim : int
            Dimension (1 or 2)
        """
        self.domain_size = domain_size
        self.dx = dx
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dim = dim
        
        # Initialize field
        if dim == 1:
            self.phi = np.zeros(domain_size[0])
            self.x = np.arange(domain_size[0]) * dx
        else:
            self.phi = np.zeros(domain_size)
            self.x = np.arange(domain_size[0]) * dx
            self.y = np.arange(domain_size[1]) * dx
            self.X, self.Y = np.meshgrid(self.x, self.y, indexing='ij')
        
        self.time = 0
        self.history = []
        
    def compute_laplacian(self, phi):
        """Compute Laplacian using finite differences"""
        if self.dim == 1:
            lap = np.zeros_like(phi)
            lap[1:-1] = (phi[2:] - 2*phi[1:-1] + phi[:-2]) / self.dx**2
            # Periodic boundary conditions
            lap[0] = (phi[1] - 2*phi[0] + phi[-1]) / self.dx**2
            lap[-1] = (phi[0] - 2*phi[-1] + phi[-2]) / self.dx**2
        else:
            # Use scipy's Laplacian with periodic boundaries
            lap = laplace(phi, mode='wrap') / self.dx**2
        return lap
    
    def compute_gradient_magnitude(self, phi):
        """Compute |∇φ|"""
        if self.dim == 1:
            grad = np.zeros_like(phi)
            grad[1:-1] = (phi[2:] - phi[:-2]) / (2*self.dx)
            grad[0] = (phi[1] - phi[-1]) / (2*self.dx)
            grad[-1] = (phi[0] - phi[-2]) / (2*self.dx)
            return np.abs(grad)
        else:
            # Use Sobel operator for gradient
            gx = sobel(phi, axis=0, mode='wrap') / (2*self.dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*self.dx)
            return np.sqrt(gx**2 + gy**2)
    
    def compute_gradient_vector(self, phi):
        """Compute gradient vector (∇φ)"""
        if self.dim == 1:
            grad = np.zeros_like(phi)
            grad[1:-1] = (phi[2:] - phi[:-2]) / (2*self.dx)
            grad[0] = (phi[1] - phi[-1]) / (2*self.dx)
            grad[-1] = (phi[0] - phi[-2]) / (2*self.dx)
            return grad
        else:
            gx = sobel(phi, axis=0, mode='wrap') / (2*self.dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*self.dx)
            return gx, gy
    
    def step(self):
        """
        Perform one time step with adaptive time stepping
        
        Automatically determines stable time step based on CFL condition
        and magnitude of non-linear terms.
        """
        # Compute spatial derivatives
        lap_phi = self.compute_laplacian(self.phi)
        grad_mag = self.compute_gradient_magnitude(self.phi)
        
        # Compute terms (fully non-linear)
        diffusion_term = self.alpha * (lap_phi - self.gamma * grad_mag**2)
        reaction_term = self.beta * np.tanh(self.phi) * np.exp(-grad_mag)
        
        # Total update
        total_update = diffusion_term + reaction_term
        
        # Adaptive time step for stability
        # CFL condition for diffusion: dt < dx²/(2α)
        dt_diffusion = 0.25 * self.dx**2 / (self.alpha + 1e-10)
        
        # Limit based on update magnitude (ensure |update| < 0.5 * |phi|)
        max_update = np.max(np.abs(total_update))
        max_phi = np.max(np.abs(self.phi)) + 1e-10
        dt_nonlinear = 0.5 * max_phi / (max_update + 1e-10)
        
        # Take minimum of constraints, cap at 1.0
        dt = min(dt_diffusion, dt_nonlinear, 1.0)
        
        # Apply update
        self.phi = self.phi + dt * total_update
        
        self.time += dt
        
        return self.phi.copy()
    
    def run(self, n_steps, save_interval=1):
        """Run simulation for n_steps"""
        self.history = [self.phi.copy()]
        
        for i in range(n_steps):
            self.step()
            if (i + 1) % save_interval == 0:
                self.history.append(self.phi.copy())
        
        return np.array(self.history)
    
    def set_initial_condition(self, ic_type='random', amplitude=0.1, **kwargs):
        """Set initial condition"""
        if ic_type == 'random':
            self.phi = amplitude * np.random.randn(*self.domain_size)
        
        elif ic_type == 'gaussian':
            if self.dim == 1:
                center = kwargs.get('center', self.domain_size[0] // 2)
                width = kwargs.get('width', 10)
                self.phi = amplitude * np.exp(-((self.x - center*self.dx)**2) / (2*width**2))
            else:
                center = kwargs.get('center', (self.domain_size[0]//2, self.domain_size[1]//2))
                width = kwargs.get('width', 10)
                r2 = (self.X - center[0]*self.dx)**2 + (self.Y - center[1]*self.dx)**2
                self.phi = amplitude * np.exp(-r2 / (2*width**2))
        
        elif ic_type == 'step':
            if self.dim == 1:
                center = kwargs.get('center', self.domain_size[0] // 2)
                self.phi[:center] = -amplitude
                self.phi[center:] = amplitude
            else:
                center = kwargs.get('center', self.domain_size[0] // 2)
                self.phi[:center, :] = -amplitude
                self.phi[center:, :] = amplitude
        
        elif ic_type == 'sine':
            k = kwargs.get('k', 2*np.pi/self.domain_size[0])
            if self.dim == 1:
                self.phi = amplitude * np.sin(k * self.x)
            else:
                self.phi = amplitude * np.sin(k * self.X)
        
        elif ic_type == 'localized':
            # Multiple localized spots
            n_spots = kwargs.get('n_spots', 5)
            width = kwargs.get('width', 5)
            if self.dim == 2:
                for _ in range(n_spots):
                    cx = np.random.randint(0, self.domain_size[0])
                    cy = np.random.randint(0, self.domain_size[1])
                    r2 = (self.X - cx*self.dx)**2 + (self.Y - cy*self.dx)**2
                    self.phi += amplitude * np.exp(-r2 / (2*width**2))
        
        self.time = 0
        self.history = []
    
    # ========== ADVANCED ANALYSIS METHODS ==========
    
    def find_fixed_points(self, n_trials=10):
        """
        Find fixed points of the system
        
        Returns:
        --------
        fixed_points : list of arrays
            List of fixed point field configurations
        """
        fixed_points = []
        
        def residual(phi_flat):
            """Residual for fixed point: φ_next - φ = 0"""
            phi = phi_flat.reshape(self.domain_size)
            
            lap_phi = self.compute_laplacian(phi)
            grad_mag = self.compute_gradient_magnitude(phi)
            
            diffusion = self.alpha * (lap_phi - self.gamma * grad_mag**2)
            reaction = self.beta * np.tanh(phi) * np.exp(-grad_mag)
            
            residual = diffusion + reaction
            return residual.flatten()
        
        # Try multiple initial guesses
        for _ in range(n_trials):
            phi0 = np.random.randn(*self.domain_size) * 0.1
            
            try:
                result = fsolve(residual, phi0.flatten(), full_output=True)
                phi_fp = result[0].reshape(self.domain_size)
                info = result[1]
                
                # Check if solution is valid
                if info['fvec'].max() < 1e-6:
                    # Check if this is a new fixed point
                    is_new = True
                    for fp in fixed_points:
                        if np.allclose(phi_fp, fp, atol=1e-4):
                            is_new = False
                            break
                    
                    if is_new:
                        fixed_points.append(phi_fp)
            except:
                pass
        
        return fixed_points
    
    def compute_jacobian_eigenvalues(self, phi):
        """
        Compute eigenvalues of Jacobian at given field configuration
        
        For stability analysis of fixed points
        
        Parameters:
        -----------
        phi : array
            Field configuration
            
        Returns:
        --------
        eigenvalues : array
            Eigenvalues of Jacobian
        """
        # For small systems, compute full Jacobian
        # For large systems, use iterative methods
        
        if np.prod(self.domain_size) > 1000:
            print("Warning: Jacobian computation expensive for large systems")
            return None
        
        n = np.prod(self.domain_size)
        J = np.zeros((n, n))
        
        # Compute Jacobian by finite differences
        eps = 1e-6
        phi_flat = phi.flatten()
        
        def f(phi_flat):
            """Evolution function"""
            phi = phi_flat.reshape(self.domain_size)
            lap_phi = self.compute_laplacian(phi)
            grad_mag = self.compute_gradient_magnitude(phi)
            diffusion = self.alpha * (lap_phi - self.gamma * grad_mag**2)
            reaction = self.beta * np.tanh(phi) * np.exp(-grad_mag)
            return (diffusion + reaction).flatten()
        
        f0 = f(phi_flat)
        
        for i in range(n):
            phi_pert = phi_flat.copy()
            phi_pert[i] += eps
            f_pert = f(phi_pert)
            J[:, i] = (f_pert - f0) / eps
        
        # Add identity (since φ_next = φ + f(φ))
        J = np.eye(n) + J
        
        eigenvalues = eig(J)[0]
        return eigenvalues
    
    def test_conserved_quantity(self, quantity_func, n_steps=1000):
        """
        Test if a quantity is conserved
        
        Parameters:
        -----------
        quantity_func : callable
            Function that computes quantity from phi
        n_steps : int
            Number of steps to test
            
        Returns:
        --------
        is_conserved : bool
            Whether quantity is conserved
        values : array
            Values of quantity over time
        """
        values = []
        
        for _ in range(n_steps):
            q = quantity_func(self.phi)
            values.append(q)
            self.step()
        
        values = np.array(values)
        
        # Check if variance is small
        relative_variance = np.std(values) / (np.abs(np.mean(values)) + 1e-10)
        is_conserved = relative_variance < 1e-3
        
        return is_conserved, values
    
    def compute_lyapunov_exponent(self, n_steps=10000, n_transient=1000):
        """
        Compute largest Lyapunov exponent
        
        Measures sensitivity to initial conditions (chaos indicator)
        
        Returns:
        --------
        lyapunov : float
            Largest Lyapunov exponent
        """
        # Initialize two nearby trajectories
        phi1 = self.phi.copy()
        phi2 = phi1 + 1e-8 * np.random.randn(*self.domain_size)
        
        lyapunov_sum = 0.0
        
        for i in range(n_steps + n_transient):
            # Evolve both
            phi1_next = self._evolve_once(phi1)
            phi2_next = self._evolve_once(phi2)
            
            # Compute separation
            delta = phi2_next - phi1_next
            distance = np.linalg.norm(delta)
            
            if i >= n_transient:
                lyapunov_sum += np.log(distance / 1e-8)
            
            # Renormalize
            phi2_next = phi1_next + (delta / distance) * 1e-8
            
            phi1 = phi1_next
            phi2 = phi2_next
        
        lyapunov = lyapunov_sum / n_steps
        return lyapunov
    
    def _evolve_once(self, phi):
        """Single evolution step (helper for Lyapunov)"""
        lap_phi = self.compute_laplacian(phi)
        grad_mag = self.compute_gradient_magnitude(phi)
        diffusion = self.alpha * (lap_phi - self.gamma * grad_mag**2)
        reaction = self.beta * np.tanh(phi) * np.exp(-grad_mag)
        return phi + diffusion + reaction
    
    def extract_pattern_wavelength(self):
        """
        Extract dominant pattern wavelength using FFT
        
        Returns:
        --------
        wavelength : float
            Dominant wavelength
        """
        if self.dim == 1:
            fft = np.fft.fft(self.phi)
            power = np.abs(fft)**2
            freqs = np.fft.fftfreq(len(self.phi), self.dx)
        else:
            fft = np.fft.fft2(self.phi)
            power = np.abs(fft)**2
            kx = np.fft.fftfreq(self.phi.shape[0], self.dx)
            ky = np.fft.fftfreq(self.phi.shape[1], self.dx)
            KX, KY = np.meshgrid(kx, ky, indexing='ij')
            freqs = np.sqrt(KX**2 + KY**2)
        
        # Exclude DC component
        power.flat[0] = 0
        
        # Find peak
        peak_idx = np.argmax(power)
        if self.dim == 1:
            k_peak = np.abs(freqs[peak_idx])
        else:
            k_peak = freqs.flat[peak_idx]
        
        wavelength = 2*np.pi / k_peak if k_peak > 0 else np.inf
        return wavelength
    
    def measure_edge_width(self):
        """
        Measure characteristic edge width
        
        Returns:
        --------
        edge_width : float
            Average width of high-gradient regions
        """
        grad_mag = self.compute_gradient_magnitude(self.phi)
        
        # Find regions with high gradients
        threshold = np.percentile(grad_mag, 90)
        edge_regions = grad_mag > threshold
        
        if np.sum(edge_regions) == 0:
            return 0.0
        
        # Measure width of edge regions
        if self.dim == 1:
            edge_widths = []
            in_edge = False
            width = 0
            
            for val in edge_regions:
                if val:
                    width += 1
                    in_edge = True
                else:
                    if in_edge:
                        edge_widths.append(width)
                        width = 0
                        in_edge = False
            
            return np.mean(edge_widths) * self.dx if edge_widths else 0.0
        else:
            # For 2D, estimate from gradient distribution
            return 1.0 / np.mean(grad_mag[edge_regions])
    
    def compute_energy(self):
        """
        Compute approximate energy functional
        
        E = ∫ [α/2 |∇φ|² - α·γ/4 |∇φ|⁴ - β·log(cosh(φ))·e^(-|∇φ|)] dx
        
        Returns:
        --------
        energy : float
            Total energy
        """
        grad_mag = self.compute_gradient_magnitude(self.phi)
        
        E_grad = 0.5 * self.alpha * np.sum(grad_mag**2)
        E_quartic = -0.25 * self.alpha * self.gamma * np.sum(grad_mag**4)
        E_reaction = -self.beta * np.sum(np.log(np.cosh(self.phi)) * np.exp(-grad_mag))
        
        volume_element = self.dx**self.dim
        energy = (E_grad + E_quartic + E_reaction) * volume_element
        
        return energy
    
    def compute_entropy_production(self):
        """
        Compute entropy production rate
        
        σ = ∫ (∂φ/∂t)² dx
        
        Returns:
        --------
        entropy_rate : float
            Entropy production rate
        """
        # Compute time derivative
        lap_phi = self.compute_laplacian(self.phi)
        grad_mag = self.compute_gradient_magnitude(self.phi)
        diffusion = self.alpha * (lap_phi - self.gamma * grad_mag**2)
        reaction = self.beta * np.tanh(self.phi) * np.exp(-grad_mag)
        dphi_dt = diffusion + reaction
        
        entropy_rate = np.sum(dphi_dt**2) * self.dx**self.dim
        return entropy_rate
    
    def identify_topological_defects(self):
        """
        Identify topological defects (vortices, domain walls, etc.)
        
        Returns:
        --------
        defects : list
            List of defect locations and types
        """
        defects = []
        
        if self.dim == 2:
            # Compute winding number for vortices
            gx, gy = self.compute_gradient_vector(self.phi)
            
            # Look for circulation in gradient field
            # This is a simplified detection - full topological analysis more complex
            curl = np.gradient(gy, axis=0) - np.gradient(gx, axis=1)
            
            # Find local maxima/minima of curl
            threshold = np.std(curl) * 3
            vortex_candidates = np.abs(curl) > threshold
            
            # Extract positions
            positions = np.argwhere(vortex_candidates)
            for pos in positions:
                charge = np.sign(curl[tuple(pos)])
                defects.append({
                    'type': 'vortex',
                    'position': pos * self.dx,
                    'charge': charge
                })
        
        return defects


if __name__ == "__main__":
    # Quick test
    print("Testing AdvancedPhiSolver...")
    
    solver = AdvancedPhiSolver((64, 64), dx=1.0, alpha=1.0, beta=2.0, gamma=0.1, dim=2)
    solver.set_initial_condition('random', amplitude=0.1)
    
    print("Running simulation...")
    history = solver.run(100, save_interval=10)
    
    print(f"Final variance: {np.var(history[-1]):.4f}")
    print(f"Pattern wavelength: {solver.extract_pattern_wavelength():.2f}")
    print(f"Edge width: {solver.measure_edge_width():.2f}")
    print(f"Energy: {solver.compute_energy():.4f}")
    
    print("\nAdvancedPhiSolver test complete!")
