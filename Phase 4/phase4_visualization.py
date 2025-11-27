"""Phase 4: Visualization and Comparison"""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(r"D:\PierSight_Maritime_Study")
PHASE4_DIR = BASE_DIR / "phase4_analysis"

def load_results(constellation: str):
    """Load Phase 4 results for given constellation."""
    path = PHASE4_DIR / f"Phase4_Patrol_vs_Tracking_{constellation}.csv"
    results = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def create_comparison_charts():
    """Create Phase 4 comparison charts."""

    # Load both constellations
    results_12 = load_results("12sat")
    results_32 = load_results("32sat")

    # Parse latencies (handle None values)
    def safe_float(val):
        if val is None or val == 'None':
            return None
        try:
            return float(val)
        except:
            return None

    # Extract metrics
    metrics_12 = {}
    for row in results_12:
        key = (row['ship_id'], row['mode'])
        metrics_12[key] = {
            'detected': int(row['detected']),
            'detect_lat': safe_float(row['detect_latency_s']),
            'delivery_lat': safe_float(row['delivery_latency_s']),
        }

    metrics_32 = {}
    for row in results_32:
        key = (row['ship_id'], row['mode'])
        metrics_32[key] = {
            'detected': int(row['detected']),
            'detect_lat': safe_float(row['detect_latency_s']),
            'delivery_lat': safe_float(row['delivery_latency_s']),
        }

    # Create comparison figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Phase 4: Patrol vs Tracking Comparison (12-sat vs 32-sat)', fontsize=14, fontweight='bold')

    ships = ['Ship1', 'Ship2', 'Ship3']
    modes = ['PATROL', 'TRACKING']
    colors = {'PATROL': '#2E86AB', 'TRACKING': '#A23B72'}

    # Detection Success Rate
    ax = axes[0, 0]
    x_pos = np.arange(len(ships))
    width = 0.2

    for i, mode in enumerate(modes):
        patrol_12 = [metrics_12.get((ship, mode), {}).get('detected', 0) for ship in ships]
        patrol_32 = [metrics_32.get((ship, mode), {}).get('detected', 0) for ship in ships]
        ax.bar(x_pos - width/2 + i*width, patrol_12, width, label=f'{mode} (12-sat)', alpha=0.8)

    ax.set_ylabel('Detection Success (0=Missed, 1=Detected)')
    ax.set_title('Detection Rate by Ship and Mode')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(ships)
    ax.legend()
    ax.set_ylim([0, 1.2])
    ax.grid(axis='y', alpha=0.3)

    # Detection Latency Comparison
    ax = axes[0, 1]
    x_pos = np.arange(len(ships))
    for i, mode in enumerate(modes):
        detect_12 = [metrics_12.get((ship, mode), {}).get('detect_lat') or 0 for ship in ships]
        detect_32 = [metrics_32.get((ship, mode), {}).get('detect_lat') or 0 for ship in ships]
        ax.bar(x_pos - width/2 + i*width, detect_12, width, label=f'{mode} (12-sat)', alpha=0.8)

    ax.set_ylabel('Detection Latency (seconds)')
    ax.set_title('Detection Latency by Ship and Mode')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(ships)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Dark Ship Detection (Ship3) - Patrol vs Tracking
    ax = axes[1, 0]
    ship3_patrol_12 = metrics_12.get(('Ship3', 'PATROL'), {}).get('detected', 0)
    ship3_tracking_12 = metrics_12.get(('Ship3', 'TRACKING'), {}).get('detected', 0)
    ship3_patrol_32 = metrics_32.get(('Ship3', 'PATROL'), {}).get('detected', 0)
    ship3_tracking_32 = metrics_32.get(('Ship3', 'TRACKING'), {}).get('detected', 0)

    modes_x = ['PATROL', 'TRACKING']
    ship3_12_data = [ship3_patrol_12, ship3_tracking_12]
    ship3_32_data = [ship3_patrol_32, ship3_tracking_32]

    x = np.arange(len(modes_x))
    ax.bar(x - width/2, ship3_12_data, width, label='12-sat', color='#F18F01')
    ax.bar(x + width/2, ship3_32_data, width, label='32-sat', color='#C73E1D')

    ax.set_ylabel('Detection Success (Dark Ship)')
    ax.set_title('Ship3 (Dark Ship): Patrol vs Tracking')
    ax.set_xticks(x)
    ax.set_xticklabels(modes_x)
    ax.legend()
    ax.set_ylim([0, 1.2])
    ax.grid(axis='y', alpha=0.3)

    # Mode Advantage (Latency Reduction)
    ax = axes[1, 1]
    advantages = []
    labels = []
    for ship in ships:
        patrol_lat = metrics_12.get((ship, 'PATROL'), {}).get('detect_lat')
        tracking_lat = metrics_12.get((ship, 'TRACKING'), {}).get('detect_lat')
        if patrol_lat and tracking_lat:
            advantage = ((patrol_lat - tracking_lat) / patrol_lat * 100)
            advantages.append(advantage)
            labels.append(ship)

    colors_bars = ['#06A77D' if x > 0 else '#D62828' for x in advantages]
    ax.barh(labels, advantages, color=colors_bars)
    ax.set_xlabel('Latency Reduction (%)')
    ax.set_title('Tracking Mode Advantage over Patrol (12-sat)')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(PHASE4_DIR / 'Phase4_Patrol_vs_Tracking_Comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: Phase4_Patrol_vs_Tracking_Comparison.png")
    plt.close()

if __name__ == "__main__":
    create_comparison_charts()
