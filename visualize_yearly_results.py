"""
可视化年度回测结果
Visualize yearly backtest results
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('results/extreme_reversal_yearly_results.csv')

print("=" * 80)
print("年度回测结果可视化")
print("=" * 80)
print()
print(df.to_string(index=False))
print()

# 创建综合图表
fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. 年度收益柱状图
ax1 = fig.add_subplot(gs[0, :])
colors = ['green' if x > 0 else 'red' for x in df['total_return']]
bars = ax1.bar(df['year'], df['total_return'] * 100, color=colors, alpha=0.7, edgecolor='black')
ax1.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax1.set_xlabel('年份', fontsize=12)
ax1.set_ylabel('收益率 (%)', fontsize=12)
ax1.set_title('年度收益率', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}%',
            ha='center', va='bottom' if height > 0 else 'top',
            fontsize=9)

# 2. 胜率趋势
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(df['year'], df['win_rate'] * 100, marker='o', linewidth=2, markersize=8)
ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50%基准')
ax2.set_xlabel('年份', fontsize=12)
ax2.set_ylabel('胜率 (%)', fontsize=12)
ax2.set_title('年度胜率', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Sharpe比率
ax3 = fig.add_subplot(gs[1, 1])
colors_sharpe = ['green' if x > 0 else 'red' for x in df['sharpe_ratio']]
ax3.bar(df['year'], df['sharpe_ratio'], color=colors_sharpe, alpha=0.7, edgecolor='black')
ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax3.set_xlabel('年份', fontsize=12)
ax3.set_ylabel('Sharpe比率', fontsize=12)
ax3.set_title('年度Sharpe比率', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# 4. 信号数量
ax4 = fig.add_subplot(gs[1, 2])
ax4.bar(df['year'], df['n_signals'], alpha=0.7, color='blue', edgecolor='black')
ax4.set_xlabel('年份', fontsize=12)
ax4.set_ylabel('信号数量', fontsize=12)
ax4.set_title('年度信号数量', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

# 5. 盈亏比
ax5 = fig.add_subplot(gs[2, 0])
ax5.plot(df['year'], df['profit_factor'], marker='s', linewidth=2, markersize=8, color='purple')
ax5.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='盈亏平衡')
ax5.set_xlabel('年份', fontsize=12)
ax5.set_ylabel('盈亏比', fontsize=12)
ax5.set_title('年度盈亏比', fontsize=12, fontweight='bold')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. 信号率
ax6 = fig.add_subplot(gs[2, 1])
ax6.plot(df['year'], df['signal_rate'], marker='^', linewidth=2, markersize=8, color='orange')
ax6.set_xlabel('年份', fontsize=12)
ax6.set_ylabel('信号率 (%)', fontsize=12)
ax6.set_title('年度信号率', fontsize=12, fontweight='bold')
ax6.grid(True, alpha=0.3)

# 7. 做多vs做空
ax7 = fig.add_subplot(gs[2, 2])
x = np.arange(len(df))
width = 0.35
ax7.bar(x - width/2, df['n_long'], width, label='做多', alpha=0.7, color='green', edgecolor='black')
ax7.bar(x + width/2, df['n_short'], width, label='做空', alpha=0.7, color='red', edgecolor='black')
ax7.set_xlabel('年份', fontsize=12)
ax7.set_ylabel('信号数量', fontsize=12)
ax7.set_title('做多 vs 做空信号', fontsize=12, fontweight='bold')
ax7.set_xticks(x)
ax7.set_xticklabels(df['year'], rotation=45)
ax7.legend()
ax7.grid(True, alpha=0.3, axis='y')

plt.suptitle('极端反转策略 - 年度回测结果分析 (2015-2025)', 
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig('results/extreme_reversal_yearly_analysis.png', dpi=150, bbox_inches='tight')
print("✅ 年度分析图已保存: results/extreme_reversal_yearly_analysis.png")

# 创建相关性分析图
fig2, axes = plt.subplots(2, 2, figsize=(14, 10))

# 信号数 vs 收益
axes[0, 0].scatter(df['n_signals'], df['total_return'] * 100, s=100, alpha=0.6)
for i, year in enumerate(df['year']):
    axes[0, 0].annotate(str(year), (df['n_signals'].iloc[i], df['total_return'].iloc[i] * 100),
                       fontsize=9, ha='center')
axes[0, 0].set_xlabel('信号数量', fontsize=12)
axes[0, 0].set_ylabel('收益率 (%)', fontsize=12)
axes[0, 0].set_title('信号数量 vs 收益率', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# 胜率 vs 收益
axes[0, 1].scatter(df['win_rate'] * 100, df['total_return'] * 100, s=100, alpha=0.6, color='green')
for i, year in enumerate(df['year']):
    axes[0, 1].annotate(str(year), (df['win_rate'].iloc[i] * 100, df['total_return'].iloc[i] * 100),
                       fontsize=9, ha='center')
axes[0, 1].set_xlabel('胜率 (%)', fontsize=12)
axes[0, 1].set_ylabel('收益率 (%)', fontsize=12)
axes[0, 1].set_title('胜率 vs 收益率', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# 盈亏比 vs 收益
axes[1, 0].scatter(df['profit_factor'], df['total_return'] * 100, s=100, alpha=0.6, color='purple')
for i, year in enumerate(df['year']):
    axes[1, 0].annotate(str(year), (df['profit_factor'].iloc[i], df['total_return'].iloc[i] * 100),
                       fontsize=9, ha='center')
axes[1, 0].set_xlabel('盈亏比', fontsize=12)
axes[1, 0].set_ylabel('收益率 (%)', fontsize=12)
axes[1, 0].set_title('盈亏比 vs 收益率', fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# 信号率 vs 收益
axes[1, 1].scatter(df['signal_rate'], df['total_return'] * 100, s=100, alpha=0.6, color='orange')
for i, year in enumerate(df['year']):
    axes[1, 1].annotate(str(year), (df['signal_rate'].iloc[i], df['total_return'].iloc[i] * 100),
                       fontsize=9, ha='center')
axes[1, 1].set_xlabel('信号率 (%)', fontsize=12)
axes[1, 1].set_ylabel('收益率 (%)', fontsize=12)
axes[1, 1].set_title('信号率 vs 收益率', fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.suptitle('相关性分析', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('results/extreme_reversal_correlation_analysis.png', dpi=150, bbox_inches='tight')
print("✅ 相关性分析图已保存: results/extreme_reversal_correlation_analysis.png")

# 统计分析
print("\n" + "=" * 80)
print("统计分析")
print("=" * 80)
print()

print("📊 基本统计:")
print(f"  平均年收益: {df['total_return'].mean() * 100:.2f}%")
print(f"  收益标准差: {df['total_return'].std() * 100:.2f}%")
print(f"  最佳年份: {df.loc[df['total_return'].idxmax(), 'year']} ({df['total_return'].max() * 100:.2f}%)")
print(f"  最差年份: {df.loc[df['total_return'].idxmin(), 'year']} ({df['total_return'].min() * 100:.2f}%)")
print(f"  盈利年份: {(df['total_return'] > 0).sum()}/{len(df)} ({(df['total_return'] > 0).sum()/len(df)*100:.1f}%)")
print()

print("📈 相关性分析:")
print(f"  信号数 vs 收益: {df['n_signals'].corr(df['total_return']):.3f}")
print(f"  胜率 vs 收益: {df['win_rate'].corr(df['total_return']):.3f}")
print(f"  盈亏比 vs 收益: {df['profit_factor'].corr(df['total_return']):.3f}")
print(f"  信号率 vs 收益: {df['signal_rate'].corr(df['total_return']):.3f}")
print()

plt.show()

