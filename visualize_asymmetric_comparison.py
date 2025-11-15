"""
Visualize Asymmetric Strategy Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load results
df_pure = pd.read_csv('results/asymmetric_pure_results.csv')
df_managed = pd.read_csv('results/asymmetric_managed_results.csv')

# Also load reversal results for comparison
df_reversal_pure = pd.read_csv('results/pure_factor_performance.csv')
df_reversal_pure = df_reversal_pure[df_reversal_pure['strategy'] == 'reversal']

# Create figure
fig = plt.figure(figsize=(16, 12))

# 1. Sharpe Comparison - Pure vs Managed
ax1 = plt.subplot(2, 3, 1)
x = np.arange(len(df_pure))
width = 0.35

bars1 = ax1.bar(x - width/2, df_pure['sharpe'], width, label='Pure (No SL/TP)', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x + width/2, df_managed['sharpe_ratio'], width, label='Managed (With SL/TP)', color='coral', alpha=0.8)

ax1.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax1.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
ax1.set_title('Sharpe Ratio: Pure vs Managed', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(df_pure['bar_size'])
ax1.legend()
ax1.grid(axis='y', alpha=0.3)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)

# 2. Total Return Comparison
ax2 = plt.subplot(2, 3, 2)
bars1 = ax2.bar(x - width/2, df_pure['total_return']*100, width, label='Pure', color='steelblue', alpha=0.8)
bars2 = ax2.bar(x + width/2, df_managed['total_return']*100, width, label='Managed', color='coral', alpha=0.8)

ax2.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax2.set_ylabel('Total Return (%)', fontsize=11, fontweight='bold')
ax2.set_title('Total Return: Pure vs Managed', fontsize=12, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(df_pure['bar_size'])
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)

# 3. Win Rate Comparison
ax3 = plt.subplot(2, 3, 3)
bars1 = ax3.bar(x - width/2, df_pure['win_rate']*100, width, label='Pure', color='steelblue', alpha=0.8)
bars2 = ax3.bar(x + width/2, df_managed['win_rate']*100, width, label='Managed', color='coral', alpha=0.8)

ax3.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax3.set_ylabel('Win Rate (%)', fontsize=11, fontweight='bold')
ax3.set_title('Win Rate: Pure vs Managed', fontsize=12, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(df_pure['bar_size'])
ax3.legend()
ax3.grid(axis='y', alpha=0.3)
ax3.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.5, label='50% baseline')

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontsize=9)

# 4. Reversal vs Asymmetric (Pure Factor)
ax4 = plt.subplot(2, 3, 4)

# Filter to common timeframes
common_tf = ['5min', '30min']
reversal_sharpe = [df_reversal_pure[df_reversal_pure['bar_size']==tf]['sharpe'].values[0] for tf in common_tf]
asymmetric_sharpe = [df_pure[df_pure['bar_size']==tf]['sharpe'].values[0] for tf in common_tf]

x2 = np.arange(len(common_tf))
bars1 = ax4.bar(x2 - width/2, reversal_sharpe, width, label='Reversal', color='indianred', alpha=0.8)
bars2 = ax4.bar(x2 + width/2, asymmetric_sharpe, width, label='Asymmetric', color='seagreen', alpha=0.8)

ax4.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax4.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
ax4.set_title('Strategy Comparison: Reversal vs Asymmetric (Pure)', fontsize=12, fontweight='bold')
ax4.set_xticks(x2)
ax4.set_xticklabels(common_tf)
ax4.legend()
ax4.grid(axis='y', alpha=0.3)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)

# 5. Impact of SL/TP (Sharpe change)
ax5 = plt.subplot(2, 3, 5)
sharpe_change = df_managed['sharpe_ratio'].values - df_pure['sharpe'].values
colors = ['green' if x > 0 else 'red' for x in sharpe_change]

bars = ax5.bar(df_pure['bar_size'], sharpe_change, color=colors, alpha=0.7)
ax5.set_xlabel('Timeframe', fontsize=11, fontweight='bold')
ax5.set_ylabel('Sharpe Change', fontsize=11, fontweight='bold')
ax5.set_title('Impact of SL/TP on Sharpe', fontsize=12, fontweight='bold')
ax5.grid(axis='y', alpha=0.3)
ax5.axhline(y=0, color='black', linestyle='-', linewidth=1)

for bar in bars:
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:+.2f}',
            ha='center', va='bottom' if height > 0 else 'top', fontsize=10, fontweight='bold')

# 6. Summary Table
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

# Create summary data
summary_data = []
for _, row in df_pure.iterrows():
    tf = row['bar_size']
    managed_row = df_managed[df_managed['bar_size'] == tf].iloc[0]
    
    summary_data.append([
        tf,
        f"{row['sharpe']:.2f}",
        f"{managed_row['sharpe_ratio']:.2f}",
        f"{(managed_row['sharpe_ratio'] - row['sharpe']):.2f}"
    ])

table = ax6.table(cellText=summary_data,
                 colLabels=['Timeframe', 'Pure\nSharpe', 'Managed\nSharpe', 'Change'],
                 cellLoc='center',
                 loc='center',
                 bbox=[0, 0.2, 1, 0.6])

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Color code the change column
for i in range(1, len(summary_data) + 1):
    change_val = float(summary_data[i-1][3])
    if change_val > 0:
        table[(i, 3)].set_facecolor('#90EE90')
    else:
        table[(i, 3)].set_facecolor('#FFB6C6')

# Header styling
for j in range(4):
    table[(0, j)].set_facecolor('#4472C4')
    table[(0, j)].set_text_props(weight='bold', color='white')

ax6.text(0.5, 0.9, 'Summary: SL/TP Impact', 
         ha='center', va='top', fontsize=12, fontweight='bold', transform=ax6.transAxes)

# Add key findings
findings = [
    "KEY FINDINGS:",
    "• 15min Pure: Sharpe 1.43 (BEST)",
    "• 60min Managed: Sharpe 1.65 (BEST)",
    "• SL/TP hurts 5/15/30min",
    "• SL/TP helps 60min"
]

y_pos = 0.15
for finding in findings:
    weight = 'bold' if 'KEY' in finding or 'BEST' in finding else 'normal'
    ax6.text(0.05, y_pos, finding, ha='left', va='top', fontsize=9, 
            fontweight=weight, transform=ax6.transAxes)
    y_pos -= 0.04

plt.suptitle('Asymmetric Strategy - Comprehensive Analysis\n(UP=continuation, DOWN=reversal)', 
             fontsize=14, fontweight='bold', y=0.995)

plt.tight_layout()
plt.savefig('results/asymmetric_strategy_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Saved: results/asymmetric_strategy_analysis.png")

plt.show()

