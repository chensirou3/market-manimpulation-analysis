"""
分析排除最大回撤期间后的策略表现
"""

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sys.path.append('market-manimpulation-analysis')
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import (
    compute_trend_strength,
    compute_extreme_trend_thresholds
)

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("分析排除最大回撤期间后的BTC 30min Long-Only策略表现")
print("=" * 80)

# Load data
data_file = 'results/bars_30min_btc_full_with_manipscore.csv'
print(f"\n加载数据: {data_file}")
df = pd.read_csv(data_file)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()

print(f"完整数据范围: {df.index[0]} 至 {df.index[-1]}")
print(f"完整数据点数: {len(df)}")

# Define drawdown period to exclude
dd_start = pd.Timestamp('2019-08-15', tz='UTC')
dd_end = pd.Timestamp('2020-03-13', tz='UTC')

print(f"\n排除回撤期间: {dd_start} 至 {dd_end}")

# Split data into periods
period1 = df[df.index < dd_start].copy()  # Before drawdown
period2 = df[df.index > dd_end].copy()    # After drawdown

print(f"\n期间1 (回撤前): {period1.index[0]} 至 {period1.index[-1]}")
print(f"  数据点数: {len(period1)}")

print(f"\n期间2 (回撤后): {period2.index[0]} 至 {period2.index[-1]}")
print(f"  数据点数: {len(period2)}")

# Create config
config = ExtremeReversalConfig(
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9,
    holding_horizon=5,
    atr_window=10,
    sl_atr_mult=0.5,
    tp_atr_mult=0.8,
    cost_per_trade=0.0007
)

def run_backtest_on_period(df_period, period_name):
    """Run backtest on a specific period"""
    print(f"\n{'='*60}")
    print(f"回测 {period_name}")
    print(f"{'='*60}")
    
    # Compute trend strength if needed
    if 'TS' not in df_period.columns:
        df_period = compute_trend_strength(df_period, config.L_past, config.vol_window)
    
    # Compute thresholds
    thresholds = compute_extreme_trend_thresholds(df_period, quantile=config.q_extreme_trend)
    T_trend = thresholds['threshold']
    M_thresh = df_period['ManipScore'].quantile(config.q_manip)
    
    # Generate signals (Long-Only)
    extreme_up = (
        (df_period['TS'] > T_trend) &
        (df_period['returns'] > 0) &
        (df_period['ManipScore'] > M_thresh)
    )
    
    extreme_down = (
        (df_period['TS'] < -T_trend) &
        (df_period['returns'] < 0) &
        (df_period['ManipScore'] > M_thresh)
    )
    
    signal_raw = pd.Series(0, index=df_period.index)
    signal_raw[extreme_up] = -1
    signal_raw[extreme_down] = +1
    
    # Long-Only: remove shorts
    signal_exec = signal_raw.shift(1).fillna(0)
    signal_exec[signal_exec == -1] = 0
    
    df_period['exec_signal'] = signal_exec
    
    # Run backtest
    result = run_extreme_reversal_backtest(
        bars=df_period,
        exec_signals=signal_exec,
        config=config,
        initial_capital=10000.0
    )
    
    stats = result.stats
    
    print(f"\n回测结果:")
    print(f"  总收益: {stats['total_return']*100:+.2f}%")
    print(f"  年化收益: {stats['annualized_return']*100:+.2f}%")
    print(f"  Sharpe: {stats['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {stats['max_drawdown']*100:.2f}%")
    print(f"  胜率: {stats['win_rate']*100:.1f}%")
    print(f"  交易次数: {stats['n_trades']}")
    print(f"  盈亏比: {stats.get('profit_factor', 0):.2f}")
    
    # Market performance
    market_return = (df_period['close'].iloc[-1] / df_period['close'].iloc[0] - 1) * 100
    print(f"\n市场表现:")
    print(f"  起始价格: ${df_period['close'].iloc[0]:.2f}")
    print(f"  结束价格: ${df_period['close'].iloc[-1]:.2f}")
    print(f"  市场收益: {market_return:+.2f}%")
    
    return result, stats

# Run backtests
result1, stats1 = run_backtest_on_period(period1, "期间1 (回撤前)")
result2, stats2 = run_backtest_on_period(period2, "期间2 (回撤后)")

# Combined analysis (excluding drawdown period)
print(f"\n{'='*80}")
print("排除回撤期间后的整体表现")
print(f"{'='*80}")

# Calculate combined metrics
total_days_1 = (period1.index[-1] - period1.index[0]).days
total_days_2 = (period2.index[-1] - period2.index[0]).days
total_days_combined = total_days_1 + total_days_2

print(f"\n时间统计:")
print(f"  期间1天数: {total_days_1} 天")
print(f"  期间2天数: {total_days_2} 天")
print(f"  合计天数: {total_days_combined} 天 ({total_days_combined/365:.1f} 年)")
print(f"  排除天数: {(dd_end - dd_start).days} 天")

# Combined return (assuming we reinvest)
final_capital_1 = 10000 * (1 + stats1['total_return'])
final_capital_2 = final_capital_1 * (1 + stats2['total_return'])
combined_return = (final_capital_2 / 10000 - 1) * 100

print(f"\n收益统计:")
print(f"  期间1收益: {stats1['total_return']*100:+.2f}%")
print(f"  期间2收益: {stats2['total_return']*100:+.2f}%")
print(f"  合计收益: {combined_return:+.2f}%")
print(f"  年化收益: {(final_capital_2/10000)**(365/total_days_combined) - 1:+.2%}")

# Combined Sharpe (weighted average)
combined_sharpe = (stats1['sharpe_ratio'] * total_days_1 + stats2['sharpe_ratio'] * total_days_2) / total_days_combined
print(f"\n风险指标:")
print(f"  期间1 Sharpe: {stats1['sharpe_ratio']:.2f}")
print(f"  期间2 Sharpe: {stats2['sharpe_ratio']:.2f}")
print(f"  加权平均Sharpe: {combined_sharpe:.2f}")

# Max drawdown (worst of the two periods)
combined_max_dd = min(stats1['max_drawdown'], stats2['max_drawdown']) * 100
print(f"  期间1最大回撤: {stats1['max_drawdown']*100:.2f}%")
print(f"  期间2最大回撤: {stats2['max_drawdown']*100:.2f}%")
print(f"  排除后最大回撤: {combined_max_dd:.2f}%")

# Trading stats
total_trades = stats1['n_trades'] + stats2['n_trades']
combined_win_rate = (stats1['win_rate'] * stats1['n_trades'] + stats2['win_rate'] * stats2['n_trades']) / total_trades
print(f"\n交易统计:")
print(f"  期间1交易: {stats1['n_trades']} 笔")
print(f"  期间2交易: {stats2['n_trades']} 笔")
print(f"  合计交易: {total_trades} 笔")
print(f"  加权平均胜率: {combined_win_rate*100:.1f}%")

print(f"\n{'='*80}")
print("✅ 分析完成！")

