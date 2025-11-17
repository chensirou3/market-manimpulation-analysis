# -*- coding: utf-8 -*-
"""
Test the fixed static SL/TP backtest
"""

import pandas as pd
from src.backtest.static_exit_backtest import StaticExitConfig, run_static_exit_backtest, compute_atr
from src.strategies.extreme_reversal import ExtremeReversalConfig, generate_extreme_reversal_signals

# Load BTC 4H data
bars = pd.read_csv('results/bars_4h_btc_full_with_manipscore.csv', parse_dates=['timestamp'])
bars = bars.set_index('timestamp')

# Compute ATR
atr = compute_atr(bars, window=10)

# Generate signals
strategy_config = ExtremeReversalConfig(
    bar_size="4h",
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9,
    use_normalized_trend=True
)

df_with_signals = generate_extreme_reversal_signals(
    bars,
    strategy_config,
    return_col='returns',
    manip_col='ManipScore'
)

signal_exec = (df_with_signals['exec_signal'] == 1).astype(int)
print(f"Total signals: {signal_exec.sum()}")

# Run with best config from before
config = StaticExitConfig(
    bar_size="4h",
    sl_atr_mult=3.0,
    tp_atr_mult=1.0,
    max_holding_bars=10,
    cost_per_trade=0.0007
)

result = run_static_exit_backtest(bars, signal_exec, atr, config)

print(f"\nBacktest Results:")
print(f"Trades: {len(result['trades'])}")
print(f"Total Return: {result['stats']['total_return']:.2%}")
print(f"Sharpe: {result['stats']['sharpe']:.2f}")
print(f"Win Rate: {result['stats']['win_rate']:.1%}")
print(f"Avg PnL per trade: {result['stats']['avg_pnl_per_trade']:.2%}")

print(f"\nExit Reason Breakdown:")
trades_df = result['trades']
print(trades_df['exit_reason'].value_counts())

print(f"\nFirst 10 trades:")
print(trades_df[['entry_time', 'exit_time', 'holding_bars', 'pnl_pct', 'exit_reason']].head(10))

# Compare with trade path analysis
df_tp = pd.read_csv('results/btc_4h_trade_path_analysis.csv')
print(f"\n\nTrade Path Analysis:")
print(f"Trades: {len(df_tp)}")
print(f"Exit reasons:")
print(df_tp['exit_reason'].value_counts())

