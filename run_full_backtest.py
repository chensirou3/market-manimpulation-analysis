"""
完整回测分析 - 所有年份
Full backtest analysis - All years
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("完整回测分析 (2015-2025)")
print("Full Backtest Analysis (2015-2025)")
print("=" * 80)
print()

def simple_ma_strategy(bars, fast=10, slow=30):
    """简单移动平均交叉策略"""
    fast_ma = bars['close'].rolling(window=fast).mean()
    slow_ma = bars['close'].rolling(window=slow).mean()
    signals = pd.Series(0, index=bars.index)
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma < slow_ma] = -1
    return signals

def calc_metrics(returns, signals):
    """计算策略性能指标"""
    strategy_returns = signals.shift(1) * returns
    strategy_returns = strategy_returns.dropna()
    
    if len(strategy_returns) == 0:
        return {'total_return': 0, 'sharpe_ratio': 0, 'max_drawdown': 0, 'win_rate': 0, 'n_trades': 0}
    
    total_return = (1 + strategy_returns).prod() - 1
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(288 * 252) if strategy_returns.std() > 0 else 0
    
    cum_returns = (1 + strategy_returns).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    wins = (strategy_returns > 0).sum()
    total = (strategy_returns != 0).sum()
    win_rate = wins / total if total > 0 else 0
    n_trades = (signals.diff() != 0).sum()
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': n_trades
    }

results_dir = Path('results')
all_years = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']
all_results = []

for year in all_years:
    print(f"处理 {year} 年...")
    
    year_files = sorted(results_dir.glob(f'bars_with_manipscore_{year}-*.csv'))
    if not year_files:
        continue
    
    dfs = [pd.read_csv(f, index_col=0, parse_dates=True) for f in year_files]
    bars = pd.concat(dfs, axis=0).sort_index()
    bars['returns'] = bars['close'].pct_change()
    
    signals_raw = simple_ma_strategy(bars, fast=10, slow=30)
    metrics_raw = calc_metrics(bars['returns'], signals_raw)
    
    # 测试阈值0.7
    signals_filtered = signals_raw.copy()
    signals_filtered[bars['manip_score'] > 0.7] = 0
    metrics_filtered = calc_metrics(bars['returns'], signals_filtered)
    
    filter_rate = (bars['manip_score'] > 0.7).sum() / len(bars) * 100
    
    all_results.append({
        'year': year,
        'n_bars': len(bars),
        'filter_rate': filter_rate,
        'raw_return': metrics_raw['total_return'],
        'raw_sharpe': metrics_raw['sharpe_ratio'],
        'raw_drawdown': metrics_raw['max_drawdown'],
        'filtered_return': metrics_filtered['total_return'],
        'filtered_sharpe': metrics_filtered['sharpe_ratio'],
        'filtered_drawdown': metrics_filtered['max_drawdown'],
        'return_diff': metrics_filtered['total_return'] - metrics_raw['total_return'],
        'sharpe_diff': metrics_filtered['sharpe_ratio'] - metrics_raw['sharpe_ratio']
    })

df = pd.DataFrame(all_results)

print("\n" + "=" * 80)
print("回测结果汇总 (阈值=0.7)")
print("=" * 80)
print()

print(f"{'年份':<6} {'K线数':>8} {'过滤率':>8} {'原始收益':>10} {'过滤收益':>10} {'收益差':>10} {'原始Sharpe':>12} {'过滤Sharpe':>12}")
print("-" * 80)

for _, row in df.iterrows():
    print(f"{row['year']:<6} {row['n_bars']:>8,} {row['filter_rate']:>7.2f}% "
          f"{row['raw_return']:>9.2%} {row['filtered_return']:>9.2%} {row['return_diff']:>9.2%} "
          f"{row['raw_sharpe']:>11.2f} {row['filtered_sharpe']:>11.2f}")

print()
print("=" * 80)
print("统计汇总")
print("=" * 80)

# 计算改善/恶化的年份数
improved_return = (df['return_diff'] > 0).sum()
improved_sharpe = (df['sharpe_diff'] > 0).sum()

print(f"\n收益改善年份: {improved_return}/{len(df)} ({improved_return/len(df)*100:.1f}%)")
print(f"Sharpe改善年份: {improved_sharpe}/{len(df)} ({improved_sharpe/len(df)*100:.1f}%)")
print(f"\n平均收益差: {df['return_diff'].mean():+.2%}")
print(f"平均Sharpe差: {df['sharpe_diff'].mean():+.2f}")
print(f"\n总体原始收益: {df['raw_return'].sum():.2%}")
print(f"总体过滤收益: {df['filtered_return'].sum():.2%}")

# 保存
output_file = 'results/full_backtest_results.csv'
df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✅ 结果已保存: {output_file}")

print("\n" + "=" * 80)
print("🎉 完整回测完成！")
print("=" * 80)

