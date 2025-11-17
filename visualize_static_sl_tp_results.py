# -*- coding: utf-8 -*-
"""
Visualize Static SL/TP Grid Search Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Read results
df = pd.read_csv('results/static_sl_tp_grid_4h_summary.csv')

# Create figure with subplots
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Color map for symbols
colors = {'XAUUSD': '#FFD700', 'BTCUSD': '#F7931A', 'ETHUSD': '#627EEA'}

# 1. Sharpe Ratio Heatmap for each symbol
for idx, symbol in enumerate(['XAUUSD', 'BTCUSD', 'ETHUSD']):
    ax = fig.add_subplot(gs[0, idx])
    symbol_df = df[df['symbol'] == symbol]
    
    # Create pivot table for heatmap (SL vs TP, averaged over max_holding_bars)
    pivot = symbol_df.groupby(['sl_mult', 'tp_mult'])['sharpe'].mean().reset_index()
    pivot_table = pivot.pivot(index='sl_mult', columns='tp_mult', values='sharpe')
    
    sns.heatmap(pivot_table, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                ax=ax, cbar_kws={'label': 'Sharpe Ratio'})
    ax.set_title(f'{symbol} - Sharpe Ratio (SL vs TP)', fontweight='bold', fontsize=12)
    ax.set_xlabel('TP Multiplier', fontweight='bold')
    ax.set_ylabel('SL Multiplier', fontweight='bold')

# 2. Total Return vs Max Drawdown scatter
ax2 = fig.add_subplot(gs[1, 0])
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    ax2.scatter(symbol_df['max_drawdown'] * 100, symbol_df['total_return'] * 100,
                alpha=0.6, s=50, label=symbol, color=colors[symbol])
ax2.set_xlabel('Max Drawdown (%)', fontweight='bold')
ax2.set_ylabel('Total Return (%)', fontweight='bold')
ax2.set_title('Return vs Drawdown Trade-off', fontweight='bold', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# 3. Sharpe Ratio by Max Holding Bars
ax3 = fig.add_subplot(gs[1, 1])
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    grouped = symbol_df.groupby('max_holding_bars')['sharpe'].mean()
    ax3.plot(grouped.index, grouped.values, marker='o', linewidth=2, 
             markersize=8, label=symbol, color=colors[symbol])
ax3.set_xlabel('Max Holding Bars', fontweight='bold')
ax3.set_ylabel('Average Sharpe Ratio', fontweight='bold')
ax3.set_title('Sharpe vs Max Holding Period', fontweight='bold', fontsize=12)
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)

# 4. Win Rate Distribution
ax4 = fig.add_subplot(gs[1, 2])
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    ax4.hist(symbol_df['win_rate'] * 100, bins=15, alpha=0.5, 
             label=symbol, color=colors[symbol])
ax4.set_xlabel('Win Rate (%)', fontweight='bold')
ax4.set_ylabel('Frequency', fontweight='bold')
ax4.set_title('Win Rate Distribution', fontweight='bold', fontsize=12)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')
ax4.axvline(x=50, color='green', linestyle='--', alpha=0.5, label='50%')

# 5. SL/TP Ratio vs Sharpe
ax5 = fig.add_subplot(gs[2, 0])
df['sl_tp_ratio'] = df['sl_mult'] / df['tp_mult']
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    ax5.scatter(symbol_df['sl_tp_ratio'], symbol_df['sharpe'],
                alpha=0.6, s=50, label=symbol, color=colors[symbol])
ax5.set_xlabel('SL/TP Ratio', fontweight='bold')
ax5.set_ylabel('Sharpe Ratio', fontweight='bold')
ax5.set_title('SL/TP Ratio vs Sharpe', fontweight='bold', fontsize=12)
ax5.legend()
ax5.grid(True, alpha=0.3)
ax5.axhline(y=0, color='red', linestyle='--', alpha=0.5)

# 6. Profit Factor Distribution
ax6 = fig.add_subplot(gs[2, 1])
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    ax6.hist(symbol_df['profit_factor'], bins=15, alpha=0.5,
             label=symbol, color=colors[symbol])
ax6.set_xlabel('Profit Factor', fontweight='bold')
ax6.set_ylabel('Frequency', fontweight='bold')
ax6.set_title('Profit Factor Distribution', fontweight='bold', fontsize=12)
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')
ax6.axvline(x=1.0, color='green', linestyle='--', alpha=0.5, label='Break-even')

# 7. Summary Table
ax7 = fig.add_subplot(gs[2, 2])
ax7.axis('off')

summary_data = []
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = df[df['symbol'] == symbol]
    best = symbol_df.nlargest(1, 'sharpe').iloc[0]
    summary_data.append([
        symbol,
        f"{best['sl_mult']:.1f}/{best['tp_mult']:.1f}/{int(best['max_holding_bars'])}",
        f"{best['sharpe']:.2f}",
        f"{best['total_return']:.1%}",
        f"{best['win_rate']:.1%}",
        f"{best['max_drawdown']:.1%}"
    ])

table = ax7.table(cellText=summary_data,
                  colLabels=['Symbol', 'SL/TP/Bars', 'Sharpe', 'Return', 'Win%', 'MaxDD'],
                  cellLoc='center',
                  loc='center',
                  bbox=[0, 0.2, 1, 0.6])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Color code the cells
for i in range(1, 4):
    symbol = summary_data[i-1][0]
    table[(i, 0)].set_facecolor(colors[symbol])
    table[(i, 0)].set_text_props(weight='bold', color='white')

ax7.set_title('Best Configuration per Symbol', fontsize=12, fontweight='bold', pad=20)

# Add key insights
insights_text = """
KEY INSIGHTS:
• BTCUSD: Only profitable asset (7.5% return, 0.17 Sharpe)
• XAUUSD: Near break-even (-1.7% return, -0.03 Sharpe)
• ETHUSD: Significant losses (-57.8% return, -0.23 Sharpe)
• Optimal SL: 3.0 ATR for XAUUSD/BTCUSD, 1.5 ATR for ETHUSD
• Optimal TP: 1.0-1.5 ATR across all assets
• Max Holding: 10-15 bars optimal
"""
ax7.text(0.5, 0.05, insights_text, transform=ax7.transAxes,
         fontsize=8, verticalalignment='bottom', horizontalalignment='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.suptitle('Static SL/TP Grid Search Results - 4H Timeframe', 
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig('results/static_sl_tp_grid_4h_analysis.png', dpi=300, bbox_inches='tight')
print("Visualization saved to: results/static_sl_tp_grid_4h_analysis.png")
plt.close()

# Print detailed summary
print("\n" + "=" * 80)
print("DETAILED SUMMARY BY SYMBOL")
print("=" * 80)

for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    print(f"\n{symbol}:")
    print("-" * 80)
    symbol_df = df[df['symbol'] == symbol]
    
    # Top 5 by Sharpe
    print("\nTop 5 Configurations by Sharpe:")
    top5 = symbol_df.nlargest(5, 'sharpe')[['sl_mult', 'tp_mult', 'max_holding_bars', 
                                              'sharpe', 'total_return', 'win_rate', 'max_drawdown']]
    print(top5.to_string(index=False))
    
    # Statistics
    print(f"\nOverall Statistics:")
    print(f"  Avg Sharpe:        {symbol_df['sharpe'].mean():>8.2f}")
    print(f"  Best Sharpe:       {symbol_df['sharpe'].max():>8.2f}")
    print(f"  Worst Sharpe:      {symbol_df['sharpe'].min():>8.2f}")
    print(f"  Avg Total Return:  {symbol_df['total_return'].mean():>8.1%}")
    print(f"  Avg Win Rate:      {symbol_df['win_rate'].mean():>8.1%}")
    print(f"  Avg Max DD:        {symbol_df['max_drawdown'].mean():>8.1%}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)

