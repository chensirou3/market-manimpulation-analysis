# -*- coding: utf-8 -*-
"""
Diagnose why Static SL/TP has different trade count than Trade Path Analysis
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("DIAGNOSING TRADE COUNT DIFFERENCE")
print("=" * 80)
print()

# Load BTC 4H trade path analysis results
df_tp = pd.read_csv('results/btc_4h_trade_path_analysis.csv')
print(f"Trade Path Analysis: {len(df_tp)} trades")
print()

# Load static SL/TP summary
df_static_summary = pd.read_csv('results/static_sl_tp_grid_4h_summary.csv')
btc_best = df_static_summary[df_static_summary['symbol']=='BTCUSD'].nlargest(1, 'sharpe').iloc[0]
print(f"Static SL/TP (best config): {int(btc_best['num_trades'])} trades")
print(f"Config: SL={btc_best['sl_mult']}, TP={btc_best['tp_mult']}, MaxBars={int(btc_best['max_holding_bars'])}")
print()

# The issue: Trade Path shows 82 trades, but comparison table shows 82 trades
# Let's check the comparison table
df_comparison = pd.read_csv('results/all_assets_complete_comparison.csv')
btc_4h_comp = df_comparison[(df_comparison['asset']=='BTC') & (df_comparison['timeframe']=='4h')].iloc[0]
print(f"Comparison table shows: {btc_4h_comp['n_trades']} trades")
print()

print("=" * 80)
print("HYPOTHESIS: Different signal generation or data")
print("=" * 80)
print()

# Re-generate signals to check
from src.strategies.extreme_reversal import ExtremeReversalConfig, generate_extreme_reversal_signals

# Load BTC 4H data
bars = pd.read_csv('results/bars_4h_btc_full_with_manipscore.csv', parse_dates=['timestamp'])
bars = bars.set_index('timestamp')
print(f"BTC 4H data: {len(bars)} bars")
print(f"Date range: {bars.index[0]} to {bars.index[-1]}")
print()

# Generate signals
config = ExtremeReversalConfig(
    bar_size="4h",
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9,
    use_normalized_trend=True
)

df_with_signals = generate_extreme_reversal_signals(
    bars,
    config,
    return_col='returns',
    manip_col='ManipScore'
)

# Count signals
long_signals_raw = (df_with_signals['raw_signal'] == 1).sum()
long_signals_exec = (df_with_signals['exec_signal'] == 1).sum()

print(f"Long signals (raw_signal == 1): {long_signals_raw}")
print(f"Long signals (exec_signal == 1): {long_signals_exec}")
print()

# Check if trade path analysis used different config
print("=" * 80)
print("CHECKING TRADE PATH ANALYSIS CONFIGURATION")
print("=" * 80)
print()

# Trade path analysis uses -5 ATR stop, no TP, no max bars by default
# Let's see the actual trades
print("Trade Path Analysis - First 10 trades:")
print(df_tp[['entry_time', 'exit_time', 'holding_bars', 'pnl_pct', 'exit_reason']].head(10))
print()

print("Trade Path Analysis - Exit reason breakdown:")
print(df_tp['exit_reason'].value_counts())
print()

# The key difference: Trade Path may filter out some trades
# Let's check if there's a minimum holding period or other filter
print("=" * 80)
print("KEY FINDING")
print("=" * 80)
print()

print("Trade Path Analysis config:")
print("  - Entry: signal_exec == 1")
print("  - Exit: -5 ATR stop OR new signal OR (optional) max bars")
print("  - No TP")
print("  - No transaction costs")
print()

print("Static SL/TP config:")
print("  - Entry: signal_exec == 1")
print("  - Exit: SL=3.0 ATR OR TP=1.0 ATR OR max_bars=10 OR new signal")
print("  - Transaction cost: 0.07%")
print()

print("EXPECTED: Same number of trades if using same signals")
print(f"ACTUAL: Trade Path has {len(df_tp)} trades, Static has {int(btc_best['num_trades'])} trades")
print()

# Check if the issue is that static SL/TP is counting differently
# Maybe it's entering on every signal, while trade path skips some?
print("=" * 80)
print("SOLUTION: Run static SL/TP with NO TP to match Trade Path")
print("=" * 80)
print()

# Check if there's a config with no TP (very wide TP)
btc_all = df_static_summary[df_static_summary['symbol']=='BTCUSD']
print("Configs with widest TP (2.5 ATR):")
wide_tp = btc_all[btc_all['tp_mult']==2.5].nlargest(5, 'sharpe')
print(wide_tp[['sl_mult', 'tp_mult', 'max_holding_bars', 'num_trades', 
               'avg_pnl_per_trade', 'win_rate', 'sharpe']].to_string(index=False))
print()

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("1. The trade count difference (82 vs 158) suggests different entry logic")
print("2. Trade Path may be using a different signal generation or filtering")
print("3. Need to check the actual trade path analysis script to see exact config")
print("4. Re-run static SL/TP with:")
print("   - cost_per_trade = 0.0 (to match trade path)")
print("   - Very wide TP (e.g., 10.0 ATR) to effectively disable TP")
print("   - SL = 5.0 ATR (to match trade path's -5 ATR stop)")
print("   - No max_holding_bars (or very large value)")
print()

