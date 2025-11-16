"""
可视化回撤分析和杠杆风险

Visualize Drawdown Analysis and Leverage Risk
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
    forex_file = Path('market-manimpulation-analysis/results/symmetric_longshort_forex_lowcost.csv')
    df = pd.read_csv(forex_file)
    return df

def plot_drawdown_vs_return(df, output_file):
    """
    绘制回撤vs收益散点图
    """
    # Filter for 30min timeframe (best performing)
    df_30min = df[df['timeframe'] == '30min'].copy()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot by strategy type
    strategies = df_30min['strategy'].unique()
    colors = {'A Long Only': 'green', 'B Symmetric': 'blue', 'C Short Only': 'red'}
    markers = {'A Long Only': 'o', 'B Symmetric': 's', 'C Short Only': '^'}
    
    for strategy in strategies:
        data = df_30min[df_30min['strategy'] == strategy]
        ax.scatter(data['max_drawdown']*100, data['total_return']*100,
                  c=colors[strategy], marker=markers[strategy], s=200,
                  alpha=0.7, label=strategy, edgecolors='black', linewidth=1.5)
        
        # Add labels
        for _, row in data.iterrows():
            ax.annotate(row['symbol'], 
                       (row['max_drawdown']*100, row['total_return']*100),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=9, alpha=0.8)
    
    ax.set_xlabel('最大回撤 (%)', fontsize=12)
    ax.set_ylabel('总收益 (%)', fontsize=12)
    ax.set_title('回撤 vs 收益 (30min, 0.3bp成本)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_leverage_impact(df, output_file):
    """
    绘制不同杠杆倍数下的回撤
    """
    # Filter for best strategies
    best_strategies = [
        ('EURUSD', '30min', 'A Long Only'),
        ('USDCHF', '30min', 'B Symmetric'),
        ('EURUSD', '15min', 'B Symmetric'),
    ]
    
    leverage_levels = [1, 3, 5, 10, 20]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(leverage_levels))
    width = 0.25
    
    for i, (symbol, timeframe, strategy) in enumerate(best_strategies):
        data = df[(df['symbol'] == symbol) & 
                 (df['timeframe'] == timeframe) & 
                 (df['strategy'] == strategy)]
        
        if len(data) > 0:
            base_dd = data['max_drawdown'].values[0]
            leveraged_dd = [base_dd * lev * 100 for lev in leverage_levels]
            
            label = f"{symbol} {timeframe} {strategy.split()[0]}"
            ax.bar(x + i*width, leveraged_dd, width, label=label, alpha=0.7)
    
    ax.set_xlabel('杠杆倍数', fontsize=12)
    ax.set_ylabel('最大回撤 (%)', fontsize=12)
    ax.set_title('不同杠杆倍数下的最大回撤', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels([f'{lev}x' for lev in leverage_levels])
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    # Add danger zones
    ax.axhline(y=-10, color='orange', linestyle='--', linewidth=2, alpha=0.5, label='警戒线 (-10%)')
    ax.axhline(y=-20, color='red', linestyle='--', linewidth=2, alpha=0.5, label='危险线 (-20%)')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_timeframe_drawdown(df, output_file):
    """
    绘制不同时间周期的回撤对比
    """
    # Group by timeframe and strategy
    summary = df.groupby(['timeframe', 'strategy'])['max_drawdown'].mean().reset_index()
    
    # Pivot
    pivot = summary.pivot(index='timeframe', columns='strategy', values='max_drawdown')
    
    # Reorder timeframes
    timeframe_order = ['5min', '15min', '30min', '60min', '4h', '1d']
    pivot = pivot.reindex(timeframe_order)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(pivot))
    width = 0.25
    
    strategies = pivot.columns
    colors = {'A Long Only': 'green', 'B Symmetric': 'blue', 'C Short Only': 'red'}
    
    for i, strategy in enumerate(strategies):
        ax.bar(x + i*width, pivot[strategy]*100, width, 
              label=strategy, color=colors[strategy], alpha=0.7)
    
    ax.set_xlabel('时间周期', fontsize=12)
    ax.set_ylabel('平均最大回撤 (%)', fontsize=12)
    ax.set_title('不同时间周期的平均最大回撤', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(pivot.index)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def plot_sharpe_vs_drawdown(df, output_file):
    """
    绘制Sharpe vs 回撤散点图
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Filter for strategies with Sharpe > 0
    df_positive = df[df['sharpe_ratio'] > 0].copy()
    
    # Plot by timeframe
    timeframes = ['15min', '30min', '60min']
    colors_tf = {'15min': 'orange', '30min': 'green', '60min': 'blue'}
    markers_tf = {'15min': 'o', '30min': 's', '60min': '^'}
    
    for tf in timeframes:
        data = df_positive[df_positive['timeframe'] == tf]
        ax.scatter(data['max_drawdown']*100, data['sharpe_ratio'],
                  c=colors_tf[tf], marker=markers_tf[tf], s=150,
                  alpha=0.6, label=tf, edgecolors='black', linewidth=1)
    
    # Highlight best strategies
    best = df_positive[df_positive['sharpe_ratio'] > 3]
    for _, row in best.iterrows():
        ax.scatter(row['max_drawdown']*100, row['sharpe_ratio'],
                  c='red', marker='*', s=500, alpha=0.8,
                  edgecolors='black', linewidth=2)
        ax.annotate(f"{row['symbol']}\n{row['strategy'].split()[0]}", 
                   (row['max_drawdown']*100, row['sharpe_ratio']),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=8, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
    
    ax.set_xlabel('最大回撤 (%)', fontsize=12)
    ax.set_ylabel('Sharpe比率', fontsize=12)
    ax.set_title('Sharpe比率 vs 最大回撤 (0.3bp成本)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()

def main():
    """主函数"""
    print("Loading data...")
    df = load_data()
    
    print(f"Total rows: {len(df)}")
    
    output_dir = Path('market-manimpulation-analysis/results')
    
    # Plot 1: Drawdown vs Return
    print("\nGenerating drawdown vs return plot...")
    plot_drawdown_vs_return(df, output_dir / 'forex_drawdown_vs_return.png')
    
    # Plot 2: Leverage Impact
    print("Generating leverage impact plot...")
    plot_leverage_impact(df, output_dir / 'forex_leverage_drawdown.png')
    
    # Plot 3: Timeframe Drawdown
    print("Generating timeframe drawdown plot...")
    plot_timeframe_drawdown(df, output_dir / 'forex_timeframe_drawdown.png')
    
    # Plot 4: Sharpe vs Drawdown
    print("Generating Sharpe vs drawdown plot...")
    plot_sharpe_vs_drawdown(df, output_dir / 'forex_sharpe_vs_drawdown.png')
    
    print("\nVisualization complete!")

if __name__ == "__main__":
    main()

