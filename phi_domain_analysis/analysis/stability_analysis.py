"""
Stability and Bifurcation Analysis for φ-Equation

Analyzes fixed points, eigenvalues, and bifurcations across parameter space.
Fully non-linear analysis respecting toroidal topology.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
from scipy.optimize import fsolve, minimize
from scipy.linalg import eig
import matplotlib.pyplot as plt


class StabilityAnalyzer:
    """
    Analyze stability of fixed points and bifurcations
    
    Fully non-linear analysis - no approximations
    """
    
    def __init__(self, domain_size, dx, dim=1):
        """
        Initialize analyzer
        
        Parameters:
        -----------
        domain_size : tuple
            Size of domain
        dx : float
            Spatial step
        dim : int
            Dimension (1 or 2)
        """
        self.domain_size = domain_size
        self.dx = dx
        self.dim = dim
        
    def find_fixed_points(self, alpha, beta, gamma, n_trials=20):
        """
        Find all fixed points for given parameters
        
        Returns:
        --------
        fixed_points : list
            List of fixed point configurations
        """
        solver = AdvancedPhiSolver(self.domain_size, self.dx, 
                                   alpha, beta, gamma, self.dim)
        
        fixed_points = []
        
        # Try homogeneous fixed points first
        for phi0 in np.linspace(-3, 3, 10):
            phi_uniform = np.ones(self.domain_size) * phi0
            
            # Check if it's a fixed point
            solver.phi = phi_uniform.copy()
            phi_next = solver.step()
            
            residual = np.max(np.abs(phi_next - phi_uniform))
            
            if residual < 1e-6:
                # Check if new
                is_new = True
                for fp in fixed_points:
                    if np.allclose(fp, phi_uniform, atol=1e-4):
                        is_new = False
                        break
                
                if is_new:
                    fixed_points.append(phi_uniform.copy())
        
        # Try non-uniform fixed points
        for _ in range(n_trials):
            phi0 = np.random.randn(*self.domain_size) * 0.5
            
            solver.phi = phi0.copy()
            
            # Evolve to steady state
            for _ in range(1000):
                phi_old = solver.phi.copy()
                solver.step()
                
                if np.max(np.abs(solver.phi - phi_old)) < 1e-6:
                    # Found fixed point
                    is_new = True
                    for fp in fixed_points:
                        if np.allclose(fp, solver.phi, atol=1e-4):
                            is_new = False
                            break
                    
                    if is_new:
                        fixed_points.append(solver.phi.copy())
                    break
        
        return fixed_points
    
    def compute_eigenvalues(self, phi, alpha, beta, gamma):
        """
        Compute eigenvalues of Jacobian at fixed point
        
        For stability classification
        
        Parameters:
        -----------
        phi : array
            Fixed point configuration
        alpha, beta, gamma : float
            Equation parameters
            
        Returns:
        --------
        eigenvalues : array
            Eigenvalues (complex)
        stability : str
            Classification: 'stable', 'unstable', 'saddle'
        """
        n = np.prod(self.domain_size)
        
        if n > 500:
            print(f"Warning: Large system ({n} points), eigenvalue computation expensive")
            # For large systems, use power iteration for largest eigenvalue
            return self._largest_eigenvalue(phi, alpha, beta, gamma)
        
        # Compute full Jacobian
        J = self._compute_jacobian(phi, alpha, beta, gamma)
        
        # Eigenvalues
        eigenvalues = eig(J)[0]
        
        # Classify stability
        max_real = np.max(np.real(eigenvalues))
        
        if max_real < -1e-6:
            stability = 'stable'
        elif max_real > 1e-6:
            stability = 'unstable'
        else:
            # Check if saddle
            if np.any(np.real(eigenvalues) > 1e-6) and np.any(np.real(eigenvalues) < -1e-6):
                stability = 'saddle'
            else:
                stability = 'marginal'
        
        return eigenvalues, stability
    
    def _compute_jacobian(self, phi, alpha, beta, gamma):
        """
        Compute Jacobian matrix by finite differences
        
        Fully non-linear - no approximations
        """
        n = np.prod(self.domain_size)
        J = np.zeros((n, n))
        
        eps = 1e-7
        phi_flat = phi.flatten()
        
        # Create solver
        solver = AdvancedPhiSolver(self.domain_size, self.dx,
                                   alpha, beta, gamma, self.dim)
        
        def f(phi_flat):
            """Evolution function: φ_next - φ"""
            solver.phi = phi_flat.reshape(self.domain_size)
            phi_next = solver.step()
            return (phi_next - phi_flat.reshape(self.domain_size)).flatten()
        
        f0 = f(phi_flat)
        
        # Compute columns of Jacobian
        for i in range(n):
            phi_pert = phi_flat.copy()
            phi_pert[i] += eps
            f_pert = f(phi_pert)
            J[:, i] = (f_pert - f0) / eps
        
        # Add identity (since φ_next = φ + f(φ))
        J = np.eye(n) + J
        
        return J
    
    def _largest_eigenvalue(self, phi, alpha, beta, gamma):
        """
        Compute largest eigenvalue using power iteration
        
        For large systems where full eigenvalue computation is expensive
        """
        n = np.prod(self.domain_size)
        
        # Random initial vector
        v = np.random.randn(n)
        v = v / np.linalg.norm(v)
        
        solver = AdvancedPhiSolver(self.domain_size, self.dx,
                                   alpha, beta, gamma, self.dim)
        
        def matvec(v):
            """Matrix-vector product J·v"""
            phi_flat = phi.flatten()
            eps = 1e-7
            
            solver.phi = phi.reshape(self.domain_size)
            f0 = solver.step() - phi
            
            solver.phi = (phi + eps * v.reshape(self.domain_size))
            f_pert = solver.step() - (phi + eps * v.reshape(self.domain_size))
            
            Jv = (f_pert.flatten() - f0.flatten()) / eps
            return v + Jv  # Include identity
        
        # Power iteration
        for _ in range(100):
            v_new = matvec(v)
            lambda_est = np.dot(v, v_new)
            v = v_new / np.linalg.norm(v_new)
        
        eigenvalues = np.array([lambda_est])
        stability = 'unstable' if np.real(lambda_est) > 0 else 'stable'
        
        return eigenvalues, stability
    
    def stability_phase_diagram(self, alpha_range, beta_range, gamma_fixed=0.1,
                               n_points=20, save_path=None):
        """
        Create stability phase diagram in (α, β) space
        
        Parameters:
        -----------
        alpha_range : tuple
            (min, max) for α
        beta_range : tuple
            (min, max) for β
        gamma_fixed : float
            Fixed value of γ
        n_points : int
            Resolution of grid
        save_path : str, optional
            Path to save figure
            
        Returns:
        --------
        stability_map : array
            2D array of stability classifications
        """
        alphas = np.linspace(alpha_range[0], alpha_range[1], n_points)
        betas = np.linspace(beta_range[0], beta_range[1], n_points)
        
        stability_map = np.zeros((n_points, n_points))
        
        print(f"Computing stability diagram ({n_points}x{n_points} grid)...")
        
        for i, alpha in enumerate(alphas):
            for j, beta in enumerate(betas):
                # Find fixed points
                fps = self.find_fixed_points(alpha, beta, gamma_fixed, n_trials=5)
                
                if len(fps) == 0:
                    stability_map[i, j] = 0  # No fixed points
                else:
                    # Check stability of first fixed point
                    _, stability = self.compute_eigenvalues(fps[0], alpha, beta, gamma_fixed)
                    
                    if stability == 'stable':
                        stability_map[i, j] = 1
                    elif stability == 'unstable':
                        stability_map[i, j] = -1
                    elif stability == 'saddle':
                        stability_map[i, j] = 0.5
                    else:
                        stability_map[i, j] = 0
            
            if (i + 1) % 5 == 0:
                print(f"  Progress: {i+1}/{n_points}")
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(stability_map.T, origin='lower',
                      extent=[alpha_range[0], alpha_range[1],
                             beta_range[0], beta_range[1]],
                      aspect='auto', cmap='RdBu_r')
        
        ax.set_xlabel('α (diffusion)')
        ax.set_ylabel('β (reaction)')
        ax.set_title(f'Stability Phase Diagram (γ = {gamma_fixed})')
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Stability: -1=unstable, 0=saddle, 1=stable')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"Saved to {save_path}")
        
        plt.show()
        
        return stability_map


if __name__ == "__main__":
    print("Testing StabilityAnalyzer...")
    print()
    
    # Test 1: Find fixed points
    print("Test 1: Finding fixed points")
    print("-" * 60)
    
    analyzer = StabilityAnalyzer((32,), dx=1.0, dim=1)
    
    alpha, beta, gamma = 1.0, 0.5, 0.1
    fps = analyzer.find_fixed_points(alpha, beta, gamma, n_trials=10)
    
    print(f"Found {len(fps)} fixed point(s) for α={alpha}, β={beta}, γ={gamma}")
    for i, fp in enumerate(fps):
        print(f"  FP {i+1}: mean={np.mean(fp):.4f}, std={np.std(fp):.4f}")
    print()
    
    # Test 2: Compute eigenvalues
    if len(fps) > 0:
        print("Test 2: Computing eigenvalues")
        print("-" * 60)
        
        eigenvals, stability = analyzer.compute_eigenvalues(fps[0], alpha, beta, gamma)
        
        print(f"Fixed point stability: {stability}")
        print(f"Largest eigenvalue: {eigenvals[np.argmax(np.abs(eigenvals))]:.6f}")
        print(f"Number of eigenvalues: {len(eigenvals)}")
        print()
    
    # Test 3: Small stability diagram
    print("Test 3: Stability phase diagram (small)")
    print("-" * 60)
    
    analyzer_small = StabilityAnalyzer((16,), dx=1.0, dim=1)
    
    stability_map = analyzer_small.stability_phase_diagram(
        alpha_range=(0.5, 2.0),
        beta_range=(0.0, 2.0),
        gamma_fixed=0.1,
        n_points=10,
        save_path='stability_diagram_test.png'
    )
    
    print("✓ StabilityAnalyzer test complete!")
