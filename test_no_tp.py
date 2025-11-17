# -*- coding: utf-8 -*-
"""
Test with NO TP (very wide TP) to match Trade Path Analysis
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

# Test with NO TP (very wide TP=100 ATR), SL=5 ATR, no max bars
config = StaticExitConfig(
    bar_size="4h",
    sl_atr_mult=5.0,  # Match trade path's -5 ATR stop
    tp_atr_mult=100.0,  # Effectively no TP
    max_holding_bars=10000,  # Effectively no max bars
    cost_per_trade=0.0  # No cost to match trade path
)

result = run_static_exit_backtest(bars, signal_exec, atr, config)

print(f"\nBacktest Results (NO TP, SL=5 ATR, NO cost):")
print(f"Trades: {len(result['trades'])}")
print(f"Total Return: {result['stats']['total_return']:.2%}")
print(f"Sharpe: {result['stats']['sharpe']:.2f}")
print(f"Win Rate: {result['stats']['win_rate']:.1%}")
print(f"Avg PnL per trade: {result['stats']['avg_pnl_per_trade']:.2%}")

print(f"\nExit Reason Breakdown:")
trades_df = result['trades']
print(trades_df['exit_reason'].value_counts())

# Compare with trade path analysis
df_tp = pd.read_csv('results/btc_4h_trade_path_analysis.csv')
print(f"\n\nTrade Path Analysis:")
print(f"Trades: {len(df_tp)}")
print(f"Avg PnL: {df_tp['pnl_final'].mean():.2%}")
print(f"Exit reasons:")
print(df_tp['exit_reason'].value_counts())

print(f"\n\nCOMPARISON:")
print(f"Trade count: {len(result['trades'])} vs {len(df_tp)} (should be equal!)")
print(f"NEW_SIGNAL exits: {(trades_df['exit_reason']=='NEW_SIGNAL').sum()} vs {(df_tp['exit_reason']=='NEW_SIGNAL').sum()}")

