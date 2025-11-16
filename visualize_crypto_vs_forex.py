"""
可视化加密货币 vs 外汇的策略表现对比

Visualize Crypto vs Forex Strategy Performance Comparison
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """加载数据"""
    # Crypto data
    crypto_file = Path('market-manimpulation-analysis/results/symmetric_longshort_all_timeframes.csv')
    forex_file = Path('market-manimpulation-analysis/results/symmetric_longshort_forex.csv')
    
    crypto_df = pd.read_csv(crypto_file)
    forex_df = pd.read_csv(forex_file)
    
    # Add market type
    crypto_df['market'] = 'Crypto'
    forex_df['market'] = 'Forex'
    
    # Combine
    all_df = pd.concat([crypto_df, forex_df], ignore_index=True)
    
    return all_df

def plot_long_short_asymmetry(df, output_file):
    """
    绘制多空不对称性对比图
    """
    # Filter for 30min timeframe
    df_30min = df[df['timeframe'] == '30min'].copy()
    
    # Pivot to get long and short returns
    pivot = df_30min.pivot_table(
        index=['symbol', 'market'],
        columns='strategy',
        values='total_return',
        aggfunc='first'
    ).reset_index()
    
    # Calculate long-short gap
    pivot['long_short_gap'] = pivot['A Long Only'] - pivot['C Short Only']
    
    # Sort by market type
    pivot = pivot.sort_values(['market', 'symbol'])
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Long vs Short Returns
    ax1 = axes[0]
    x = np.arange(len(pivot))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, pivot['A Long Only']*100, width, label='Long-Only', color='green', alpha=0.7)
    bars2 = ax1.bar(x + width/2, pivot['C Short Only']*100, width, label='Short-Only', color='red', alpha=0.7)
    
    ax1.set_xlabel('Asset', fontsize=12)
    ax1.set_ylabel('Total Return (%)', fontsize=12)
    ax1.set_title('Long vs Short Returns (30min)', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(pivot['symbol'], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add market type labels
    for i, (idx, row) in enumerate(pivot.iterrows()):
        if row['market'] == 'Crypto':
            ax1.text(i, -1, 'Crypto', ha='center', va='top', fontsize=8, color='blue')
        else:
            ax1.text(i, -1, 'Forex', ha='center', va='top', fontsize=8, color='orange')
    
    # Plot 2: Long-Short Gap
    ax2 = axes[1]
    colors = ['green' if gap > 0 else 'red' for gap in pivot['long_short_gap']]
    bars = ax2.bar(x, pivot['long_short_gap']*100, color=colors, alpha=0.7)
    
    ax2.set_xlabel('Asset', fontsize=12)
    ax2.set_ylabel('Long-Short Gap (%)', fontsize=12)
    ax2.set_title('Long-Short Asymmetry (30min)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot['symbol'], rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add market type labels
    for i, (idx, row) in enumerate(pivot.iterrows()):
        if row['market'] == 'Crypto':
            ax2.text(i, -0.5, 'Crypto', ha='center', va='top', fontsize=8, color='blue')
        else:
            ax2.text(i, -0.5, 'Forex', ha='center', va='top', fontsize=8, color='orange')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_timeframe_comparison(df, output_file):
    """
    绘制不同时间周期的表现对比
    """
    # Filter for Long-Only strategy
    df_long = df[df['strategy'] == 'A Long Only'].copy()
    
    # Group by market and timeframe
    summary = df_long.groupby(['market', 'timeframe'])['total_return'].mean().reset_index()
    
    # Pivot
    pivot = summary.pivot(index='timeframe', columns='market', values='total_return')
    
    # Reorder timeframes
    timeframe_order = ['5min', '15min', '30min', '60min', '4h', '1d']
    pivot = pivot.reindex(timeframe_order)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(pivot))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, pivot['Crypto']*100, width, label='Crypto', color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, pivot['Forex']*100, width, label='Forex', color='orange', alpha=0.7)
    
    ax.set_xlabel('Timeframe', fontsize=12)
    ax.set_ylabel('Average Total Return (%)', fontsize=12)
    ax.set_title('Long-Only Strategy: Crypto vs Forex Across Timeframes', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}%',
                   ha='center', va='bottom' if height > 0 else 'top',
                   fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def main():
    """主函数"""
    print("Loading data...")
    df = load_data()
    
    print(f"Total rows: {len(df)}")
    print(f"Markets: {df['market'].unique()}")
    print(f"Symbols: {df['symbol'].unique()}")
    print(f"Timeframes: {df['timeframe'].unique()}")
    
    output_dir = Path('market-manimpulation-analysis/results')
    
    # Plot 1: Long-Short Asymmetry
    print("\nGenerating long-short asymmetry plot...")
    plot_long_short_asymmetry(df, output_dir / 'crypto_vs_forex_asymmetry.png')
    
    # Plot 2: Timeframe Comparison
    print("Generating timeframe comparison plot...")
    plot_timeframe_comparison(df, output_dir / 'crypto_vs_forex_timeframes.png')
    
    print("\nVisualization complete!")

if __name__ == "__main__":
    main()

