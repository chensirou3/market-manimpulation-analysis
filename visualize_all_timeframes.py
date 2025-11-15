"""
Visualize All Timeframes - Complete Comparison
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load all results
df_pure = pd.read_csv('results/asymmetric_pure_results.csv')
df_managed = pd.read_csv('results/asymmetric_managed_results.csv')
df_extended_pure = pd.read_csv('results/extended_asymmetric_pure_results.csv')
df_extended_managed = pd.read_csv('results/extended_asymmetric_managed_results.csv')

# Combine
df_pure_all = pd.concat([df_pure, df_extended_pure], ignore_index=True)
df_managed_all = pd.concat([df_managed, df_extended_managed], ignore_index=True)

# Define timeframe order
timeframe_order = ['5min', '15min', '30min', '60min', '4h', '1d']
df_pure_all['bar_size'] = pd.Categorical(df_pure_all['bar_size'], categories=timeframe_order, ordered=True)
df_managed_all['bar_size'] = pd.Categorical(df_managed_all['bar_size'], categories=timeframe_order, ordered=True)
df_pure_all = df_pure_all.sort_values('bar_size')
df_managed_all = df_managed_all.sort_values('bar_size')

# Create figure
fig = plt.figure(figsize=(18, 12))

# 1. Sharpe Comparison - Pure vs Managed
ax1 = plt.subplot(2, 3, 1)
x = np.arange(len(df_pure_all))
width = 0.35

bars1 = ax1.bar(x - width/2, df_pure_all['sharpe'], width, label='Pure (No SL/TP)', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x + width/2, df_managed_all['sharpe_ratio'], width, label='Managed (With SL/TP)', color='coral', alpha=0.8)

ax1.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax1.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
ax1.set_title('Sharpe Ratio: Pure vs Managed (All Timeframes)', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(df_pure_all['bar_size'])
ax1.legend()
ax1.grid(axis='y', alpha=0.3)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=8)

# 2. Win Rate Comparison
ax2 = plt.subplot(2, 3, 2)
bars1 = ax2.bar(x - width/2, df_pure_all['win_rate']*100, width, label='Pure', color='steelblue', alpha=0.8)
bars2 = ax2.bar(x + width/2, df_managed_all['win_rate']*100, width, label='Managed', color='coral', alpha=0.8)

ax2.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax2.set_ylabel('Win Rate (%)', fontsize=11, fontweight='bold')
ax2.set_title('Win Rate: Pure vs Managed', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(df_pure_all['bar_size'])
ax2.legend()
ax2.grid(axis='y', alpha=0.3)
ax2.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.5)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=8)

# 3. Average Return per Trade (Pure)
ax3 = plt.subplot(2, 3, 3)
colors = ['green' if x > 0 else 'red' for x in df_pure_all['avg_return']]
bars = ax3.bar(df_pure_all['bar_size'], df_pure_all['avg_return']*10000, color=colors, alpha=0.7)

ax3.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax3.set_ylabel('Avg Return per Trade (bps)', fontsize=11, fontweight='bold')
ax3.set_title('Pure Factor: Avg Return per Trade', fontsize=12, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)

for bar in bars:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}',
            ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

# 4. Impact of SL/TP (Sharpe change)
ax4 = plt.subplot(2, 3, 4)
sharpe_change = df_managed_all['sharpe_ratio'].values - df_pure_all['sharpe'].values
colors = ['green' if x > 0 else 'red' for x in sharpe_change]

bars = ax4.bar(df_pure_all['bar_size'], sharpe_change, color=colors, alpha=0.7)
ax4.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax4.set_ylabel('Sharpe Change', fontsize=11, fontweight='bold')
ax4.set_title('Impact of SL/TP on Sharpe', fontsize=12, fontweight='bold')
ax4.grid(axis='y', alpha=0.3)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=1)

for bar in bars:
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:+.2f}',
            ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

# 5. Number of Trades
ax5 = plt.subplot(2, 3, 5)
ax5.bar(df_pure_all['bar_size'], df_pure_all['n_trades'], color='steelblue', alpha=0.7)
ax5.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax5.set_ylabel('Number of Trades', fontsize=11, fontweight='bold')
ax5.set_title('Trade Frequency by Timeframe', fontsize=12, fontweight='bold')
ax5.set_yscale('log')
ax5.grid(axis='y', alpha=0.3)

for i, (tf, n) in enumerate(zip(df_pure_all['bar_size'], df_pure_all['n_trades'])):
    ax5.text(i, n, f'{n:,}', ha='center', va='bottom', fontsize=9)

# 6. Summary Table
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

# Create summary data - highlight best performers
summary_data = []
for i, row in df_pure_all.iterrows():
    tf = row['bar_size']
    managed_row = df_managed_all[df_managed_all['bar_size'] == tf].iloc[0]
    
    pure_sharpe = row['sharpe']
    managed_sharpe = managed_row['sharpe_ratio']
    
    # Mark best
    pure_str = f"{pure_sharpe:.2f}"
    managed_str = f"{managed_sharpe:.2f}"
    
    if pure_sharpe == df_pure_all['sharpe'].max():
        pure_str += " 🥇"
    if managed_sharpe == df_managed_all['sharpe_ratio'].max():
        managed_str += " 🥇"
    
    summary_data.append([
        tf,
        pure_str,
        managed_str,
        f"{row['win_rate']*100:.1f}%"
    ])

table = ax6.table(cellText=summary_data,
                 colLabels=['TF', 'Pure\nSharpe', 'Managed\nSharpe', 'Pure\nWin%'],
                 cellLoc='center',
                 loc='center',
                 bbox=[0, 0.15, 1, 0.7])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Header styling
for j in range(4):
    table[(0, j)].set_facecolor('#4472C4')
    table[(0, j)].set_text_props(weight='bold', color='white')

# Highlight best rows
for i in range(1, len(summary_data) + 1):
    if '🥇' in summary_data[i-1][1]:  # Best pure
        table[(i, 1)].set_facecolor('#90EE90')
    if '🥇' in summary_data[i-1][2]:  # Best managed
        table[(i, 2)].set_facecolor('#90EE90')

ax6.text(0.5, 0.92, 'Performance Summary', 
         ha='center', va='top', fontsize=12, fontweight='bold', transform=ax6.transAxes)

# Add key findings
findings = [
    "KEY FINDINGS:",
    "• 15min Pure: Best factor (Sharpe 1.43)",
    "• 4h Managed: Best overall (Sharpe 4.03)",
    "• SL/TP helps 60min/4h, hurts others",
    "• Daily has high potential (needs tuning)"
]

y_pos = 0.10
for finding in findings:
    weight = 'bold' if 'KEY' in finding or 'Best' in finding else 'normal'
    ax6.text(0.05, y_pos, finding, ha='left', va='top', fontsize=8, 
            fontweight=weight, transform=ax6.transAxes)
    y_pos -= 0.035

plt.suptitle('Asymmetric Strategy - All Timeframes Analysis (5min to Daily)\n(UP=continuation, DOWN=reversal)', 
             fontsize=14, fontweight='bold', y=0.995)

plt.tight_layout()
plt.savefig('results/all_timeframes_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Saved: results/all_timeframes_analysis.png")

plt.show()

