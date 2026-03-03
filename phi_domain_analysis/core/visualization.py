"""
Visualization and Plotting Tools for φ-Equation

Comprehensive visualization suite for exploring φ-field dynamics,
including toroidal topology and oscillatory time structure.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import hsv_to_rgb
from mpl_toolkits.mplot3d import Axes3D


class PhiVisualizer:
    """Comprehensive visualization tools for φ-equation analysis"""
    
    def __init__(self, figsize=(12, 8), dpi=100):
        self.figsize = figsize
        self.dpi = dpi
        plt.rcParams['figure.dpi'] = dpi
        plt.rcParams['savefig.dpi'] = dpi

    
    def plot_field_evolution(self, history, dx=1.0, dt=1.0, save_path=None, show=True):
        """Plot spatiotemporal evolution of φ-field"""
        fig, axes = plt.subplots(2, 3, figsize=self.figsize)
        
        n_times = len(history)
        time_indices = [0, n_times//4, n_times//2, 3*n_times//4, n_times-1]
        times = [i * dt for i in time_indices]
        
        for idx, (t_idx, t) in enumerate(zip(time_indices, times)):
            ax = axes.flat[idx]
            
            if history[t_idx].ndim == 1:
                x = np.arange(len(history[t_idx])) * dx
                ax.plot(x, history[t_idx], 'b-', linewidth=2)
                ax.set_xlabel('x')
                ax.set_ylabel('φ')
                ax.grid(True, alpha=0.3)
            else:
                im = ax.imshow(history[t_idx].T, origin='lower',
                              extent=[0, history[t_idx].shape[0]*dx,
                                     0, history[t_idx].shape[1]*dx],
                              cmap='RdBu_r', aspect='auto')
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                plt.colorbar(im, ax=ax, label='φ')
            
            ax.set_title(f't = {t:.2f}')
        
        axes.flat[-1].axis('off')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()

    
    def plot_phase_encoded(self, phi, dx=1.0, save_path=None, show=True):
        """
        Plot field with phase-encoded colors (reveals toroidal structure)
        
        Uses HSV: Hue=phase, Saturation=amplitude, Value=gradient
        """
        if phi.ndim != 2:
            raise ValueError("Phase encoding only for 2D fields")
        
        # Normalize φ to [0, 1] for hue
        phi_norm = (phi - phi.min()) / (phi.max() - phi.min() + 1e-10)
        hue = phi_norm
        
        # Gradient magnitude
        gx = np.gradient(phi, axis=0) / dx
        gy = np.gradient(phi, axis=1) / dx
        grad_mag = np.sqrt(gx**2 + gy**2)
        
        # Saturation from amplitude
        saturation = np.abs(phi) / (np.abs(phi).max() + 1e-10)
        
        # Value from inverse gradient (bright where smooth)
        value = np.exp(-grad_mag / (grad_mag.max() + 1e-10))
        
        # Create HSV image
        hsv = np.stack([hue, saturation, value], axis=-1)
        rgb = hsv_to_rgb(hsv)
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Phase-encoded
        axes[0].imshow(rgb, origin='lower',
                      extent=[0, phi.shape[0]*dx, 0, phi.shape[1]*dx])
        axes[0].set_title('Phase-Encoded φ-Field')
        axes[0].set_xlabel('x')
        axes[0].set_ylabel('y')
        
        # Raw field
        im1 = axes[1].imshow(phi.T, origin='lower',
                            extent=[0, phi.shape[0]*dx, 0, phi.shape[1]*dx],
                            cmap='RdBu_r')
        axes[1].set_title('φ-Field')
        plt.colorbar(im1, ax=axes[1], label='φ')
        
        # Gradient
        im2 = axes[2].imshow(grad_mag.T, origin='lower',
                            extent=[0, phi.shape[0]*dx, 0, phi.shape[1]*dx],
                            cmap='viridis')
        axes[2].set_title('|∇φ|')
        plt.colorbar(im2, ax=axes[2], label='|∇φ|')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()

    
    def plot_power_spectrum(self, phi, dx=1.0, save_path=None, show=True):
        """Plot power spectrum (reveals oscillatory structure)"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        if phi.ndim == 1:
            fft = np.fft.fft(phi)
            power = np.abs(fft)**2
            freqs = np.fft.fftfreq(len(phi), dx)
            
            pos_mask = freqs > 0
            axes[0].semilogy(freqs[pos_mask], power[pos_mask], 'b-')
            axes[0].set_xlabel('Frequency')
            axes[0].set_ylabel('Power')
            axes[0].set_title('Power Spectrum')
            axes[0].grid(True, alpha=0.3)
            
            wavelengths = 1 / freqs[pos_mask]
            axes[1].loglog(wavelengths, power[pos_mask], 'b-')
            axes[1].set_xlabel('Wavelength')
            axes[1].set_ylabel('Power')
            axes[1].set_title('Power vs Wavelength')
            axes[1].grid(True, alpha=0.3)
        
        else:
            fft = np.fft.fft2(phi)
            power = np.abs(fft)**2
            power_shifted = np.fft.fftshift(power)
            
            im = axes[0].imshow(np.log10(power_shifted + 1), origin='lower', cmap='viridis')
            axes[0].set_title('2D Power Spectrum (log)')
            plt.colorbar(im, ax=axes[0], label='log₁₀(Power)')
            
            # Radial average
            kx = np.fft.fftfreq(phi.shape[0], dx)
            ky = np.fft.fftfreq(phi.shape[1], dx)
            KX, KY = np.meshgrid(kx, ky, indexing='ij')
            k_mag = np.sqrt(KX**2 + KY**2)
            
            k_bins = np.linspace(0, k_mag.max(), 50)
            power_radial = np.zeros(len(k_bins) - 1)
            
            for i in range(len(k_bins) - 1):
                mask = (k_mag >= k_bins[i]) & (k_mag < k_bins[i+1])
                if np.any(mask):
                    power_radial[i] = np.mean(power[mask])
            
            k_centers = (k_bins[:-1] + k_bins[1:]) / 2
            axes[1].semilogy(k_centers, power_radial, 'b-')
            axes[1].set_xlabel('|k|')
            axes[1].set_ylabel('Power')
            axes[1].set_title('Radial Power Spectrum')
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_comparison(self, fields, labels, dx=1.0, save_path=None, show=True):
        """Compare multiple field configurations side-by-side"""
        n_fields = len(fields)
        fig, axes = plt.subplots(1, n_fields, figsize=(5*n_fields, 4))
        
        if n_fields == 1:
            axes = [axes]
        
        vmin = min(f.min() for f in fields)
        vmax = max(f.max() for f in fields)
        
        for ax, field, label in zip(axes, fields, labels):
            if field.ndim == 1:
                x = np.arange(len(field)) * dx
                ax.plot(x, field, 'b-', linewidth=2)
                ax.set_xlabel('x')
                ax.set_ylabel('φ')
                ax.grid(True, alpha=0.3)
            else:
                im = ax.imshow(field.T, origin='lower',
                              extent=[0, field.shape[0]*dx, 0, field.shape[1]*dx],
                              cmap='RdBu_r', aspect='auto', vmin=vmin, vmax=vmax)
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                plt.colorbar(im, ax=ax, label='φ')
            
            ax.set_title(label)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        if show:
            plt.show()
        else:
            plt.close()


if __name__ == "__main__":
    print("Testing PhiVisualizer...")
    
    x = np.linspace(0, 20*np.pi, 128)
    y = np.linspace(0, 20*np.pi, 128)
    X, Y = np.meshgrid(x, y)
    
    phi = np.sin(X) * np.cos(Y) + 0.5*np.sin(2*X) * np.cos(2*Y)
    phi += 0.1 * np.random.randn(*phi.shape)
    
    history = [phi * (1 + 0.1*t) for t in range(10)]
    history = np.array(history)
    
    viz = PhiVisualizer()
    
    print("Testing visualizations...")
    viz.plot_field_evolution(history, dx=x[1]-x[0], show=False)
    viz.plot_phase_encoded(phi, dx=x[1]-x[0], show=False)
    viz.plot_power_spectrum(phi, dx=x[1]-x[0], show=False)
    
    print("✓ PhiVisualizer test complete!")
