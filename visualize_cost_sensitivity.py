"""
可视化交易成本敏感性分析

Visualize Transaction Cost Sensitivity Analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """加载高成本和低成本数据"""
    high_cost_file = Path('market-manimpulation-analysis/results/symmetric_longshort_forex.csv')
    low_cost_file = Path('market-manimpulation-analysis/results/symmetric_longshort_forex_lowcost.csv')
    
    high_cost_df = pd.read_csv(high_cost_file)
    low_cost_df = pd.read_csv(low_cost_file)
    
    # Add cost label
    high_cost_df['cost_bp'] = 7.0
    low_cost_df['cost_bp'] = 0.3
    
    # Combine
    all_df = pd.concat([high_cost_df, low_cost_df], ignore_index=True)
    
    return all_df

def plot_cost_impact(df, output_file):
    """
    绘制成本影响对比图
    """
    # Filter for 30min timeframe (best performing)
    df_30min = df[df['timeframe'] == '30min'].copy()
    
    # Pivot to compare high vs low cost
    pivot = df_30min.pivot_table(
        index=['symbol', 'strategy'],
        columns='cost_bp',
        values='total_return',
        aggfunc='first'
    ).reset_index()
    
    # Sort by strategy
    pivot = pivot.sort_values(['symbol', 'strategy'])
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Total Return Comparison
    ax1 = axes[0]
    x = np.arange(len(pivot))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, pivot[7.0]*100, width, label='7bp成本', color='red', alpha=0.7)
    bars2 = ax1.bar(x + width/2, pivot[0.3]*100, width, label='0.3bp成本', color='green', alpha=0.7)
    
    ax1.set_xlabel('策略', fontsize=12)
    ax1.set_ylabel('总收益 (%)', fontsize=12)
    ax1.set_title('交易成本对收益的影响 (30min)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    labels = [f"{row['symbol']}\n{row['strategy'].split()[0]}" for _, row in pivot.iterrows()]
    ax1.set_xticklabels(labels, rotation=0, ha='center', fontsize=9)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Plot 2: Improvement
    ax2 = axes[1]
    improvement = (pivot[0.3] - pivot[7.0]) * 100
    colors = ['green' if imp > 0 else 'red' for imp in improvement]
    bars = ax2.bar(x, improvement, color=colors, alpha=0.7)
    
    ax2.set_xlabel('策略', fontsize=12)
    ax2.set_ylabel('收益改善 (%)', fontsize=12)
    ax2.set_title('成本降低带来的收益改善 (30min)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=0, ha='center', fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}%',
               ha='center', va='bottom' if height > 0 else 'top',
               fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_sharpe_comparison(df, output_file):
    """
    绘制Sharpe比率对比
    """
    # Filter for 30min timeframe
    df_30min = df[df['timeframe'] == '30min'].copy()
    
    # Pivot
    pivot = df_30min.pivot_table(
        index=['symbol', 'strategy'],
        columns='cost_bp',
        values='sharpe_ratio',
        aggfunc='first'
    ).reset_index()
    
    # Sort
    pivot = pivot.sort_values(['symbol', 'strategy'])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(pivot))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, pivot[7.0], width, label='7bp成本', color='red', alpha=0.7)
    bars2 = ax.bar(x + width/2, pivot[0.3], width, label='0.3bp成本', color='green', alpha=0.7)
    
    ax.set_xlabel('策略', fontsize=12)
    ax.set_ylabel('Sharpe比率', fontsize=12)
    ax.set_title('交易成本对Sharpe比率的影响 (30min)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    labels = [f"{row['symbol']}\n{row['strategy'].split()[0]}" for _, row in pivot.iterrows()]
    ax.set_xticklabels(labels, rotation=0, ha='center', fontsize=9)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.5:  # Only label significant values
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_timeframe_sensitivity(df, output_file):
    """
    绘制不同时间周期的成本敏感性
    """
    # Filter for Symmetric strategy
    df_sym = df[df['strategy'] == 'B Symmetric'].copy()
    
    # Group by timeframe and cost
    summary = df_sym.groupby(['timeframe', 'cost_bp'])['total_return'].mean().reset_index()
    
    # Pivot
    pivot = summary.pivot(index='timeframe', columns='cost_bp', values='total_return')
    
    # Reorder timeframes
    timeframe_order = ['5min', '15min', '30min', '60min', '4h', '1d']
    pivot = pivot.reindex(timeframe_order)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(pivot))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, pivot[7.0]*100, width, label='7bp成本', color='red', alpha=0.7)
    bars2 = ax.bar(x + width/2, pivot[0.3]*100, width, label='0.3bp成本', color='green', alpha=0.7)
    
    ax.set_xlabel('时间周期', fontsize=12)
    ax.set_ylabel('平均总收益 (%)', fontsize=12)
    ax.set_title('Symmetric策略: 不同时间周期的成本敏感性', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def main():
    """主函数"""
    print("Loading data...")
    df = load_data()
    
    print(f"Total rows: {len(df)}")
    print(f"Cost levels: {df['cost_bp'].unique()}")
    
    output_dir = Path('market-manimpulation-analysis/results')
    
    # Plot 1: Cost Impact on Returns
    print("\nGenerating cost impact plot...")
    plot_cost_impact(df, output_dir / 'forex_cost_impact_returns.png')
    
    # Plot 2: Cost Impact on Sharpe
    print("Generating Sharpe comparison plot...")
    plot_sharpe_comparison(df, output_dir / 'forex_cost_impact_sharpe.png')
    
    # Plot 3: Timeframe Sensitivity
    print("Generating timeframe sensitivity plot...")
    plot_timeframe_sensitivity(df, output_dir / 'forex_cost_timeframe_sensitivity.png')
    
    print("\nVisualization complete!")

if __name__ == "__main__":
    main()

