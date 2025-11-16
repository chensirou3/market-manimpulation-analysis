"""
Visualize Trade Path Analysis Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set Chinese font
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# Load data for all timeframes
timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']
data = {}

for tf in timeframes:
    fpath = f'results/xauusd_{tf}_trade_path_analysis.csv'
    if Path(fpath).exists():
        data[tf] = pd.read_csv(fpath)

# Create figure with multiple subplots
fig = plt.figure(figsize=(20, 12))

# ============================================================================
# 1. MFE vs MAE Scatter Plot (4H - Best Timeframe)
# ============================================================================
ax1 = plt.subplot(2, 3, 1)
df_4h = data['4h']
winners = df_4h[df_4h['pnl_final'] > 0]
losers = df_4h[df_4h['pnl_final'] <= 0]

ax1.scatter(losers['mae']*100, losers['mfe']*100, 
           alpha=0.6, s=100, c='red', label=f'亏损交易 (n={len(losers)})')
ax1.scatter(winners['mae']*100, winners['mfe']*100, 
           alpha=0.6, s=100, c='green', label=f'盈利交易 (n={len(winners)})')

# Add diagonal line (MFE = MAE)
max_val = max(df_4h['mfe'].max(), abs(df_4h['mae'].min())) * 100
ax1.plot([-max_val, max_val], [-max_val, max_val], 'k--', alpha=0.3, label='MFE=MAE')

ax1.set_xlabel('最大浮亏 MAE (%)', fontsize=12)
ax1.set_ylabel('最大浮盈 MFE (%)', fontsize=12)
ax1.set_title('4H周期: MFE vs MAE 散点图', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
ax1.axvline(x=0, color='k', linestyle='-', linewidth=0.5)

# ============================================================================
# 2. Profit Capture Efficiency Comparison
# ============================================================================
ax2 = plt.subplot(2, 3, 2)

tf_names = []
capture_rates = []
avg_mfe = []
avg_pnl = []

for tf in timeframes:
    if tf in data:
        df = data[tf]
        tf_names.append(tf)
        
        mfe_mean = df['mfe'].mean()
        pnl_mean = df['pnl_final'].mean()
        
        avg_mfe.append(mfe_mean * 100)
        avg_pnl.append(pnl_mean * 100)
        
        if mfe_mean > 0:
            capture_rate = (pnl_mean / mfe_mean) * 100
        else:
            capture_rate = 0
        capture_rates.append(capture_rate)

x = np.arange(len(tf_names))
width = 0.35

bars1 = ax2.bar(x - width/2, avg_mfe, width, label='平均MFE (潜在收益)', alpha=0.8, color='skyblue')
bars2 = ax2.bar(x + width/2, avg_pnl, width, label='平均PnL (实际收益)', alpha=0.8, color='orange')

ax2.set_xlabel('时间周期', fontsize=12)
ax2.set_ylabel('收益率 (%)', fontsize=12)
ax2.set_title('潜在收益 vs 实际收益对比', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(tf_names)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%',
                ha='center', va='bottom', fontsize=8)

# ============================================================================
# 3. Profit Capture Rate
# ============================================================================
ax3 = plt.subplot(2, 3, 3)

colors = ['red' if r < 20 else 'orange' if r < 40 else 'green' for r in capture_rates]
bars = ax3.bar(tf_names, capture_rates, color=colors, alpha=0.7)

ax3.set_xlabel('时间周期', fontsize=12)
ax3.set_ylabel('收益捕获率 (%)', fontsize=12)
ax3.set_title('收益捕获率对比', fontsize=14, fontweight='bold')
ax3.axhline(y=50, color='green', linestyle='--', alpha=0.5, label='50%基准线')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3, axis='y')

# Add value labels
for i, (bar, rate) in enumerate(zip(bars, capture_rates)):
    ax3.text(bar.get_x() + bar.get_width()/2., rate + 2,
            f'{rate:.1f}%',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# ============================================================================
# 4. MFE Distribution (All Timeframes)
# ============================================================================
ax4 = plt.subplot(2, 3, 4)

for tf in ['30min', '60min', '4h']:
    if tf in data:
        df = data[tf]
        ax4.hist(df['mfe']*100, bins=30, alpha=0.5, label=tf, density=True)

ax4.set_xlabel('最大浮盈 MFE (%)', fontsize=12)
ax4.set_ylabel('密度', fontsize=12)
ax4.set_title('MFE分布对比 (30min, 60min, 4H)', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)

# ============================================================================
# 5. t_mfe Distribution (Optimal Exit Timing)
# ============================================================================
ax5 = plt.subplot(2, 3, 5)

t_mfe_data = []
labels = []

for tf in timeframes:
    if tf in data:
        df = data[tf]
        t_mfe_data.append(df['t_mfe'].values)
        labels.append(f"{tf}\n(中位={df['t_mfe'].median():.0f})")

bp = ax5.boxplot(t_mfe_data, labels=labels, patch_artist=True)

# Color the boxes
colors_box = ['lightcoral', 'lightsalmon', 'lightgreen', 'lightblue', 'plum', 'wheat']
for patch, color in zip(bp['boxes'], colors_box[:len(bp['boxes'])]):
    patch.set_facecolor(color)

ax5.set_xlabel('时间周期', fontsize=12)
ax5.set_ylabel('t_mfe (达到最大盈利的K线数)', fontsize=12)
ax5.set_title('最优退出时机分布', fontsize=14, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='y')

# ============================================================================
# 6. Win Rate and Trade Count
# ============================================================================
ax6 = plt.subplot(2, 3, 6)

win_rates = []
trade_counts = []

for tf in timeframes:
    if tf in data:
        df = data[tf]
        win_rate = (df['pnl_final'] > 0).sum() / len(df) * 100
        win_rates.append(win_rate)
        trade_counts.append(len(df))

ax6_twin = ax6.twinx()

# Bar chart for trade count
bars = ax6.bar(tf_names, trade_counts, alpha=0.6, color='steelblue', label='交易数量')
ax6.set_xlabel('时间周期', fontsize=12)
ax6.set_ylabel('交易数量', fontsize=12, color='steelblue')
ax6.tick_params(axis='y', labelcolor='steelblue')

# Line chart for win rate
line = ax6_twin.plot(tf_names, win_rates, 'ro-', linewidth=2, markersize=8, label='胜率')
ax6_twin.set_ylabel('胜率 (%)', fontsize=12, color='red')
ax6_twin.tick_params(axis='y', labelcolor='red')
ax6_twin.axhline(y=50, color='gray', linestyle='--', alpha=0.5)

ax6.set_title('交易数量 & 胜率', fontsize=14, fontweight='bold')

# Add value labels
for i, (bar, count, wr) in enumerate(zip(bars, trade_counts, win_rates)):
    ax6.text(bar.get_x() + bar.get_width()/2., count,
            f'{count}',
            ha='center', va='bottom', fontsize=9)
    ax6_twin.text(i, wr + 2, f'{wr:.1f}%',
                 ha='center', va='bottom', fontsize=9, color='red')

# Combine legends
lines1, labels1 = ax6.get_legend_handles_labels()
lines2, labels2 = ax6_twin.get_legend_handles_labels()
ax6.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

# ============================================================================
# Overall title and layout
# ============================================================================
fig.suptitle('XAUUSD 交易路径分析可视化报告', fontsize=18, fontweight='bold', y=0.995)
plt.tight_layout(rect=[0, 0, 1, 0.99])

# Save figure
output_path = 'results/xauusd_trade_path_visualization.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"\n图表已保存到: {output_path}")

plt.show()

