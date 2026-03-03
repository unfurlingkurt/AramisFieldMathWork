"""
Parameter Fitting Engine for φ-Equation

Extracts α, β, γ from spatiotemporal data using non-linear optimization.

CRITICAL: This equation is entirely non-linear. No linear approximations.
All dynamics computed from deltas against neutral state.
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from scipy.ndimage import laplace, sobel
import warnings
warnings.filterwarnings('ignore')


class ParameterFitter:
    """
    Extract α, β, γ from observed spatiotemporal dynamics
    
    Uses non-linear optimization to fit the fully non-linear φ-equation
    to observed data. No linear approximations are made.
    """
    
    def __init__(self, data, dx, dt=1.0, method='nonlinear_least_squares'):
        """
        Initialize fitter
        
        Parameters:
        -----------
        data : array
            Spatiotemporal data (time, space) or (time, x, y)
        dx : float
            Spatial step size
        dt : float
            Temporal step size
        method : str
            Fitting method: 'nonlinear_least_squares', 'maximum_likelihood', 
            'differential_evolution', 'bayesian'
        """
        self.data = data
        self.dx = dx
        self.dt = dt
        self.method = method
        self.dim = len(data.shape) - 1  # Subtract time dimension
        
        # Fitted parameters
        self.alpha = None
        self.beta = None
        self.gamma = None
        self.confidence_intervals = None
        
    def preprocess_data(self, denoise=False, normalize=False):
        """
        Prepare data for fitting
        
        Parameters:
        -----------
        denoise : bool
            Apply gentle denoising (non-linear)
        normalize : bool
            Normalize to zero mean (preserves non-linear structure)
        """
        processed = self.data.copy()
        
        if normalize:
            # Center around zero (neutral state)
            # This preserves all non-linear dynamics
            processed = processed - np.mean(processed)
        
        if denoise:
            # Apply non-linear median filter (preserves edges)
            from scipy.ndimage import median_filter
            for t in range(len(processed)):
                processed[t] = median_filter(processed[t], size=3)
        
        self.data = processed
        return processed
    
    def compute_spatial_derivatives(self, phi):
        """
        Compute Laplacian and gradient magnitude
        
        These are non-linear operators - no approximations
        """
        if self.dim == 1:
            # Laplacian
            lap = np.zeros_like(phi)
            lap[1:-1] = (phi[2:] - 2*phi[1:-1] + phi[:-2]) / self.dx**2
            lap[0] = (phi[1] - 2*phi[0] + phi[-1]) / self.dx**2
            lap[-1] = (phi[0] - 2*phi[-1] + phi[-2]) / self.dx**2
            
            # Gradient magnitude
            grad = np.zeros_like(phi)
            grad[1:-1] = (phi[2:] - phi[:-2]) / (2*self.dx)
            grad[0] = (phi[1] - phi[-1]) / (2*self.dx)
            grad[-1] = (phi[0] - phi[-2]) / (2*self.dx)
            grad_mag = np.abs(grad)
            
        else:
            # 2D case
            lap = laplace(phi, mode='wrap') / self.dx**2
            
            gx = sobel(phi, axis=0, mode='wrap') / (2*self.dx)
            gy = sobel(phi, axis=1, mode='wrap') / (2*self.dx)
            grad_mag = np.sqrt(gx**2 + gy**2)
        
        return lap, grad_mag
    
    def compute_temporal_derivative(self, t_idx):
        """
        Compute ∂φ/∂t from data
        
        Uses central differences (non-linear, exact for discrete data)
        """
        if t_idx == 0:
            # Forward difference
            dphi_dt = (self.data[1] - self.data[0]) / self.dt
        elif t_idx == len(self.data) - 1:
            # Backward difference
            dphi_dt = (self.data[-1] - self.data[-2]) / self.dt
        else:
            # Central difference
            dphi_dt = (self.data[t_idx + 1] - self.data[t_idx - 1]) / (2*self.dt)
        
        return dphi_dt
    
    def residual(self, params, t_idx):
        """
        Compute residual for given parameters at time t_idx
        
        Residual = observed ∂φ/∂t - predicted ∂φ/∂t
        
        This is fully non-linear - no approximations
        """
        alpha, beta, gamma = params
        
        # Get field at this time
        phi = self.data[t_idx]
        
        # Compute spatial derivatives (non-linear operators)
        lap, grad_mag = self.compute_spatial_derivatives(phi)
        
        # Compute predicted time derivative from φ-equation
        # This is the full non-linear equation
        diffusion_term = alpha * (lap - gamma * grad_mag**2)
        reaction_term = beta * np.tanh(phi) * np.exp(-grad_mag)
        predicted_dphi_dt = diffusion_term + reaction_term
        
        # Compute observed time derivative
        observed_dphi_dt = self.compute_temporal_derivative(t_idx)
        
        # Residual (fully non-linear)
        residual = observed_dphi_dt - predicted_dphi_dt
        
        return residual
    
    def objective_function(self, params):
        """
        Objective function for optimization
        
        Sum of squared residuals across all time points
        Fully non-linear optimization problem
        """
        alpha, beta, gamma = params
        
        # Parameter bounds check (physical constraints)
        if alpha <= 0 or beta < 0 or gamma < 0:
            return 1e10  # Penalty for invalid parameters
        
        total_error = 0.0
        n_points = 0
        
        # Sum over time points (excluding boundaries)
        for t in range(1, len(self.data) - 1):
            res = self.residual(params, t)
            total_error += np.sum(res**2)
            n_points += res.size
        
        # Mean squared error
        mse = total_error / n_points
        
        return mse
    
    def fit_parameters(self, initial_guess=None, bounds=None):
        """
        Fit parameters using non-linear optimization
        
        Parameters:
        -----------
        initial_guess : tuple
            Initial (α, β, γ). If None, uses heuristic
        bounds : list of tuples
            Parameter bounds [(α_min, α_max), (β_min, β_max), (γ_min, γ_max)]
            
        Returns:
        --------
        params : tuple
            Fitted (α, β, γ)
        """
        # Default bounds (physical constraints)
        if bounds is None:
            bounds = [(1e-3, 10.0),   # α: diffusion
                      (0.0, 10.0),     # β: reaction
                      (0.0, 2.0)]      # γ: gradient penalty
        
        # Heuristic initial guess if not provided
        if initial_guess is None:
            # Estimate α from spatial smoothing scale
            spatial_var = np.var(np.gradient(self.data[0]))
            alpha_guess = spatial_var * self.dx**2
            
            # Estimate β from temporal variation
            temporal_var = np.var(self.data[1:] - self.data[:-1])
            beta_guess = temporal_var
            
            # Estimate γ from gradient statistics
            _, grad_mag = self.compute_spatial_derivatives(self.data[0])
            gamma_guess = 1.0 / (np.mean(grad_mag**2) + 1e-6)
            
            initial_guess = (alpha_guess, beta_guess, gamma_guess)
        
        print(f"Initial guess: α={initial_guess[0]:.4f}, β={initial_guess[1]:.4f}, γ={initial_guess[2]:.4f}")
        
        if self.method == 'nonlinear_least_squares':
            # Non-linear least squares (local optimization)
            result = minimize(
                self.objective_function,
                initial_guess,
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 1000}
            )
            
            self.alpha, self.beta, self.gamma = result.x
            success = result.success
            
        elif self.method == 'differential_evolution':
            # Global optimization (more robust, slower)
            # Handles non-linear landscape better
            result = differential_evolution(
                self.objective_function,
                bounds,
                maxiter=100,
                popsize=15,
                seed=42
            )
            
            self.alpha, self.beta, self.gamma = result.x
            success = result.success
        
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        if not success:
            print("Warning: Optimization did not converge")
        
        print(f"Fitted: α={self.alpha:.4f}, β={self.beta:.4f}, γ={self.gamma:.4f}")
        print(f"Final error: {self.objective_function((self.alpha, self.beta, self.gamma)):.6f}")
        
        return (self.alpha, self.beta, self.gamma)
    
    def validate_fit(self, test_data=None, n_steps=None):
        """
        Validate fitted parameters on test data
        
        Simulates forward using fitted parameters and compares to data
        Fully non-linear forward simulation
        
        Parameters:
        -----------
        test_data : array, optional
            Test data. If None, uses second half of training data
        n_steps : int, optional
            Number of steps to simulate. If None, uses length of test data
            
        Returns:
        --------
        error : float
            Mean squared error on test data
        predicted : array
            Predicted evolution
        """
        if test_data is None:
            # Use second half of data for testing
            split = len(self.data) // 2
            test_data = self.data[split:]
            initial_condition = self.data[split]
        else:
            initial_condition = test_data[0]
        
        if n_steps is None:
            n_steps = len(test_data) - 1
        
        # Simulate forward (fully non-linear)
        predicted = [initial_condition]
        phi = initial_condition.copy()
        
        for _ in range(n_steps):
            # Compute derivatives (non-linear)
            lap, grad_mag = self.compute_spatial_derivatives(phi)
            
            # Apply φ-equation (fully non-linear)
            diffusion = self.alpha * (lap - self.gamma * grad_mag**2)
            reaction = self.beta * np.tanh(phi) * np.exp(-grad_mag)
            
            phi = phi + (diffusion + reaction) * self.dt
            predicted.append(phi.copy())
        
        predicted = np.array(predicted)
        
        # Compute error
        min_len = min(len(predicted), len(test_data))
        error = np.mean((predicted[:min_len] - test_data[:min_len])**2)
        
        print(f"Validation MSE: {error:.6f}")
        
        return error, predicted
    
    def compute_confidence_intervals(self, n_bootstrap=100):
        """
        Estimate confidence intervals using bootstrap
        
        Resamples data (preserving temporal structure) and refits
        Non-linear bootstrap for non-linear problem
        
        Returns:
        --------
        ci : dict
            Confidence intervals for each parameter
        """
        if self.alpha is None:
            raise ValueError("Must fit parameters first")
        
        print("Computing confidence intervals via bootstrap...")
        
        bootstrap_params = []
        
        for i in range(n_bootstrap):
            # Resample time points (with replacement)
            n_times = len(self.data)
            indices = np.random.choice(n_times, size=n_times, replace=True)
            indices = np.sort(indices)  # Maintain temporal order
            
            # Create bootstrap sample
            bootstrap_data = self.data[indices]
            
            # Fit to bootstrap sample
            fitter = ParameterFitter(bootstrap_data, self.dx, self.dt, self.method)
            try:
                params = fitter.fit_parameters(
                    initial_guess=(self.alpha, self.beta, self.gamma)
                )
                bootstrap_params.append(params)
            except:
                pass  # Skip failed fits
            
            if (i + 1) % 10 == 0:
                print(f"  Bootstrap {i+1}/{n_bootstrap}")
        
        bootstrap_params = np.array(bootstrap_params)
        
        # Compute 95% confidence intervals
        ci = {
            'alpha': (np.percentile(bootstrap_params[:, 0], 2.5),
                     np.percentile(bootstrap_params[:, 0], 97.5)),
            'beta': (np.percentile(bootstrap_params[:, 1], 2.5),
                    np.percentile(bootstrap_params[:, 1], 97.5)),
            'gamma': (np.percentile(bootstrap_params[:, 2], 2.5),
                     np.percentile(bootstrap_params[:, 2], 97.5))
        }
        
        self.confidence_intervals = ci
        
        print(f"95% CI for α: [{ci['alpha'][0]:.4f}, {ci['alpha'][1]:.4f}]")
        print(f"95% CI for β: [{ci['beta'][0]:.4f}, {ci['beta'][1]:.4f}]")
        print(f"95% CI for γ: [{ci['gamma'][0]:.4f}, {ci['gamma'][1]:.4f}]")
        
        return ci
    
    def sensitivity_analysis(self, perturbation=0.1):
        """
        Test sensitivity to parameter perturbations
        
        Perturbs each parameter and measures effect on prediction
        Tests robustness of non-linear fit
        
        Returns:
        --------
        sensitivity : dict
            Sensitivity measures for each parameter
        """
        if self.alpha is None:
            raise ValueError("Must fit parameters first")
        
        print("Performing sensitivity analysis...")
        
        # Baseline prediction
        baseline_error, _ = self.validate_fit()
        
        sensitivity = {}
        
        for param_name, param_value in [('alpha', self.alpha), 
                                        ('beta', self.beta), 
                                        ('gamma', self.gamma)]:
            # Perturb parameter
            perturbed_value = param_value * (1 + perturbation)
            
            # Temporarily set perturbed value
            original = getattr(self, param_name)
            setattr(self, param_name, perturbed_value)
            
            # Compute error with perturbed parameter
            perturbed_error, _ = self.validate_fit()
            
            # Restore original
            setattr(self, param_name, original)
            
            # Sensitivity = change in error / change in parameter
            sensitivity[param_name] = (perturbed_error - baseline_error) / (perturbation * param_value)
            
            print(f"  Sensitivity to {param_name}: {sensitivity[param_name]:.6f}")
        
        return sensitivity
    
    def get_fitted_parameters(self):
        """
        Get fitted parameters with metadata
        
        Returns:
        --------
        params : dict
            Dictionary with parameters and metadata
        """
        if self.alpha is None:
            raise ValueError("Must fit parameters first")
        
        return {
            'alpha': self.alpha,
            'beta': self.beta,
            'gamma': self.gamma,
            'confidence_intervals': self.confidence_intervals,
            'method': self.method,
            'data_shape': self.data.shape,
            'dx': self.dx,
            'dt': self.dt
        }


if __name__ == "__main__":
    # Test with synthetic data
    print("Testing ParameterFitter with synthetic data...")
    
    # Generate synthetic data from known parameters
    from equation_solver import AdvancedPhiSolver
    
    true_alpha, true_beta, true_gamma = 1.0, 2.0, 0.1
    
    solver = AdvancedPhiSolver((64,), dx=1.0, alpha=true_alpha, 
                               beta=true_beta, gamma=true_gamma, dim=1)
    solver.set_initial_condition('random', amplitude=0.1)
    
    print("Generating synthetic data...")
    data = solver.run(50, save_interval=1)
    
    # Fit parameters
    print("\nFitting parameters...")
    fitter = ParameterFitter(data, dx=1.0, dt=1.0, method='nonlinear_least_squares')
    fitted_params = fitter.fit_parameters()
    
    print(f"\nTrue parameters: α={true_alpha}, β={true_beta}, γ={true_gamma}")
    print(f"Fitted parameters: α={fitted_params[0]:.4f}, β={fitted_params[1]:.4f}, γ={fitted_params[2]:.4f}")
    
    # Validate
    print("\nValidating fit...")
    error, predicted = fitter.validate_fit()
    
    print("\nParameterFitter test complete!")
