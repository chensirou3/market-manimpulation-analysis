# -*- coding: utf-8 -*-
"""
Visualize Exit Rule Evaluation Results - ALL TIMEFRAMES
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load results
df = pd.read_csv('results/exit_rule_all_timeframes_summary.csv')

print("=" * 120)
print("EXIT RULE EVALUATION - ALL TIMEFRAMES ANALYSIS")
print("=" * 120)
print()

# Create comprehensive visualization
fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

symbols = ['XAUUSD', 'BTCUSD', 'ETHUSD']
timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']

# Row 1: Mean PnL heatmap by symbol and timeframe
for idx, symbol in enumerate(symbols):
    ax = fig.add_subplot(gs[0, idx])
    
    symbol_df = df[df['symbol'] == symbol].copy()
    
    # Pivot to get best PnL per timeframe
    pivot_data = []
    for tf in timeframes:
        tf_df = symbol_df[symbol_df['timeframe'] == tf]
        if len(tf_df) > 0:
            best_pnl = tf_df['mean_pnl'].max()
            pivot_data.append({'timeframe': tf, 'best_pnl': best_pnl})
    
    if pivot_data:
        pivot_df = pd.DataFrame(pivot_data)
        
        colors = ['red' if x < 0 else 'green' for x in pivot_df['best_pnl']]
        ax.barh(pivot_df['timeframe'], pivot_df['best_pnl'], color=colors, alpha=0.7)
        ax.set_xlabel('Best Mean PnL')
        ax.set_title(f'{symbol} - Best PnL by Timeframe', fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax.grid(True, alpha=0.3, axis='x')

# Row 2: Win Rate comparison
for idx, symbol in enumerate(symbols):
    ax = fig.add_subplot(gs[1, idx])
    
    symbol_df = df[df['symbol'] == symbol].copy()
    
    # Get best win rate per timeframe
    pivot_data = []
    for tf in timeframes:
        tf_df = symbol_df[symbol_df['timeframe'] == tf]
        if len(tf_df) > 0:
            best_wr = tf_df['win_rate'].max()
            pivot_data.append({'timeframe': tf, 'win_rate': best_wr})
    
    if pivot_data:
        pivot_df = pd.DataFrame(pivot_data)
        
        ax.barh(pivot_df['timeframe'], pivot_df['win_rate'], color='steelblue', alpha=0.7)
        ax.set_xlabel('Best Win Rate')
        ax.set_title(f'{symbol} - Best Win Rate by Timeframe', fontweight='bold')
        ax.axvline(x=0.5, color='red', linestyle='--', linewidth=1, label='50%')
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(0, 1)

# Row 3: Number of trades per timeframe
for idx, symbol in enumerate(symbols):
    ax = fig.add_subplot(gs[2, idx])
    
    symbol_df = df[df['symbol'] == symbol].copy()
    
    # Get number of trades per timeframe
    pivot_data = []
    for tf in timeframes:
        tf_df = symbol_df[symbol_df['timeframe'] == tf]
        if len(tf_df) > 0:
            num_trades = tf_df['num_trades'].iloc[0]
            pivot_data.append({'timeframe': tf, 'num_trades': num_trades})
    
    if pivot_data:
        pivot_df = pd.DataFrame(pivot_data)
        
        ax.barh(pivot_df['timeframe'], pivot_df['num_trades'], color='orange', alpha=0.7)
        ax.set_xlabel('Number of Trades')
        ax.set_title(f'{symbol} - Trade Count by Timeframe', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xscale('log')

# Row 4: Best rule type distribution
ax = fig.add_subplot(gs[3, :])

# Categorize rules
def categorize_rule(name):
    if 'NoTP' in name or 'TPinf' in name:
        return 'Wide SL + No TP'
    elif 'Trail' in name:
        return 'Trailing Stop'
    else:
        return 'Static SL/TP'

df['rule_type'] = df['rule_name'].apply(categorize_rule)

# Count best rules by type
best_rules = df.loc[df.groupby(['symbol', 'timeframe'])['mean_pnl'].idxmax()]
rule_type_counts = best_rules['rule_type'].value_counts()

ax.bar(range(len(rule_type_counts)), rule_type_counts.values, 
       color=['green', 'blue', 'orange'], alpha=0.7)
ax.set_xticks(range(len(rule_type_counts)))
ax.set_xticklabels(rule_type_counts.index, rotation=0)
ax.set_ylabel('Count')
ax.set_title('Best Rule Type Distribution (Across All Symbol-Timeframe Combinations)', 
             fontweight='bold', fontsize=12)
ax.grid(True, alpha=0.3, axis='y')

for i, v in enumerate(rule_type_counts.values):
    ax.text(i, v + 0.3, str(v), ha='center', fontweight='bold')

plt.suptitle('Exit Rule Evaluation - All Timeframes Summary', 
             fontsize=16, fontweight='bold', y=0.995)

plt.savefig('results/exit_rule_all_timeframes_summary.png', dpi=150, bbox_inches='tight')
print(f"✅ Visualization saved to: results/exit_rule_all_timeframes_summary.png\n")

# Print detailed summary
print("\n" + "=" * 120)
print("DETAILED SUMMARY BY SYMBOL")
print("=" * 120)

for symbol in symbols:
    symbol_df = df[df['symbol'] == symbol]
    
    if len(symbol_df) == 0:
        continue
    
    print(f"\n{'=' * 120}")
    print(f"{symbol}")
    print(f"{'=' * 120}\n")
    
    for tf in timeframes:
        tf_df = symbol_df[symbol_df['timeframe'] == tf]
        
        if len(tf_df) == 0:
            continue
        
        best = tf_df.nlargest(1, 'mean_pnl').iloc[0]
        
        print(f"{tf:6s} | Best: {best['rule_name']:40s} | PnL={best['mean_pnl']:+.4f} | "
              f"WR={best['win_rate']:.1%} | Trades={int(best['num_trades']):5d} | "
              f"AvgHold={best['mean_holding_bars']:.1f} bars")

# Key insights
print("\n" + "=" * 120)
print("KEY INSIGHTS")
print("=" * 120)

print("\n1. BEST PERFORMING TIMEFRAMES (by mean PnL):\n")
best_configs = df.nlargest(10, 'mean_pnl')[['symbol', 'timeframe', 'rule_name', 'mean_pnl', 'win_rate', 'num_trades']]
print(best_configs.to_string(index=False))

print("\n\n2. WORST PERFORMING TIMEFRAMES (by mean PnL):\n")
worst_configs = df.nsmallest(10, 'mean_pnl')[['symbol', 'timeframe', 'rule_name', 'mean_pnl', 'win_rate', 'num_trades']]
print(worst_configs.to_string(index=False))

print("\n\n3. RULE TYPE EFFECTIVENESS:\n")
rule_type_stats = df.groupby('rule_type').agg({
    'mean_pnl': ['mean', 'median', 'std'],
    'win_rate': 'mean',
    'num_trades': 'sum'
}).round(4)
print(rule_type_stats)

print("\n" + "=" * 120)
print("ANALYSIS COMPLETE!")
print("=" * 120)

