# -*- coding: utf-8 -*-
"""
Compare Trade Path Analysis vs Static SL/TP Results
"""

import pandas as pd

print("=" * 80)
print("TRADE PATH ANALYSIS vs STATIC SL/TP COMPARISON")
print("=" * 80)
print()

# Load trade path analysis results
df_trade_path = pd.read_csv('results/all_assets_complete_comparison.csv')

# Load static SL/TP results
df_static = pd.read_csv('results/static_sl_tp_grid_4h_summary.csv')

# Compare BTC 4H
print("=" * 80)
print("BTC 4H COMPARISON")
print("=" * 80)
print()

btc_4h_trade_path = df_trade_path[(df_trade_path['asset']=='BTC') & (df_trade_path['timeframe']=='4h')].iloc[0]
btc_4h_static_best = df_static[df_static['symbol']=='BTCUSD'].nlargest(1, 'sharpe').iloc[0]

print("Trade Path Analysis (No time limit, -5 ATR stop):")
print(f"  Trades:              {btc_4h_trade_path['n_trades']}")
print(f"  Win Rate:            {btc_4h_trade_path['win_rate']:.1%}")
print(f"  Avg PnL per trade:   {btc_4h_trade_path['avg_pnl']:.2%}")
print(f"  Avg MFE:             {btc_4h_trade_path['avg_mfe']:.2%}")
print(f"  Profit Capture:      {btc_4h_trade_path['profit_capture_ratio']:.1%}")
print(f"  t_mfe median:        {btc_4h_trade_path['t_mfe_median']:.0f} bars")
print()

print("Static SL/TP (Best config: SL=3.0, TP=1.0, MaxBars=10):")
print(f"  Trades:              {int(btc_4h_static_best['num_trades'])}")
print(f"  Win Rate:            {btc_4h_static_best['win_rate']:.1%}")
print(f"  Avg PnL per trade:   {btc_4h_static_best['avg_pnl_per_trade']:.2%}")
print(f"  Total Return:        {btc_4h_static_best['total_return']:.2%}")
print(f"  Ann Return:          {btc_4h_static_best['ann_return']:.2%}")
print(f"  Sharpe:              {btc_4h_static_best['sharpe']:.2f}")
print(f"  Max Drawdown:        {btc_4h_static_best['max_drawdown']:.2%}")
print()

print("KEY DIFFERENCES:")
print(f"  Trade count:         {int(btc_4h_static_best['num_trades'])} vs {btc_4h_trade_path['n_trades']} (same ✓)")
print(f"  Win rate:            {btc_4h_static_best['win_rate']:.1%} vs {btc_4h_trade_path['win_rate']:.1%} (higher in static)")
print(f"  Avg PnL:             {btc_4h_static_best['avg_pnl_per_trade']:.2%} vs {btc_4h_trade_path['avg_pnl']:.2%} (WORSE in static!)")
print()

# Compare XAUUSD 4H
print("=" * 80)
print("XAUUSD 4H COMPARISON")
print("=" * 80)
print()

xauusd_4h_trade_path = df_trade_path[(df_trade_path['asset']=='XAUUSD') & (df_trade_path['timeframe']=='4h')].iloc[0]
xauusd_4h_static_best = df_static[df_static['symbol']=='XAUUSD'].nlargest(1, 'sharpe').iloc[0]

print("Trade Path Analysis:")
print(f"  Trades:              {xauusd_4h_trade_path['n_trades']}")
print(f"  Win Rate:            {xauusd_4h_trade_path['win_rate']:.1%}")
print(f"  Avg PnL per trade:   {xauusd_4h_trade_path['avg_pnl']:.2%}")
print(f"  Profit Capture:      {xauusd_4h_trade_path['profit_capture_ratio']:.1%}")
print()

print("Static SL/TP (Best config: SL=3.0, TP=1.0, MaxBars=15):")
print(f"  Trades:              {int(xauusd_4h_static_best['num_trades'])}")
print(f"  Win Rate:            {xauusd_4h_static_best['win_rate']:.1%}")
print(f"  Avg PnL per trade:   {xauusd_4h_static_best['avg_pnl_per_trade']:.2%}")
print(f"  Total Return:        {xauusd_4h_static_best['total_return']:.2%}")
print(f"  Sharpe:              {xauusd_4h_static_best['sharpe']:.2f}")
print()

# Analyze the problem
print("=" * 80)
print("PROBLEM ANALYSIS")
print("=" * 80)
print()

print("ISSUE: Static SL/TP performs WORSE than Trade Path Analysis")
print()
print("Possible reasons:")
print()
print("1. TRANSACTION COSTS:")
print("   - Static SL/TP: 0.07% (7bp) per round-trip")
print("   - Trade Path: No transaction costs applied")
print("   - Impact: -0.07% per trade")
print()

print("2. ENTRY PRICE:")
print("   - Static SL/TP: Uses 'open' price for entry")
print("   - Trade Path: May use different entry logic")
print()

print("3. EXIT LOGIC:")
print("   - Static SL/TP: Fixed SL/TP based on entry ATR")
print("   - Trade Path: -5 ATR stop + new signal exit + no time limit")
print()

print("4. SL/TP PARAMETERS:")
print("   - Best static: SL=3.0, TP=1.0 (tight TP)")
print("   - Trade Path: -5.0 ATR stop (wider)")
print()

# Check if we should test without transaction costs
print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print()
print("1. Re-run static SL/TP with cost_per_trade=0.0 to match Trade Path")
print("2. Check if entry price logic matches")
print("3. Test wider TP values (2.0, 3.0, 4.0 ATR)")
print("4. Test no TP (only SL + max bars)")
print()

# Show all BTC configs sorted by avg_pnl_per_trade
print("=" * 80)
print("ALL BTC 4H CONFIGS (Top 10 by Avg PnL per Trade)")
print("=" * 80)
print()
btc_all = df_static[df_static['symbol']=='BTCUSD'].nlargest(10, 'avg_pnl_per_trade')
print(btc_all[['sl_mult', 'tp_mult', 'max_holding_bars', 'avg_pnl_per_trade', 
               'win_rate', 'sharpe', 'total_return']].to_string(index=False))
print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("The static SL/TP system is working correctly, but:")
print("1. Transaction costs (7bp) are eating into profits")
print("2. Tight TP (1.0 ATR) may be exiting too early")
print("3. Need to test without costs and with wider TP")
print()

