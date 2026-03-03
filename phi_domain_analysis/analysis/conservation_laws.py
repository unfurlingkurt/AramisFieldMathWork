"""
Conservation Law Analysis for φ-Equation

Tests candidate conserved quantities numerically.
Searches for non-obvious conservation laws.
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from equation_solver import AdvancedPhiSolver
import matplotlib.pyplot as plt


class ConservationAnalyzer:
    """
    Test and identify conserved quantities
    
    Fully non-linear approach - no approximations
    """
    
    def __init__(self, solver):
        """
        Initialize analyzer
        
        Parameters:
        -----------
        solver : AdvancedPhiSolver
            Configured solver instance
        """
        self.solver = solver
        self.dx = solver.dx
        self.dim = solver.dim
        
    def compute_total_mass(self, phi):
        """
        Compute total mass (integral of φ)
        
        M = ∫ φ dV
        """
        if self.dim == 1:
            return np.sum(phi) * self.dx
        elif self.dim == 2:
            return np.sum(phi) * self.dx**2
        else:
            return np.sum(phi) * self.dx**3
    
    def compute_total_energy(self, phi):
        """
        Compute total energy
        
        E = ∫ [½|∇φ|² + V(φ)] dV
        
        where V(φ) is potential from reaction term
        """
        # Gradient energy
        grad_phi = self.solver.compute_gradient_magnitude(phi)
        grad_energy = 0.5 * np.sum(grad_phi**2)
        
        # Potential energy (integrate reaction term)
        # V(φ) such that -dV/dφ = β·tanh(φ)·e^(-|∇φ|)
        # Approximate: V(φ) ≈ -β·log(cosh(φ))·e^(-|∇φ|)
        potential = -self.solver.beta * np.log(np.cosh(phi)) * np.exp(-grad_phi)
        potential_energy = np.sum(potential)
        
        if self.dim == 1:
            return (grad_energy + potential_energy) * self.dx
        elif self.dim == 2:
            return (grad_energy + potential_energy) * self.dx**2
        else:
            return (grad_energy + potential_energy) * self.dx**3
    
    def compute_momentum(self, phi):
        """
        Compute total momentum
        
        P = ∫ φ·∇φ dV
        """
        grad_phi = self.solver.compute_gradient_magnitude(phi)
        momentum = phi * grad_phi
        
        if self.dim == 1:
            return np.sum(momentum) * self.dx
        elif self.dim == 2:
            return np.sum(momentum) * self.dx**2
        else:
            return np.sum(momentum) * self.dx**3
    
    def compute_l2_norm(self, phi):
        """
        Compute L² norm
        
        ||φ||² = ∫ φ² dV
        """
        if self.dim == 1:
            return np.sum(phi**2) * self.dx
        elif self.dim == 2:
            return np.sum(phi**2) * self.dx**2
        else:
            return np.sum(phi**2) * self.dx**3
    
    def compute_gradient_norm(self, phi):
        """
        Compute gradient norm
        
        ||∇φ||² = ∫ |∇φ|² dV
        """
        grad_phi = self.solver.compute_gradient_magnitude(phi)
        
        if self.dim == 1:
            return np.sum(grad_phi**2) * self.dx
        elif self.dim == 2:
            return np.sum(grad_phi**2) * self.dx**2
        else:
            return np.sum(grad_phi**2) * self.dx**3
    
    def compute_entropy(self, phi):
        """
        Compute entropy-like quantity
        
        S = -∫ φ·log|φ| dV
        """
        # Avoid log(0)
        phi_safe = np.where(np.abs(phi) > 1e-10, phi, 1e-10)
        entropy = -phi_safe * np.log(np.abs(phi_safe))
        
        if self.dim == 1:
            return np.sum(entropy) * self.dx
        elif self.dim == 2:
            return np.sum(entropy) * self.dx**2
        else:
            return np.sum(entropy) * self.dx**3
    
    def compute_custom_quantity(self, phi, func):
        """
        Compute custom conserved quantity
        
        Q = ∫ func(φ, ∇φ) dV
        
        Parameters:
        -----------
        phi : ndarray
            Field configuration
        func : callable
            Function of (phi, grad_phi) returning scalar field
        """
        grad_phi = self.solver.compute_gradient_magnitude(phi)
        quantity = func(phi, grad_phi)
        
        if self.dim == 1:
            return np.sum(quantity) * self.dx
        elif self.dim == 2:
            return np.sum(quantity) * self.dx**2
        else:
            return np.sum(quantity) * self.dx**3
    
    def test_conservation(self, quantity_func, n_steps=1000, 
                         save_interval=10, tolerance=0.01):
        """
        Test if a quantity is conserved
        
        Parameters:
        -----------
        quantity_func : callable
            Function that computes quantity from phi
        n_steps : int
            Number of time steps
        save_interval : int
            How often to measure
        tolerance : float
            Relative change threshold for conservation
            
        Returns:
        --------
        is_conserved : bool
            True if quantity conserved within tolerance
        values : ndarray
            Time series of quantity values
        relative_change : float
            Max relative change over evolution
        """
        # Run simulation
        history = self.solver.run(n_steps, save_interval=save_interval)
        
        # Compute quantity at each time
        values = np.array([quantity_func(phi) for phi in history])
        
        # Measure conservation
        initial = values[0]
        if np.abs(initial) > 1e-10:
            relative_changes = np.abs((values - initial) / initial)
            max_relative_change = np.max(relative_changes)
        else:
            # If initial value is zero, use absolute change
            max_relative_change = np.max(np.abs(values - initial))
        
        is_conserved = max_relative_change < tolerance
        
        return is_conserved, values, max_relative_change
    
    def test_all_standard_quantities(self, n_steps=1000, save_interval=10):
        """
        Test all standard candidate conserved quantities
        
        Returns:
        --------
        results : dict
            Dictionary with conservation test results
        """
        print("Testing standard conserved quantities...")
        print()
        
        results = {}
        
        # Test mass
        print("Testing total mass...")
        is_conserved, values, change = self.test_conservation(
            self.compute_total_mass, n_steps, save_interval
        )
        results['mass'] = {
            'conserved': is_conserved,
            'values': values,
            'max_change': change
        }
        print(f"  Mass: {'CONSERVED' if is_conserved else 'NOT conserved'} "
              f"(max change: {change:.6f})")
        
        # Test energy
        print("Testing total energy...")
        is_conserved, values, change = self.test_conservation(
            self.compute_total_energy, n_steps, save_interval
        )
        results['energy'] = {
            'conserved': is_conserved,
            'values': values,
            'max_change': change
        }
        print(f"  Energy: {'CONSERVED' if is_conserved else 'NOT conserved'} "
              f"(max change: {change:.6f})")
        
        # Test momentum
        print("Testing momentum...")
        is_conserved, values, change = self.test_conservation(
            self.compute_momentum, n_steps, save_interval
        )
        results['momentum'] = {
            'conserved': is_conserved,
            'values': values,
            'max_change': change
        }
        print(f"  Momentum: {'CONSERVED' if is_conserved else 'NOT conserved'} "
              f"(max change: {change:.6f})")
        
        # Test L² norm
        print("Testing L² norm...")
        is_conserved, values, change = self.test_conservation(
            self.compute_l2_norm, n_steps, save_interval
        )
        results['l2_norm'] = {
            'conserved': is_conserved,
            'values': values,
            'max_change': change
        }
        print(f"  L² norm: {'CONSERVED' if is_conserved else 'NOT conserved'} "
              f"(max change: {change:.6f})")
        
        # Test gradient norm
        print("Testing gradient norm...")
        is_conserved, values, change = self.test_conservation(
            self.compute_gradient_norm, n_steps, save_interval
        )
        results['gradient_norm'] = {
            'conserved': is_conserved,
            'values': values,
            'max_change': change
        }
        print(f"  Gradient norm: {'CONSERVED' if is_conserved else 'NOT conserved'} "
              f"(max change: {change:.6f})")
        
        print()
        return results
    
    def plot_conservation_test(self, results, save_path=None):
        """
        Plot time evolution of conserved quantities
        
        Parameters:
        -----------
        results : dict
            Results from test_all_standard_quantities
        save_path : str, optional
            Path to save figure
        """
        fig, axes = plt.subplots(3, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        quantities = ['mass', 'energy', 'momentum', 'l2_norm', 'gradient_norm']
        titles = ['Total Mass', 'Total Energy', 'Momentum', 
                 'L² Norm', 'Gradient Norm']
        
        for i, (qty, title) in enumerate(zip(quantities, titles)):
            if qty in results:
                values = results[qty]['values']
                conserved = results[qty]['conserved']
                change = results[qty]['max_change']
                
                # Normalize to initial value
                if np.abs(values[0]) > 1e-10:
                    normalized = values / values[0]
                else:
                    normalized = values
                
                axes[i].plot(normalized, 'b-', linewidth=2)
                axes[i].axhline(1.0, color='r', linestyle='--', alpha=0.5)
                axes[i].set_xlabel('Time step')
                axes[i].set_ylabel('Normalized value')
                axes[i].set_title(f'{title}\n{"CONSERVED" if conserved else "NOT conserved"} '
                                f'(Δ={change:.4f})')
                axes[i].grid(True, alpha=0.3)
        
        # Remove unused subplot
        fig.delaxes(axes[5])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight', dpi=150)
            print(f"Saved to {save_path}")
        
        plt.show()
    
    def search_for_novel_conservation_laws(self, n_candidates=10):
        """
        Search for non-obvious conserved quantities
        
        Tests combinations of φ, ∇φ, and their powers
        
        Parameters:
        -----------
        n_candidates : int
            Number of candidate forms to test
            
        Returns:
        --------
        novel_laws : list
            List of (description, func, max_change) for conserved quantities
        """
        print("Searching for novel conservation laws...")
        print()
        
        novel_laws = []
        
        # Candidate forms
        candidates = [
            ("φ³", lambda phi, grad: phi**3),
            ("φ⁴", lambda phi, grad: phi**4),
            ("φ·|∇φ|²", lambda phi, grad: phi * grad**2),
            ("φ²·|∇φ|", lambda phi, grad: phi**2 * grad),
            ("|∇φ|³", lambda phi, grad: grad**3),
            ("φ²·e^(-|∇φ|)", lambda phi, grad: phi**2 * np.exp(-grad)),
            ("φ·tanh(φ)", lambda phi, grad: phi * np.tanh(phi)),
            ("log(cosh(φ))", lambda phi, grad: np.log(np.cosh(phi))),
            ("φ·e^(-φ²)", lambda phi, grad: phi * np.exp(-phi**2)),
            ("(φ² + |∇φ|²)", lambda phi, grad: phi**2 + grad**2),
        ]
        
        for desc, func in candidates[:n_candidates]:
            print(f"Testing: {desc}")
            
            quantity_func = lambda phi: self.compute_custom_quantity(phi, func)
            
            is_conserved, values, change = self.test_conservation(
                quantity_func, n_steps=500, save_interval=10, tolerance=0.05
            )
            
            if is_conserved:
                print(f"  ✓ CONSERVED! (max change: {change:.6f})")
                novel_laws.append((desc, func, change))
            else:
                print(f"  ✗ Not conserved (max change: {change:.6f})")
        
        print()
        print(f"Found {len(novel_laws)} novel conservation laws")
        
        return novel_laws


if __name__ == "__main__":
    print("Testing ConservationAnalyzer...")
    print()
    
    # Create solver
    solver = AdvancedPhiSolver(
        domain_size=(64,),
        dx=1.0,
        alpha=1.0,
        beta=0.5,
        gamma=0.1,
        dim=1
    )
    
    # Set initial condition
    solver.set_initial_condition('random', amplitude=0.1)
    
    # Create analyzer
    analyzer = ConservationAnalyzer(solver)
    
    # Test standard quantities
    results = analyzer.test_all_standard_quantities(n_steps=500, save_interval=10)
    
    # Plot results
    analyzer.plot_conservation_test(results, save_path='conservation_test.png')
    
    # Search for novel laws
    novel_laws = analyzer.search_for_novel_conservation_laws(n_candidates=10)
    
    print()
    print("✓ ConservationAnalyzer test complete!")
