"""
Visualize 4H Enhancement Study Results

Create comparison plots for:
1. Main experiment (4 variants)
2. Clustering parameter sensitivity
3. Daily parameter sensitivity
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10


def plot_main_comparison():
    """Plot main experiment comparison"""
    # Manual data entry (from results)
    data = {
        'Variant': ['Baseline', 'Clustering\n(W=6,min=3)'],
        'Signals': [358, 67],
        'Sharpe': [4.03, 1.58],
        'Total_Return': [13.09, 3.59],
        'Win_Rate': [43.6, 44.8],
    }
    
    df = pd.DataFrame(data)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('4H Strategy Enhancement Study - Main Results', fontsize=16, fontweight='bold')
    
    # Plot 1: Sharpe Ratio
    ax = axes[0, 0]
    bars = ax.bar(df['Variant'], df['Sharpe'], color=['#2ecc71', '#e74c3c'])
    ax.set_ylabel('Sharpe Ratio', fontweight='bold')
    ax.set_title('Sharpe Ratio Comparison')
    ax.axhline(y=4.03, color='gray', linestyle='--', alpha=0.5, label='Baseline')
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom', fontweight='bold')
    
    # Plot 2: Total Return
    ax = axes[0, 1]
    bars = ax.bar(df['Variant'], df['Total_Return'], color=['#2ecc71', '#e74c3c'])
    ax.set_ylabel('Total Return (%)', fontweight='bold')
    ax.set_title('Total Return (11 years)')
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%',
                ha='center', va='bottom', fontweight='bold')
    
    # Plot 3: Number of Signals
    ax = axes[1, 0]
    bars = ax.bar(df['Variant'], df['Signals'], color=['#2ecc71', '#e74c3c'])
    ax.set_ylabel('Number of Signals', fontweight='bold')
    ax.set_title('Signal Count')
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')
    
    # Plot 4: Win Rate
    ax = axes[1, 1]
    bars = ax.bar(df['Variant'], df['Win_Rate'], color=['#2ecc71', '#e74c3c'])
    ax.set_ylabel('Win Rate (%)', fontweight='bold')
    ax.set_title('Win Rate')
    ax.set_ylim([0, 60])
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('results/4h_enhancement_main_comparison.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: results/4h_enhancement_main_comparison.png")
    plt.close()


def plot_clustering_sensitivity():
    """Plot clustering parameter sensitivity"""
    df = pd.read_csv('results/4h_clustering_sensitivity.csv')
    
    # Create param label
    df['params'] = df.apply(lambda x: f"W={int(x['W'])}\nmin={int(x['min_count'])}\nq={x['q_manip']:.2f}", axis=1)
    
    # Sort by Sharpe
    df = df.sort_values('sharpe_ratio', ascending=False)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Clustering Parameter Sensitivity Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Sharpe vs Params
    ax = axes[0, 0]
    colors = ['#2ecc71' if s > 3.5 else '#f39c12' if s > 2.0 else '#e74c3c' for s in df['sharpe_ratio']]
    bars = ax.bar(range(len(df)), df['sharpe_ratio'], color=colors)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['params'], rotation=0, ha='center', fontsize=8)
    ax.set_ylabel('Sharpe Ratio', fontweight='bold')
    ax.set_title('Sharpe Ratio by Parameters')
    ax.axhline(y=4.03, color='gray', linestyle='--', alpha=0.5, label='Baseline (4.03)')
    ax.legend()
    
    # Plot 2: Sharpe vs Signal Count
    ax = axes[0, 1]
    scatter = ax.scatter(df['n_trades'], df['sharpe_ratio'], 
                        s=df['win_rate']*500, c=df['sharpe_ratio'], 
                        cmap='RdYlGn', alpha=0.6, edgecolors='black')
    ax.set_xlabel('Number of Signals', fontweight='bold')
    ax.set_ylabel('Sharpe Ratio', fontweight='bold')
    ax.set_title('Sharpe vs Signal Count (bubble size = win rate)')
    ax.axhline(y=4.03, color='gray', linestyle='--', alpha=0.5)
    plt.colorbar(scatter, ax=ax, label='Sharpe')
    
    # Annotate best points
    for idx, row in df.head(3).iterrows():
        ax.annotate(f"W={int(row['W'])},min={int(row['min_count'])}", 
                   (row['n_trades'], row['sharpe_ratio']),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    # Plot 3: Win Rate vs Params
    ax = axes[1, 0]
    bars = ax.bar(range(len(df)), df['win_rate']*100, color=colors)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['params'], rotation=0, ha='center', fontsize=8)
    ax.set_ylabel('Win Rate (%)', fontweight='bold')
    ax.set_title('Win Rate by Parameters')
    ax.axhline(y=43.6, color='gray', linestyle='--', alpha=0.5, label='Baseline (43.6%)')
    ax.legend()
    
    # Plot 4: Total Return vs Params
    ax = axes[1, 1]
    bars = ax.bar(range(len(df)), df['total_return']*100, color=colors)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['params'], rotation=0, ha='center', fontsize=8)
    ax.set_ylabel('Total Return (%)', fontweight='bold')
    ax.set_title('Total Return by Parameters')
    ax.axhline(y=13.09, color='gray', linestyle='--', alpha=0.5, label='Baseline (13.09%)')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('results/4h_clustering_sensitivity.png', dpi=300, bbox_inches='tight')
    print("✅ Saved: results/4h_clustering_sensitivity.png")
    plt.close()


def main():
    print("="*80)
    print("VISUALIZING 4H ENHANCEMENT STUDY RESULTS")
    print("="*80)
    print()
    
    # Plot main comparison
    print("Creating main comparison plot...")
    plot_main_comparison()
    
    # Plot clustering sensitivity
    print("Creating clustering sensitivity plot...")
    plot_clustering_sensitivity()
    
    print()
    print("="*80)
    print("VISUALIZATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

