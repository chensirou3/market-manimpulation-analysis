# -*- coding: utf-8 -*-
"""
Visualize comparison of all three assets across timeframes
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read complete comparison data
df = pd.read_csv('results/all_assets_complete_comparison.csv')

# Create figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Trade Path Analysis - BTC vs ETH vs XAUUSD Comparison', fontsize=16, fontweight='bold')

# Define colors for each asset
colors = {'BTC': '#F7931A', 'ETH': '#627EEA', 'XAUUSD': '#FFD700'}
timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']

# 1. Profit Capture Ratio by Timeframe
ax1 = axes[0, 0]
for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = df[df['asset'] == asset].sort_values('timeframe', key=lambda x: x.map({tf: i for i, tf in enumerate(timeframes)}))
    ax1.plot(asset_df['timeframe'], asset_df['profit_capture_ratio'] * 100, 
             marker='o', linewidth=2, markersize=8, label=asset, color=colors[asset])
ax1.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax1.set_ylabel('Profit Capture Rate (%)', fontsize=11, fontweight='bold')
ax1.set_title('Profit Capture Rate by Timeframe', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='30% threshold')

# 2. Win Rate by Timeframe
ax2 = axes[0, 1]
for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = df[df['asset'] == asset].sort_values('timeframe', key=lambda x: x.map({tf: i for i, tf in enumerate(timeframes)}))
    ax2.plot(asset_df['timeframe'], asset_df['win_rate'] * 100, 
             marker='s', linewidth=2, markersize=8, label=asset, color=colors[asset])
ax2.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax2.set_ylabel('Win Rate (%)', fontsize=11, fontweight='bold')
ax2.set_title('Win Rate by Timeframe', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.axhline(y=50, color='green', linestyle='--', alpha=0.5, label='50% threshold')

# 3. Average PnL by Timeframe
ax3 = axes[0, 2]
for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = df[df['asset'] == asset].sort_values('timeframe', key=lambda x: x.map({tf: i for i, tf in enumerate(timeframes)}))
    ax3.plot(asset_df['timeframe'], asset_df['avg_pnl'] * 100, 
             marker='^', linewidth=2, markersize=8, label=asset, color=colors[asset])
ax3.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax3.set_ylabel('Average PnL (%)', fontsize=11, fontweight='bold')
ax3.set_title('Average PnL by Timeframe', fontsize=12, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)

# 4. Number of Trades by Timeframe
ax4 = axes[1, 0]
x = np.arange(len(timeframes))
width = 0.25
for i, asset in enumerate(['BTC', 'ETH', 'XAUUSD']):
    asset_df = df[df['asset'] == asset].sort_values('timeframe', key=lambda x: x.map({tf: i for i, tf in enumerate(timeframes)}))
    ax4.bar(x + i*width, asset_df['n_trades'], width, label=asset, color=colors[asset], alpha=0.8)
ax4.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax4.set_ylabel('Number of Trades', fontsize=11, fontweight='bold')
ax4.set_title('Number of Trades by Timeframe', fontsize=12, fontweight='bold')
ax4.set_xticks(x + width)
ax4.set_xticklabels(timeframes)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')
ax4.set_yscale('log')

# 5. t_mfe Median by Timeframe
ax5 = axes[1, 1]
for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = df[df['asset'] == asset].sort_values('timeframe', key=lambda x: x.map({tf: i for i, tf in enumerate(timeframes)}))
    ax5.plot(asset_df['timeframe'], asset_df['t_mfe_median'], 
             marker='D', linewidth=2, markersize=8, label=asset, color=colors[asset])
ax5.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax5.set_ylabel('t_mfe Median (bars)', fontsize=11, fontweight='bold')
ax5.set_title('Optimal Holding Time by Timeframe', fontsize=12, fontweight='bold')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. Summary Statistics Table
ax6 = axes[1, 2]
ax6.axis('off')

summary_data = []
for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = df[df['asset'] == asset]
    summary_data.append([
        asset,
        f"{asset_df['n_trades'].sum():,}",
        f"{asset_df['win_rate'].mean():.1%}",
        f"{asset_df['profit_capture_ratio'].mean():.1%}",
        f"{asset_df.loc[asset_df['profit_capture_ratio'].idxmax(), 'timeframe']}"
    ])

table = ax6.table(cellText=summary_data,
                  colLabels=['Asset', 'Total\nTrades', 'Avg\nWin Rate', 'Avg\nCapture', 'Best\nTF'],
                  cellLoc='center',
                  loc='center',
                  bbox=[0, 0.2, 1, 0.6])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Color code the cells
for i in range(1, 4):
    asset = summary_data[i-1][0]
    table[(i, 0)].set_facecolor(colors[asset])
    table[(i, 0)].set_text_props(weight='bold', color='white')

ax6.set_title('Summary Statistics', fontsize=12, fontweight='bold', pad=20)

# Add key insights text
insights_text = """
KEY INSIGHTS:
• XAUUSD 4H: Best overall (46.1% capture rate)
• BTC 4H: High profit per trade (5.90%)
• ETH: Generally underperforms
• Long timeframes (4H, 1D) >> Short timeframes
"""
ax6.text(0.5, 0.05, insights_text, transform=ax6.transAxes,
         fontsize=9, verticalalignment='bottom', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig('results/all_assets_comparison.png', dpi=300, bbox_inches='tight')
print("Visualization saved to: results/all_assets_comparison.png")
plt.close()

print("\n" + "=" * 80)
print("VISUALIZATION COMPLETE!")
print("=" * 80)
print("\nGenerated files:")
print("1. results/all_assets_complete_comparison.csv - Complete data table")
print("2. results/all_assets_comparison.png - Comprehensive visualization")
print("\nKey findings:")
print("• XAUUSD 4H is the best configuration overall (46.1% profit capture)")
print("• BTC 4H offers highest single-trade profit (5.90% avg)")
print("• ETH underperforms across all timeframes")
print("• Longer timeframes (4H, 1D) significantly outperform shorter ones")
print("=" * 80)

