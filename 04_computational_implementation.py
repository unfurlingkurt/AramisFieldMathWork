"""
Computational Implementation and Numerical Experiments
for the φ-Equation Investigation

φ_{t+1} = φ_t + α(Δφ_t - γ|∇φ_t|²) + β·tanh(φ_t)·e^(-|∇φ_t|)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.ndimage import laplace, sobel
import warnings
warnings.filterwarnings('ignore')


class PhiEquationSolver:
    """
    Numerical solver for the φ-equation in 1D and 2D
    """
    
    def __init__(self, domain_size, dx, alpha, gamma, beta, dim=2):
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
        gamma : float
            Gradient penalty coefficient
        beta : float
            Reaction strength
        dim : int
            Dimension (1 or 2)
        """
        self.domain_size = domain_size
        self.dx = dx
        self.alpha = alpha
        self.gamma = gamma
        self.beta = beta
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
            gx = sobel(phi, axis=0, mode='wrap') / self.dx
            gy = sobel(phi, axis=1, mode='wrap') / self.dx
            return np.sqrt(gx**2 + gy**2)
    
    def step(self):
        """Perform one time step"""
        # Compute spatial derivatives
        lap_phi = self.compute_laplacian(self.phi)
        grad_mag = self.compute_gradient_magnitude(self.phi)
        
        # Compute terms
        diffusion_term = self.alpha * (lap_phi - self.gamma * grad_mag**2)
        reaction_term = self.beta * np.tanh(self.phi) * np.exp(-grad_mag)
        
        # Update
        self.phi = self.phi + diffusion_term + reaction_term
        self.time += 1
        
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


def analyze_stability(alpha_range, beta_range, gamma, domain_size=(64, 64), dx=1.0, n_steps=500):
    """
    Analyze stability across parameter space
    """
    results = np.zeros((len(alpha_range), len(beta_range)))
    
    for i, alpha in enumerate(alpha_range):
        for j, beta in enumerate(beta_range):
            solver = PhiEquationSolver(domain_size, dx, alpha, gamma, beta, dim=2)
            solver.set_initial_condition('random', amplitude=0.1)
            
            # Run simulation
            history = solver.run(n_steps, save_interval=50)
            
            # Measure final variance as indicator of pattern formation
            results[i, j] = np.var(history[-1])
    
    return results


def measure_pattern_wavelength(phi, dx):
    """
    Measure dominant wavelength using FFT
    """
    # 2D FFT
    fft = np.fft.fft2(phi)
    power = np.abs(fft)**2
    
    # Get frequencies
    kx = np.fft.fftfreq(phi.shape[0], dx)
    ky = np.fft.fftfreq(phi.shape[1], dx)
    
    # Find peak (excluding DC component)
    power[0, 0] = 0
    peak_idx = np.unravel_index(np.argmax(power), power.shape)
    
    k_peak = np.sqrt(kx[peak_idx[0]]**2 + ky[peak_idx[1]]**2)
    wavelength = 2*np.pi / k_peak if k_peak > 0 else np.inf
    
    return wavelength


def analyze_edge_width(phi, dx):
    """
    Measure characteristic edge width
    """
    grad_mag = np.gradient(phi)[0]  # Just use one direction for simplicity
    
    # Find regions with high gradients
    threshold = np.percentile(np.abs(grad_mag), 90)
    edge_regions = np.abs(grad_mag) > threshold
    
    if np.sum(edge_regions) == 0:
        return 0
    
    # Measure width of edge regions
    # Simple estimate: count connected edge pixels
    edge_widths = []
    in_edge = False
    width = 0
    
    for val in edge_regions.flatten():
        if val:
            width += 1
            in_edge = True
        else:
            if in_edge:
                edge_widths.append(width)
                width = 0
                in_edge = False
    
    return np.mean(edge_widths) * dx if edge_widths else 0


def compute_energy(phi, alpha, gamma, beta, dx):
    """
    Compute approximate energy functional
    """
    grad_mag = np.gradient(phi)[0] if phi.ndim == 1 else np.sqrt(np.gradient(phi)[0]**2 + np.gradient(phi)[1]**2)
    
    # Energy components
    E_grad = 0.5 * alpha * np.sum(grad_mag**2) * dx**phi.ndim
    E_quartic = -0.25 * alpha * gamma * np.sum(grad_mag**4) * dx**phi.ndim
    E_reaction = -beta * np.sum(np.log(np.cosh(phi)) * np.exp(-grad_mag)) * dx**phi.ndim
    
    return E_grad + E_quartic + E_reaction


def find_traveling_wave_speed(solver, n_steps=1000):
    """
    Estimate traveling wave speed by tracking peak position
    """
    positions = []
    
    for i in range(n_steps):
        solver.step()
        
        if i % 10 == 0:
            # Find peak position
            if solver.dim == 1:
                peak_pos = np.argmax(solver.phi) * solver.dx
            else:
                peak_idx = np.unravel_index(np.argmax(solver.phi), solver.phi.shape)
                peak_pos = peak_idx[0] * solver.dx
            
            positions.append(peak_pos)
    
    # Linear fit to get speed
    times = np.arange(len(positions)) * 10
    if len(positions) > 2:
        speed = np.polyfit(times, positions, 1)[0]
    else:
        speed = 0
    
    return speed, positions


def experiment_1_pattern_formation():
    """
    Experiment 1: Pattern formation from random initial conditions
    """
    print("Experiment 1: Pattern Formation")
    print("-" * 50)
    
    # Parameters
    domain_size = (128, 128)
    dx = 1.0
    alpha = 1.0
    gamma = 0.1
    beta_values = [0.5, 1.0, 2.0, 5.0]
    n_steps = 500
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    for idx, beta in enumerate(beta_values):
        solver = PhiEquationSolver(domain_size, dx, alpha, gamma, beta, dim=2)
        solver.set_initial_condition('random', amplitude=0.1)
        
        # Initial condition
        axes[0, idx].imshow(solver.phi, cmap='RdBu_r', vmin=-2, vmax=2)
        axes[0, idx].set_title(f'β={beta}, t=0')
        axes[0, idx].axis('off')
        
        # Run simulation
        history = solver.run(n_steps, save_interval=100)
        
        # Final state
        axes[1, idx].imshow(history[-1], cmap='RdBu_r', vmin=-2, vmax=2)
        axes[1, idx].set_title(f'β={beta}, t={n_steps}')
        axes[1, idx].axis('off')
        
        # Measure wavelength
        wavelength = measure_pattern_wavelength(history[-1], dx)
        print(f"β={beta}: wavelength={wavelength:.2f}, variance={np.var(history[-1]):.4f}")
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp1_pattern_formation.png', dpi=150)
    print("Saved: exp1_pattern_formation.png\n")


def experiment_2_edge_preservation():
    """
    Experiment 2: Edge preservation with varying γ
    """
    print("Experiment 2: Edge Preservation")
    print("-" * 50)
    
    # Parameters
    domain_size = (128, 128)
    dx = 1.0
    alpha = 1.0
    beta = 2.0
    gamma_values = [0.0, 0.1, 0.5, 1.0]
    n_steps = 200
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    
    for idx, gamma in enumerate(gamma_values):
        solver = PhiEquationSolver(domain_size, dx, alpha, gamma, beta, dim=2)
        
        # Step initial condition
        solver.set_initial_condition('step', amplitude=1.0)
        
        # Add noise
        solver.phi += 0.1 * np.random.randn(*domain_size)
        
        # Initial condition
        axes[0, idx].imshow(solver.phi, cmap='RdBu_r', vmin=-2, vmax=2)
        axes[0, idx].set_title(f'γ={gamma}, t=0')
        axes[0, idx].axis('off')
        
        # Run simulation
        history = solver.run(n_steps, save_interval=50)
        
        # Final state
        axes[1, idx].imshow(history[-1], cmap='RdBu_r', vmin=-2, vmax=2)
        axes[1, idx].set_title(f'γ={gamma}, t={n_steps}')
        axes[1, idx].axis('off')
        
        # Measure edge width
        edge_width = analyze_edge_width(history[-1], dx)
        print(f"γ={gamma}: edge_width={edge_width:.2f}")
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp2_edge_preservation.png', dpi=150)
    print("Saved: exp2_edge_preservation.png\n")


def experiment_3_traveling_waves():
    """
    Experiment 3: Traveling wave solutions (1D)
    """
    print("Experiment 3: Traveling Waves")
    print("-" * 50)
    
    # Parameters
    domain_size = (256,)
    dx = 1.0
    alpha = 1.0
    gamma = 0.1
    beta = 2.0
    n_steps = 500
    
    solver = PhiEquationSolver(domain_size, dx, alpha, gamma, beta, dim=1)
    
    # Localized initial condition
    solver.set_initial_condition('gaussian', amplitude=2.0, center=64, width=10)
    
    # Run and save history
    history = solver.run(n_steps, save_interval=10)
    
    # Plot space-time diagram
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Space-time plot
    im = ax1.imshow(history.T, aspect='auto', cmap='RdBu_r', 
                    extent=[0, n_steps, 0, domain_size[0]*dx],
                    vmin=-2, vmax=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Space')
    ax1.set_title('Space-Time Diagram')
    plt.colorbar(im, ax=ax1)
    
    # Snapshots at different times
    times = [0, 100, 200, 300, 400, 500]
    for t in times:
        idx = t // 10
        if idx < len(history):
            ax2.plot(solver.x, history[idx], label=f't={t}', alpha=0.7)
    
    ax2.set_xlabel('Space')
    ax2.set_ylabel('φ')
    ax2.set_title('Wave Profiles')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp3_traveling_waves.png', dpi=150)
    print("Saved: exp3_traveling_waves.png\n")


def experiment_4_parameter_space():
    """
    Experiment 4: Parameter space exploration
    """
    print("Experiment 4: Parameter Space")
    print("-" * 50)
    
    # Parameter ranges
    alpha_range = np.linspace(0.1, 2.0, 15)
    beta_range = np.linspace(0.1, 5.0, 15)
    gamma = 0.1
    
    print("Computing stability diagram (this may take a while)...")
    results = analyze_stability(alpha_range, beta_range, gamma, 
                                domain_size=(64, 64), dx=1.0, n_steps=300)
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(results.T, aspect='auto', origin='lower',
                   extent=[alpha_range[0], alpha_range[-1], 
                          beta_range[0], beta_range[-1]],
                   cmap='viridis')
    ax.set_xlabel('α (diffusion)')
    ax.set_ylabel('β (reaction)')
    ax.set_title('Pattern Formation Intensity (variance of final state)')
    plt.colorbar(im, ax=ax, label='Variance')
    
    # Add theoretical prediction line
    # Turing instability: β > α·k² approximately
    k_typical = 2*np.pi / 64  # Typical wavenumber
    beta_theory = alpha_range * k_typical**2
    ax.plot(alpha_range, beta_theory, 'r--', linewidth=2, label='Theoretical threshold')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp4_parameter_space.png', dpi=150)
    print("Saved: exp4_parameter_space.png\n")


def experiment_5_gradient_modulation():
    """
    Experiment 5: Effect of gradient modulation on reaction
    """
    print("Experiment 5: Gradient Modulation")
    print("-" * 50)
    
    # Create a field with varying gradients
    domain_size = (128, 128)
    dx = 1.0
    
    # Create test field
    x = np.arange(domain_size[0]) * dx
    y = np.arange(domain_size[1]) * dx
    X, Y = np.meshgrid(x, y, indexing='ij')
    
    # Field with different gradient regions
    phi_test = np.zeros(domain_size)
    phi_test[:40, :] = 1.0  # Flat region
    phi_test[40:60, :] = np.linspace(1, -1, 20)[:, np.newaxis]  # Sharp gradient
    phi_test[60:, :] = -1.0  # Flat region
    
    # Compute gradient magnitude
    gx = np.gradient(phi_test, axis=0) / dx
    gy = np.gradient(phi_test, axis=1) / dx
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    # Compute reaction term
    beta = 2.0
    reaction = beta * np.tanh(phi_test) * np.exp(-grad_mag)
    
    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    im0 = axes[0].imshow(phi_test, cmap='RdBu_r', vmin=-1.5, vmax=1.5)
    axes[0].set_title('Field φ')
    axes[0].axis('off')
    plt.colorbar(im0, ax=axes[0])
    
    im1 = axes[1].imshow(grad_mag, cmap='hot')
    axes[1].set_title('Gradient Magnitude |∇φ|')
    axes[1].axis('off')
    plt.colorbar(im1, ax=axes[1])
    
    im2 = axes[2].imshow(reaction, cmap='RdBu_r')
    axes[2].set_title('Reaction Term β·tanh(φ)·exp(-|∇φ|)')
    axes[2].axis('off')
    plt.colorbar(im2, ax=axes[2])
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp5_gradient_modulation.png', dpi=150)
    print("Saved: exp5_gradient_modulation.png\n")
    
    # Quantitative analysis
    print("Quantitative Analysis:")
    print(f"Flat region (top): mean reaction = {np.mean(reaction[:40, :]):.4f}")
    print(f"Gradient region: mean reaction = {np.mean(reaction[40:60, :]):.4f}")
    print(f"Flat region (bottom): mean reaction = {np.mean(reaction[60:, :]):.4f}")
    print(f"Suppression factor: {np.mean(reaction[:40, :]) / np.mean(reaction[40:60, :]):.2f}x\n")


def experiment_6_energy_evolution():
    """
    Experiment 6: Energy evolution over time
    """
    print("Experiment 6: Energy Evolution")
    print("-" * 50)
    
    # Parameters
    domain_size = (64,)
    dx = 1.0
    alpha = 1.0
    gamma = 0.1
    beta = 2.0
    n_steps = 1000
    
    solver = PhiEquationSolver(domain_size, dx, alpha, gamma, beta, dim=1)
    solver.set_initial_condition('random', amplitude=0.5)
    
    # Track energy and other quantities
    energies = []
    variances = []
    max_gradients = []
    
    for i in range(n_steps):
        solver.step()
        
        if i % 10 == 0:
            energy = compute_energy(solver.phi, alpha, gamma, beta, dx)
            energies.append(energy)
            variances.append(np.var(solver.phi))
            
            grad_mag = solver.compute_gradient_magnitude(solver.phi)
            max_gradients.append(np.max(grad_mag))
    
    # Plot
    fig, axes = plt.subplots(3, 1, figsize=(10, 10))
    times = np.arange(len(energies)) * 10
    
    axes[0].plot(times, energies)
    axes[0].set_ylabel('Energy')
    axes[0].set_title('Energy Evolution')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(times, variances)
    axes[1].set_ylabel('Variance')
    axes[1].set_title('Field Variance')
    axes[1].grid(True, alpha=0.3)
    
    axes[2].plot(times, max_gradients)
    axes[2].set_xlabel('Time')
    axes[2].set_ylabel('Max |∇φ|')
    axes[2].set_title('Maximum Gradient')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('phi_equation_investigation/exp6_energy_evolution.png', dpi=150)
    print("Saved: exp6_energy_evolution.png\n")


if __name__ == "__main__":
    print("=" * 60)
    print("φ-EQUATION COMPUTATIONAL INVESTIGATION")
    print("=" * 60)
    print()
    
    # Run all experiments
    experiment_1_pattern_formation()
    experiment_2_edge_preservation()
    experiment_3_traveling_waves()
    experiment_4_parameter_space()
    experiment_5_gradient_modulation()
    experiment_6_energy_evolution()
    
    print("=" * 60)
    print("All experiments completed!")
    print("=" * 60)
