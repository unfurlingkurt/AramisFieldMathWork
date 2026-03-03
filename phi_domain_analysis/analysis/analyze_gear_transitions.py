"""
Analyze gear transitions from geared time results

Looks at:
1. How long system stays in each gear (dwell times)
2. Which gear transitions are most common
3. Whether mass changes occur at transitions
"""

import numpy as np
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

# Load results from previous run (simulated for now)
# In real analysis, we'd load from saved data

def analyze_gear_stability(gear_history):
    """
    Analyze how long system stays in each gear
    """
    print("=" * 70)
    print("GEAR STABILITY ANALYSIS")
    print("=" * 70)
    print()
    
    # Find runs of same gear
    runs = []
    current_gear = gear_history[0]
    run_length = 1
    
    for gear in gear_history[1:]:
        if gear == current_gear:
            run_length += 1
        else:
            runs.append((current_gear, run_length))
            current_gear = gear
            run_length = 1
    runs.append((current_gear, run_length))
    
    # Statistics by gear
    gear_dwells = defaultdict(list)
    for gear, length in runs:
        gear_dwells[gear].append(length)
    
    print("Dwell Time Statistics (steps in each gear before transition):")
    print()
    for gear in ['ultra_fast', 'fast', 'medium', 'slow', 'ultra_slow', 'quantum']:
        if gear in gear_dwells:
            dwells = gear_dwells[gear]
            print(f"{gear:12s}:")
            print(f"  Mean dwell: {np.mean(dwells):.2f} steps")
            print(f"  Median dwell: {np.median(dwells):.2f} steps")
            print(f"  Max dwell: {np.max(dwells)} steps")
            print(f"  Number of visits: {len(dwells)}")
            print()
    
    return runs, gear_dwells


def analyze_gear_transitions(gear_history):
    """
    Analyze which gear transitions occur
    """
    print("=" * 70)
    print("GEAR TRANSITION ANALYSIS")
    print("=" * 70)
    print()
    
    # Count transitions
    transitions = []
    for i in range(len(gear_history) - 1):
        if gear_history[i] != gear_history[i+1]:
            transitions.append((gear_history[i], gear_history[i+1]))
    
    transition_counts = Counter(transitions)
    
    print(f"Total transitions: {len(transitions)}")
    print()
    print("Most common transitions:")
    for (from_gear, to_gear), count in transition_counts.most_common(10):
        pct = 100 * count / len(transitions)
        print(f"  {from_gear:12s} → {to_gear:12s}: {count:3d} ({pct:5.1f}%)")
    print()
    
    # Build transition matrix
    gears = ['ultra_fast', 'fast', 'medium', 'slow', 'ultra_slow', 'quantum']
    gear_to_idx = {g: i for i, g in enumerate(gears)}
    
    matrix = np.zeros((6, 6))
    for (from_gear, to_gear), count in transition_counts.items():
        i = gear_to_idx[from_gear]
        j = gear_to_idx[to_gear]
        matrix[i, j] = count
    
    # Normalize to probabilities
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    prob_matrix = matrix / row_sums
    
    print("Transition Probability Matrix:")
    print("(rows = from gear, columns = to gear)")
    print()
    print("        ", end="")
    for g in gears:
        print(f"{g[:8]:>8s}", end=" ")
    print()
    for i, from_gear in enumerate(gears):
        print(f"{from_gear[:8]:8s}", end=" ")
        for j in range(6):
            if prob_matrix[i, j] > 0:
                print(f"{prob_matrix[i, j]:8.3f}", end=" ")
            else:
                print(f"{'---':>8s}", end=" ")
        print()
    print()
    
    return transitions, transition_counts, prob_matrix


def plot_gear_timeline(gear_history, masses=None):
    """
    Plot gear evolution over time with optional mass overlay
    """
    gear_to_num = {
        'ultra_fast': 6,
        'fast': 5,
        'medium': 4,
        'slow': 3,
        'ultra_slow': 2,
        'quantum': 1
    }
    gear_nums = [gear_to_num[g] for g in gear_history]
    
    if masses is not None:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=(14, 6))
    
    # Plot gears
    ax1.plot(gear_nums, 'k-', linewidth=1, alpha=0.7)
    ax1.set_ylabel('Temporal Gear')
    ax1.set_yticks([1, 2, 3, 4, 5, 6])
    ax1.set_yticklabels(['quantum', 'ultra_slow', 'slow', 'medium', 'fast', 'ultra_fast'])
    ax1.set_title('Temporal Gear Evolution')
    ax1.grid(True, alpha=0.3)
    
    # Highlight transitions
    for i in range(len(gear_history) - 1):
        if gear_history[i] != gear_history[i+1]:
            ax1.axvline(i, color='r', alpha=0.2, linewidth=0.5)
    
    if masses is not None:
        # Plot mass
        ax2.plot(masses, 'b-', linewidth=2)
        ax2.set_xlabel('Time step')
        ax2.set_ylabel('Mass')
        ax2.set_title('Mass Evolution (with gear transitions marked)')
        ax2.grid(True, alpha=0.3)
        
        # Mark transitions
        for i in range(len(gear_history) - 1):
            if gear_history[i] != gear_history[i+1]:
                ax2.axvline(i, color='r', alpha=0.2, linewidth=0.5)
    else:
        ax1.set_xlabel('Time step')
    
    plt.tight_layout()
    plt.savefig('gear_timeline_analysis.png', dpi=150, bbox_inches='tight')
    print("Saved: gear_timeline_analysis.png")
    plt.show()


# Example usage with simulated data
if __name__ == "__main__":
    print("GEAR TRANSITION ANALYSIS")
    print()
    print("This analyzes the gear history from geared time evolution")
    print("to understand stability, transitions, and patterns.")
    print()
    
    # Simulate gear history based on observed distribution
    # In real analysis, load from actual run
    np.random.seed(42)
    n_steps = 500
    
    # Generate realistic gear sequence
    gear_history = []
    current_gear = 'fast'
    
    for _ in range(n_steps):
        gear_history.append(current_gear)
        
        # Probabilistic transitions based on observed patterns
        if np.random.random() < 0.05:  # 5% chance of transition per step
            # Choose next gear based on typical patterns
            if current_gear == 'fast':
                current_gear = np.random.choice(['medium', 'slow'], p=[0.7, 0.3])
            elif current_gear == 'medium':
                current_gear = np.random.choice(['fast', 'slow', 'quantum'], p=[0.5, 0.3, 0.2])
            elif current_gear == 'slow':
                current_gear = np.random.choice(['medium', 'ultra_slow', 'quantum'], p=[0.5, 0.3, 0.2])
            elif current_gear == 'ultra_slow':
                current_gear = np.random.choice(['slow', 'quantum'], p=[0.6, 0.4])
            elif current_gear == 'quantum':
                current_gear = np.random.choice(['ultra_slow', 'slow', 'medium'], p=[0.3, 0.4, 0.3])
    
    # Analyze
    runs, gear_dwells = analyze_gear_stability(gear_history)
    transitions, trans_counts, prob_matrix = analyze_gear_transitions(gear_history)
    
    # Generate simulated mass for visualization
    masses = np.cumsum(np.random.randn(n_steps+1) * 10)
    
    # Plot
    plot_gear_timeline(gear_history, masses)
    
    print()
    print("=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print()
    print("1. Gear stability: How long does system stay in each gear?")
    print("2. Transition patterns: Which transitions are most common?")
    print("3. Forbidden transitions: Which transitions never occur?")
    print("4. Mass correlation: Do mass changes occur at transitions?")
    print()
    print("Next: Run with actual geared time data to see real patterns!")
