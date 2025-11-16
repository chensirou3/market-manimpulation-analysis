"""
可视化BTC熊市期间策略表现
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Load data
results_dir = Path('results')
df = pd.read_csv(results_dir / 'btc_bear_market_2021_2023_analysis.csv')

# Create figure with subplots
fig = plt.figure(figsize=(20, 12))

# 1. Total Return by Strategy and Timeframe
ax1 = plt.subplot(2, 3, 1)
pivot_return = df.pivot(index='timeframe', columns='strategy', values='total_return')
pivot_return = pivot_return.reindex(['5min', '15min', '30min', '60min', '4h', '1d'])
pivot_return.plot(kind='bar', ax=ax1, width=0.8)
ax1.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax1.axhline(y=44.2, color='red', linestyle='--', linewidth=1, label='Market Return')
ax1.set_title('Total Return by Strategy (2021-2023 Bear Market)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Timeframe', fontsize=12)
ax1.set_ylabel('Total Return (%)', fontsize=12)
ax1.legend(title='Strategy', fontsize=10)
ax1.grid(True, alpha=0.3)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

# 2. Sharpe Ratio by Strategy and Timeframe
ax2 = plt.subplot(2, 3, 2)
pivot_sharpe = df.pivot(index='timeframe', columns='strategy', values='sharpe_ratio')
pivot_sharpe = pivot_sharpe.reindex(['5min', '15min', '30min', '60min', '4h', '1d'])
pivot_sharpe.plot(kind='bar', ax=ax2, width=0.8)
ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax2.set_title('Sharpe Ratio by Strategy', fontsize=14, fontweight='bold')
ax2.set_xlabel('Timeframe', fontsize=12)
ax2.set_ylabel('Sharpe Ratio', fontsize=12)
ax2.legend(title='Strategy', fontsize=10)
ax2.grid(True, alpha=0.3)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

# 3. Win Rate by Strategy and Timeframe
ax3 = plt.subplot(2, 3, 3)
pivot_winrate = df.pivot(index='timeframe', columns='strategy', values='win_rate')
pivot_winrate = pivot_winrate.reindex(['5min', '15min', '30min', '60min', '4h', '1d'])
pivot_winrate.plot(kind='bar', ax=ax3, width=0.8)
ax3.axhline(y=50, color='black', linestyle='--', linewidth=1, label='50% Baseline')
ax3.set_title('Win Rate by Strategy', fontsize=14, fontweight='bold')
ax3.set_xlabel('Timeframe', fontsize=12)
ax3.set_ylabel('Win Rate (%)', fontsize=12)
ax3.legend(title='Strategy', fontsize=10)
ax3.grid(True, alpha=0.3)
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 4. Max Drawdown by Strategy and Timeframe
ax4 = plt.subplot(2, 3, 4)
pivot_dd = df.pivot(index='timeframe', columns='strategy', values='max_drawdown')
pivot_dd = pivot_dd.reindex(['5min', '15min', '30min', '60min', '4h', '1d'])
pivot_dd.plot(kind='bar', ax=ax4, width=0.8)
ax4.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax4.set_title('Max Drawdown by Strategy', fontsize=14, fontweight='bold')
ax4.set_xlabel('Timeframe', fontsize=12)
ax4.set_ylabel('Max Drawdown (%)', fontsize=12)
ax4.legend(title='Strategy', fontsize=10)
ax4.grid(True, alpha=0.3)
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

# 5. Number of Trades by Strategy and Timeframe
ax5 = plt.subplot(2, 3, 5)
pivot_trades = df.pivot(index='timeframe', columns='strategy', values='n_trades')
pivot_trades = pivot_trades.reindex(['5min', '15min', '30min', '60min', '4h', '1d'])
pivot_trades.plot(kind='bar', ax=ax5, width=0.8)
ax5.set_title('Number of Trades by Strategy', fontsize=14, fontweight='bold')
ax5.set_xlabel('Timeframe', fontsize=12)
ax5.set_ylabel('Number of Trades', fontsize=12)
ax5.legend(title='Strategy', fontsize=10)
ax5.grid(True, alpha=0.3)
plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45)

# 6. Return vs Sharpe Scatter
ax6 = plt.subplot(2, 3, 6)
for strategy in df['strategy'].unique():
    strategy_data = df[df['strategy'] == strategy]
    ax6.scatter(strategy_data['sharpe_ratio'], strategy_data['total_return'], 
               label=strategy, s=100, alpha=0.7)
    
    # Add timeframe labels
    for idx, row in strategy_data.iterrows():
        ax6.annotate(row['timeframe'], 
                    (row['sharpe_ratio'], row['total_return']),
                    fontsize=8, alpha=0.7)

ax6.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax6.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax6.axhline(y=44.2, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Market Return')
ax6.set_title('Return vs Sharpe Ratio', fontsize=14, fontweight='bold')
ax6.set_xlabel('Sharpe Ratio', fontsize=12)
ax6.set_ylabel('Total Return (%)', fontsize=12)
ax6.legend(fontsize=10)
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(results_dir / 'btc_bear_market_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 图表已保存到: {results_dir / 'btc_bear_market_analysis.png'}")

# Create summary statistics table
print("\n" + "="*80)
print("BTC熊市期间策略表现总结 (2021-2023)")
print("="*80)

for strategy in ['long_only', 'symmetric', 'short_only']:
    strategy_data = df[df['strategy'] == strategy]
    
    print(f"\n{strategy.upper()} 策略:")
    print(f"  平均收益: {strategy_data['total_return'].mean():+.2f}%")
    print(f"  平均Sharpe: {strategy_data['sharpe_ratio'].mean():.2f}")
    print(f"  平均胜率: {strategy_data['win_rate'].mean():.1f}%")
    print(f"  总交易次数: {strategy_data['n_trades'].sum()}")
    print(f"  平均回撤: {strategy_data['max_drawdown'].mean():.2f}%")
    
    # Best timeframe
    best_idx = strategy_data['sharpe_ratio'].idxmax()
    if pd.notna(best_idx):
        best = strategy_data.loc[best_idx]
        print(f"  最佳时间周期: {best['timeframe']} (Sharpe {best['sharpe_ratio']:.2f}, Return {best['total_return']:+.2f}%)")

print(f"\n市场收益: +44.20%")
print(f"Long-Only平均: {df[df['strategy']=='long_only']['total_return'].mean():+.2f}%")
print(f"Short-Only平均: {df[df['strategy']=='short_only']['total_return'].mean():+.2f}%")
print(f"Symmetric平均: {df[df['strategy']=='symmetric']['total_return'].mean():+.2f}%")

print("\n" + "="*80)
print("✅ 可视化完成！")

