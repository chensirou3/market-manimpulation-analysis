"""
Visualize Route A Timeframe Study Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')

# Load comparison data
df = pd.read_csv('results/routeA_timeframe_comparison.csv')

# Create figure with subplots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Color scheme
colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
bar_sizes = df['bar_size'].tolist()

# ============================================================================
# 1. Sharpe Ratio Comparison
# ============================================================================
ax1 = fig.add_subplot(gs[0, 0])
bars1 = ax1.bar(bar_sizes, df['sharpe_ratio'], color=colors, alpha=0.8, edgecolor='black')
ax1.set_title('Sharpe Ratio by Timeframe', fontsize=14, fontweight='bold')
ax1.set_ylabel('Sharpe Ratio', fontsize=12)
ax1.set_xlabel('Timeframe', fontsize=12)
ax1.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Target: 1.0')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Highlight best
best_idx = df['sharpe_ratio'].idxmax()
bars1[best_idx].set_color('#e74c3c')
bars1[best_idx].set_edgecolor('gold')
bars1[best_idx].set_linewidth(3)

# Add values on bars
for i, (bar, val) in enumerate(zip(bars1, df['sharpe_ratio'])):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.2f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 2. Annualized Return Comparison
# ============================================================================
ax2 = fig.add_subplot(gs[0, 1])
bars2 = ax2.bar(bar_sizes, df['annualized_return']*100, color=colors, alpha=0.8, edgecolor='black')
ax2.set_title('Annualized Return by Timeframe', fontsize=14, fontweight='bold')
ax2.set_ylabel('Annualized Return (%)', fontsize=12)
ax2.set_xlabel('Timeframe', fontsize=12)
ax2.axhline(y=5.0, color='red', linestyle='--', alpha=0.5, label='Target: 5%')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# Highlight best
bars2[best_idx].set_color('#e74c3c')
bars2[best_idx].set_edgecolor('gold')
bars2[best_idx].set_linewidth(3)

for i, (bar, val) in enumerate(zip(bars2, df['annualized_return']*100)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.2f}%',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 3. Max Drawdown Comparison
# ============================================================================
ax3 = fig.add_subplot(gs[0, 2])
bars3 = ax3.bar(bar_sizes, df['max_drawdown']*100, color=colors, alpha=0.8, edgecolor='black')
ax3.set_title('Max Drawdown by Timeframe', fontsize=14, fontweight='bold')
ax3.set_ylabel('Max Drawdown (%)', fontsize=12)
ax3.set_xlabel('Timeframe', fontsize=12)
ax3.axhline(y=-5.0, color='red', linestyle='--', alpha=0.5, label='Target: -5%')
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

# Highlight best (smallest drawdown)
best_dd_idx = df['max_drawdown'].idxmax()  # Closest to 0
bars3[best_dd_idx].set_color('#2ecc71')
bars3[best_dd_idx].set_edgecolor('gold')
bars3[best_dd_idx].set_linewidth(3)

for i, (bar, val) in enumerate(zip(bars3, df['max_drawdown']*100)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.2f}%',
             ha='center', va='top', fontsize=10, fontweight='bold')

# ============================================================================
# 4. Win Rate Comparison
# ============================================================================
ax4 = fig.add_subplot(gs[1, 0])
bars4 = ax4.bar(bar_sizes, df['win_rate']*100, color=colors, alpha=0.8, edgecolor='black')
ax4.set_title('Win Rate by Timeframe', fontsize=14, fontweight='bold')
ax4.set_ylabel('Win Rate (%)', fontsize=12)
ax4.set_xlabel('Timeframe', fontsize=12)
ax4.axhline(y=50.0, color='red', linestyle='--', alpha=0.5, label='Random: 50%')
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

for i, (bar, val) in enumerate(zip(bars4, df['win_rate']*100)):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.1f}%',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 5. Number of Trades
# ============================================================================
ax5 = fig.add_subplot(gs[1, 1])
bars5 = ax5.bar(bar_sizes, df['n_trades'], color=colors, alpha=0.8, edgecolor='black')
ax5.set_title('Number of Trades by Timeframe', fontsize=14, fontweight='bold')
ax5.set_ylabel('Number of Trades', fontsize=12)
ax5.set_xlabel('Timeframe', fontsize=12)
ax5.grid(axis='y', alpha=0.3)

for i, (bar, val) in enumerate(zip(bars5, df['n_trades'])):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(val):,}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 6. Average PnL per Trade
# ============================================================================
ax6 = fig.add_subplot(gs[1, 2])
bars6 = ax6.bar(bar_sizes, df['avg_pnl'], color=colors, alpha=0.8, edgecolor='black')
ax6.set_title('Average PnL per Trade', fontsize=14, fontweight='bold')
ax6.set_ylabel('Avg PnL ($)', fontsize=12)
ax6.set_xlabel('Timeframe', fontsize=12)
ax6.grid(axis='y', alpha=0.3)

# Highlight best
best_pnl_idx = df['avg_pnl'].idxmax()
bars6[best_pnl_idx].set_color('#2ecc71')
bars6[best_pnl_idx].set_edgecolor('gold')
bars6[best_pnl_idx].set_linewidth(3)

for i, (bar, val) in enumerate(zip(bars6, df['avg_pnl'])):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
             f'${val:.2f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 7. Profit Factor
# ============================================================================
ax7 = fig.add_subplot(gs[2, 0])
bars7 = ax7.bar(bar_sizes, df['profit_factor'], color=colors, alpha=0.8, edgecolor='black')
ax7.set_title('Profit Factor by Timeframe', fontsize=14, fontweight='bold')
ax7.set_ylabel('Profit Factor', fontsize=12)
ax7.set_xlabel('Timeframe', fontsize=12)
ax7.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Breakeven: 1.0')
ax7.legend()
ax7.grid(axis='y', alpha=0.3)

for i, (bar, val) in enumerate(zip(bars7, df['profit_factor'])):
    height = bar.get_height()
    ax7.text(bar.get_x() + bar.get_width()/2., height,
             f'{val:.3f}',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 8. Risk-Return Scatter
# ============================================================================
ax8 = fig.add_subplot(gs[2, 1])
scatter = ax8.scatter(df['annualized_volatility']*100, 
                     df['annualized_return']*100,
                     s=300, c=colors, alpha=0.7, edgecolors='black', linewidths=2)

# Add labels
for i, bar_size in enumerate(bar_sizes):
    ax8.annotate(bar_size, 
                (df['annualized_volatility'].iloc[i]*100, df['annualized_return'].iloc[i]*100),
                xytext=(5, 5), textcoords='offset points', fontsize=11, fontweight='bold')

ax8.set_title('Risk-Return Profile', fontsize=14, fontweight='bold')
ax8.set_xlabel('Annualized Volatility (%)', fontsize=12)
ax8.set_ylabel('Annualized Return (%)', fontsize=12)
ax8.grid(True, alpha=0.3)

# Add diagonal lines for Sharpe ratios
vol_range = np.linspace(0, df['annualized_volatility'].max()*100*1.1, 100)
for sharpe in [0.5, 1.0, 1.5]:
    ax8.plot(vol_range, vol_range * sharpe, '--', alpha=0.3, label=f'Sharpe={sharpe}')
ax8.legend(fontsize=9)

# ============================================================================
# 9. Summary Table
# ============================================================================
ax9 = fig.add_subplot(gs[2, 2])
ax9.axis('off')

# Create summary text
summary_text = "📊 ROUTE A SUMMARY\n" + "="*30 + "\n\n"
summary_text += "🏆 BEST TIMEFRAME: 30min\n\n"
summary_text += "Key Metrics (30min):\n"
summary_text += f"  Sharpe:      {df.loc[2, 'sharpe_ratio']:.2f}\n"
summary_text += f"  Ann. Return: {df.loc[2, 'annualized_return']*100:.2f}%\n"
summary_text += f"  Max DD:      {df.loc[2, 'max_drawdown']*100:.2f}%\n"
summary_text += f"  Win Rate:    {df.loc[2, 'win_rate']*100:.1f}%\n"
summary_text += f"  Trades:      {int(df.loc[2, 'n_trades']):,}\n\n"
summary_text += "Improvement vs 5min:\n"
summary_text += f"  Sharpe:      +{(df.loc[2, 'sharpe_ratio']/df.loc[0, 'sharpe_ratio']-1)*100:.0f}%\n"
summary_text += f"  Ann. Return: +{(df.loc[2, 'annualized_return']/df.loc[0, 'annualized_return']-1)*100:.0f}%\n"
summary_text += f"  Max DD:      {(df.loc[2, 'max_drawdown']/df.loc[0, 'max_drawdown']-1)*100:.0f}%\n"

ax9.text(0.1, 0.9, summary_text, transform=ax9.transAxes,
         fontsize=11, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Overall title
fig.suptitle('Route A: Timeframe Study - Comprehensive Analysis', 
             fontsize=18, fontweight='bold', y=0.995)

# Save
plt.tight_layout()
plt.savefig('results/routeA_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Saved: results/routeA_comprehensive_analysis.png")

plt.show()

