"""
对已处理的数据进行回测
Backtest on processed data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.backtest.interfaces import apply_manipulation_filter, calculate_performance_metrics

print("=" * 80)
print("回测分析 - 基于ManipScore过滤")
print("Backtest Analysis - ManipScore Filtering")
print("=" * 80)
print()

# 简单的MA交叉策略
def simple_ma_strategy(bars, fast=10, slow=30):
    """简单移动平均交叉策略"""
    fast_ma = bars['close'].rolling(window=fast).mean()
    slow_ma = bars['close'].rolling(window=slow).mean()
    
    signals = pd.Series(0, index=bars.index)
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma < slow_ma] = -1
    
    return signals

# 计算性能指标
def calc_metrics(returns, signals):
    """计算策略性能指标"""
    strategy_returns = signals.shift(1) * returns
    strategy_returns = strategy_returns.dropna()
    
    if len(strategy_returns) == 0:
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'n_trades': 0
        }
    
    # 总收益
    total_return = (1 + strategy_returns).prod() - 1
    
    # Sharpe比率 (假设252个交易日，每天288个5分钟K线)
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(288 * 252) if strategy_returns.std() > 0 else 0
    
    # 最大回撤
    cum_returns = (1 + strategy_returns).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_dd = drawdown.min()
    
    # 胜率
    wins = (strategy_returns > 0).sum()
    total = (strategy_returns != 0).sum()
    win_rate = wins / total if total > 0 else 0
    
    # 交易次数
    n_trades = (signals.diff() != 0).sum()
    
    return {
        'total_return': total_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'n_trades': n_trades
    }

# 选择几个代表性的年份进行回测
test_years = ['2020', '2022', '2024']
results_dir = Path('results')

all_backtest_results = []

for year in test_years:
    print(f"\n{'='*80}")
    print(f"回测 {year} 年")
    print(f"{'='*80}")
    
    # 找到该年份的所有季度文件
    year_files = sorted(results_dir.glob(f'bars_with_manipscore_{year}-*.csv'))
    
    if not year_files:
        print(f"⚠️ 未找到 {year} 年的数据")
        continue
    
    print(f"找到 {len(year_files)} 个季度文件")
    
    # 合并该年所有数据
    dfs = []
    for f in year_files:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()
    
    print(f"总K线数: {len(bars):,}")
    print(f"时间范围: {bars.index[0]} 到 {bars.index[-1]}")
    
    # 计算收益率
    bars['returns'] = bars['close'].pct_change()
    
    # 生成策略信号
    print("\n生成策略信号 (MA 10/30)...")
    signals_raw = simple_ma_strategy(bars, fast=10, slow=30)
    
    # 应用不同的ManipScore过滤
    thresholds = [0.5, 0.7, 0.9]
    
    print("\n回测结果:")
    print("-" * 80)
    
    # 原始策略（无过滤）
    metrics_raw = calc_metrics(bars['returns'], signals_raw)
    print(f"\n原始策略 (无过滤):")
    print(f"  总收益: {metrics_raw['total_return']:>8.2%}")
    print(f"  Sharpe: {metrics_raw['sharpe_ratio']:>8.2f}")
    print(f"  最大回撤: {metrics_raw['max_drawdown']:>8.2%}")
    print(f"  胜率: {metrics_raw['win_rate']:>8.2%}")
    print(f"  交易次数: {metrics_raw['n_trades']:>8}")
    
    year_results = {
        'year': year,
        'n_bars': len(bars),
        'raw_return': metrics_raw['total_return'],
        'raw_sharpe': metrics_raw['sharpe_ratio'],
        'raw_drawdown': metrics_raw['max_drawdown'],
        'raw_winrate': metrics_raw['win_rate'],
        'raw_trades': metrics_raw['n_trades']
    }
    
    # 不同阈值的过滤策略
    for threshold in thresholds:
        # 过滤信号：ManipScore > threshold 时设为0
        signals_filtered = signals_raw.copy()
        signals_filtered[bars['manip_score'] > threshold] = 0
        
        metrics_filtered = calc_metrics(bars['returns'], signals_filtered)
        
        filtered_count = (bars['manip_score'] > threshold).sum()
        filter_rate = filtered_count / len(bars) * 100
        
        print(f"\n过滤策略 (阈值={threshold}):")
        print(f"  过滤K线: {filtered_count:>8} ({filter_rate:>5.2f}%)")
        print(f"  总收益: {metrics_filtered['total_return']:>8.2%} (变化: {(metrics_filtered['total_return']-metrics_raw['total_return'])*100:+.2f}%)")
        print(f"  Sharpe: {metrics_filtered['sharpe_ratio']:>8.2f} (变化: {metrics_filtered['sharpe_ratio']-metrics_raw['sharpe_ratio']:+.2f})")
        print(f"  最大回撤: {metrics_filtered['max_drawdown']:>8.2%} (变化: {(metrics_filtered['max_drawdown']-metrics_raw['max_drawdown'])*100:+.2f}%)")
        print(f"  胜率: {metrics_filtered['win_rate']:>8.2%} (变化: {(metrics_filtered['win_rate']-metrics_raw['win_rate'])*100:+.2f}%)")
        print(f"  交易次数: {metrics_filtered['n_trades']:>8} (变化: {metrics_filtered['n_trades']-metrics_raw['n_trades']:+})")
        
        year_results[f'filtered_{threshold}_return'] = metrics_filtered['total_return']
        year_results[f'filtered_{threshold}_sharpe'] = metrics_filtered['sharpe_ratio']
        year_results[f'filtered_{threshold}_filter_rate'] = filter_rate
    
    all_backtest_results.append(year_results)

# 汇总结果
print(f"\n\n{'='*80}")
print("回测汇总")
print(f"{'='*80}\n")

summary_df = pd.DataFrame(all_backtest_results)
print(summary_df.to_string(index=False))

# 保存结果
output_file = 'results/backtest_summary.csv'
summary_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✅ 回测结果已保存: {output_file}")

print(f"\n{'='*80}")
print("🎉 回测完成！")
print(f"{'='*80}")

