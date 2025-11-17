# -*- coding: utf-8 -*-
"""
Create formatted summary table of all exit rule results
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('results/exit_rule_all_timeframes_summary.csv')

# Sort by mean_pnl descending
df_sorted = df.sort_values('mean_pnl', ascending=False).reset_index(drop=True)

# Add rank
df_sorted.insert(0, 'Rank', range(1, len(df_sorted) + 1))

# Format columns for display
df_display = df_sorted.copy()

# Convert mean_pnl to percentage
df_display['Mean PnL (%)'] = (df_display['mean_pnl'] * 100).round(2)

# Convert win_rate to percentage
df_display['Win Rate (%)'] = (df_display['win_rate'] * 100).round(1)

# Round holding bars
df_display['Avg Hold (bars)'] = df_display['mean_holding_bars'].round(1)

# Simplify rule name
def simplify_rule_name(name):
    if 'NoTP' in name or 'TPinf' in name:
        return 'Wide SL + No TP'
    elif 'Trail' in name:
        return 'Trailing Stop'
    else:
        return 'Static SL/TP'

df_display['Rule Type'] = df_display['rule_name'].apply(simplify_rule_name)

# Format SL/TP parameters
df_display['SL (ATR)'] = df_display['sl_atr'].round(1)
df_display['TP (ATR)'] = df_display['tp_atr'].apply(lambda x: 'inf' if x >= 999 else f'{x:.1f}')
df_display['Trail Trigger'] = df_display['trail_trigger_atr'].apply(lambda x: '-' if x >= 999 else f'{x:.1f}')
df_display['Trail Lock'] = df_display['trail_lock_atr'].apply(lambda x: '-' if x == 0 else f'{x:.1f}')

# Select and rename columns for final output
output_df = df_display[[
    'Rank',
    'symbol',
    'timeframe',
    'rule_name',
    'Rule Type',
    'Mean PnL (%)',
    'Win Rate (%)',
    'num_trades',
    'Avg Hold (bars)',
    'SL (ATR)',
    'TP (ATR)',
    'Trail Trigger',
    'Trail Lock'
]]

output_df.columns = [
    'Rank',
    'Symbol',
    'Timeframe',
    'Rule Name',
    'Rule Type',
    'Mean PnL (%)',
    'Win Rate (%)',
    'Trades',
    'Avg Hold',
    'SL',
    'TP',
    'Trail Trig',
    'Trail Lock'
]

# Save to CSV
output_path = 'results/exit_rule_summary_table.csv'
output_df.to_csv(output_path, index=False)
print(f"✅ Summary table saved to: {output_path}")

# Print full table
print("\n" + "=" * 200)
print("COMPLETE EXIT RULE EVALUATION RESULTS - SORTED BY MEAN PnL")
print("=" * 200)
print()
print(output_df.to_string(index=False))

# Print summary statistics
print("\n" + "=" * 200)
print("SUMMARY STATISTICS")
print("=" * 200)

print("\n📊 BY SYMBOL:")
for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
    symbol_df = output_df[output_df['Symbol'] == symbol]
    if len(symbol_df) > 0:
        best = symbol_df.iloc[0]
        worst = symbol_df.iloc[-1]
        print(f"\n{symbol}:")
        print(f"  Best:  Rank #{best['Rank']:2d} | {best['Timeframe']:6s} | {best['Rule Name']:40s} | PnL={best['Mean PnL (%)']:+7.2f}%")
        print(f"  Worst: Rank #{worst['Rank']:2d} | {worst['Timeframe']:6s} | {worst['Rule Name']:40s} | PnL={worst['Mean PnL (%)']:+7.2f}%")

print("\n📊 BY TIMEFRAME:")
for tf in ['1d', '4h', '60min', '30min', '15min', '5min']:
    tf_df = output_df[output_df['Timeframe'] == tf]
    if len(tf_df) > 0:
        best = tf_df.iloc[0]
        avg_pnl = tf_df['Mean PnL (%)'].mean()
        print(f"\n{tf:6s}:")
        print(f"  Best:    Rank #{best['Rank']:2d} | {best['Symbol']:6s} | {best['Rule Name']:40s} | PnL={best['Mean PnL (%)']:+7.2f}%")
        print(f"  Average: {avg_pnl:+7.2f}%")

print("\n📊 BY RULE TYPE:")
for rule_type in ['Wide SL + No TP', 'Trailing Stop', 'Static SL/TP']:
    type_df = output_df[output_df['Rule Type'] == rule_type]
    if len(type_df) > 0:
        avg_pnl = type_df['Mean PnL (%)'].mean()
        median_pnl = type_df['Mean PnL (%)'].median()
        best = type_df.iloc[0]
        count = len(type_df)
        print(f"\n{rule_type}:")
        print(f"  Count:   {count}")
        print(f"  Average: {avg_pnl:+7.2f}%")
        print(f"  Median:  {median_pnl:+7.2f}%")
        print(f"  Best:    Rank #{best['Rank']:2d} | {best['Symbol']:6s} {best['Timeframe']:6s} | PnL={best['Mean PnL (%)']:+7.2f}%")

print("\n" + "=" * 200)
print("✅ ANALYSIS COMPLETE!")
print("=" * 200)

