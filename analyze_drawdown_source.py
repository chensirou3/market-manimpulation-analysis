"""
分析BTC 30min Long-Only策略的最大回撤来源
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
print("分析BTC 30min Long-Only策略的最大回撤来源")
print("=" * 80)

# Load data
data_file = 'results/bars_30min_btc_full_with_manipscore.csv'
print(f"\n加载数据: {data_file}")
df = pd.read_csv(data_file)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp').sort_index()

print(f"数据范围: {df.index[0]} 至 {df.index[-1]}")
print(f"数据点数: {len(df)}")

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

# Compute trend strength if needed
if 'TS' not in df.columns:
    print("\n计算趋势强度...")
    df = compute_trend_strength(df, config.L_past, config.vol_window)

# Compute thresholds
print("\n计算阈值...")
thresholds = compute_extreme_trend_thresholds(df, quantile=config.q_extreme_trend)
T_trend = thresholds['threshold']
M_thresh = df['ManipScore'].quantile(config.q_manip)

print(f"趋势阈值: {T_trend:.4f}")
print(f"ManipScore阈值: {M_thresh:.4f}")

# Generate signals (Long-Only)
print("\n生成Long-Only信号...")
extreme_up = (
    (df['TS'] > T_trend) &
    (df['returns'] > 0) &
    (df['ManipScore'] > M_thresh)
)

extreme_down = (
    (df['TS'] < -T_trend) &
    (df['returns'] < 0) &
    (df['ManipScore'] > M_thresh)
)

signal_raw = pd.Series(0, index=df.index)
signal_raw[extreme_up] = -1  # Short on extreme up (reversal)
signal_raw[extreme_down] = +1  # Long on extreme down (reversal)

# Long-Only: remove shorts
signal_exec = signal_raw.shift(1).fillna(0)
signal_exec[signal_exec == -1] = 0

df['exec_signal'] = signal_exec

# Run backtest
print("\n运行回测...")
result = run_extreme_reversal_backtest(
    bars=df,
    exec_signals=signal_exec,
    config=config,
    initial_capital=10000.0
)

stats = result.stats
equity = result.equity_curve

print(f"\n回测结果:")
print(f"  总收益: {stats['total_return']*100:+.2f}%")
print(f"  Sharpe: {stats['sharpe_ratio']:.2f}")
print(f"  最大回撤: {stats['max_drawdown']*100:.2f}%")
print(f"  交易次数: {stats['n_trades']}")

# Calculate drawdown
cummax = equity.expanding().max()
drawdown = (equity - cummax) / cummax

# Find max drawdown period
max_dd_idx = drawdown.idxmin()
max_dd_value = drawdown.min()

# Find the peak before max drawdown
peak_idx = cummax[:max_dd_idx].idxmax()
peak_value = cummax[peak_idx]

print(f"\n最大回撤详情:")
print(f"  回撤幅度: {max_dd_value*100:.2f}%")
print(f"  峰值时间: {peak_idx}")
print(f"  峰值权益: ${peak_value:.2f}")
print(f"  谷底时间: {max_dd_idx}")
print(f"  谷底权益: ${equity[max_dd_idx]:.2f}")
print(f"  持续时间: {(max_dd_idx - peak_idx).days} 天")

# Analyze the drawdown period
dd_period = df.loc[peak_idx:max_dd_idx]
print(f"\n回撤期间市场表现:")
print(f"  起始价格: ${dd_period['close'].iloc[0]:.2f}")
print(f"  结束价格: ${dd_period['close'].iloc[-1]:.2f}")
print(f"  市场变化: {(dd_period['close'].iloc[-1] / dd_period['close'].iloc[0] - 1)*100:+.2f}%")
print(f"  数据点数: {len(dd_period)}")

# Analyze trades during drawdown period
# Convert peak_idx and max_dd_idx to tz-naive for comparison
peak_idx_naive = peak_idx.tz_localize(None) if hasattr(peak_idx, 'tz_localize') else peak_idx
max_dd_idx_naive = max_dd_idx.tz_localize(None) if hasattr(max_dd_idx, 'tz_localize') else max_dd_idx

trades_in_dd = []
for t in result.trades:
    if t.entry_time is not None:
        entry_ts = pd.Timestamp(t.entry_time)
        entry_ts_naive = entry_ts.tz_localize(None) if hasattr(entry_ts, 'tz') and entry_ts.tz is not None else entry_ts
        if peak_idx_naive <= entry_ts_naive <= max_dd_idx_naive:
            trades_in_dd.append(t)

print(f"\n回撤期间交易:")
print(f"  交易次数: {len(trades_in_dd)}")

pnls = []
if len(trades_in_dd) > 0:
    pnls = [t.pnl for t in trades_in_dd if t.pnl is not None]
    print(f"  总盈亏: ${sum(pnls):.2f}")
    print(f"  平均盈亏: ${np.mean(pnls):.2f}")
    print(f"  盈利次数: {sum(1 for p in pnls if p > 0)}")
    print(f"  亏损次数: {sum(1 for p in pnls if p < 0)}")
    print(f"  胜率: {sum(1 for p in pnls if p > 0) / len(pnls) * 100:.1f}%")

    # Exit reasons
    exit_reasons = [t.exit_reason for t in trades_in_dd if t.exit_reason is not None]
    if len(exit_reasons) > 0:
        exit_counts = pd.Series(exit_reasons).value_counts()
        print(f"\n  退出原因:")
        for reason, count in exit_counts.items():
            print(f"    {reason}: {count} ({count/len(trades_in_dd)*100:.1f}%)")

# Save detailed analysis
output_data = {
    'max_drawdown_pct': max_dd_value * 100,
    'peak_time': peak_idx,
    'trough_time': max_dd_idx,
    'duration_days': (max_dd_idx - peak_idx).days,
    'peak_equity': peak_value,
    'trough_equity': equity[max_dd_idx],
    'market_start_price': dd_period['close'].iloc[0],
    'market_end_price': dd_period['close'].iloc[-1],
    'market_change_pct': (dd_period['close'].iloc[-1] / dd_period['close'].iloc[0] - 1) * 100,
    'n_trades_in_dd': len(trades_in_dd),
    'total_pnl_in_dd': sum(pnls) if len(trades_in_dd) > 0 else 0,
}

# Save to file
output_file = 'results/btc_30min_drawdown_analysis.csv'
pd.DataFrame([output_data]).to_csv(output_file, index=False)
print(f"\n✅ 详细数据已保存到: {output_file}")

print("\n" + "=" * 80)
print("分析完成！")

