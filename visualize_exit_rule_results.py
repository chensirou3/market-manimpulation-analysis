# -*- coding: utf-8 -*-
"""
Visualize Exit Rule Evaluation Results
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load results
df = pd.read_csv('results/exit_rule_per_trade_4h_summary.csv')

print("=" * 80)
print("EXIT RULE EVALUATION RESULTS - 4H TIMEFRAME")
print("=" * 80)
print()

# Display top results for each symbol
for symbol in ['XAUUSD', 'BTCUSD']:
    symbol_df = df[df['symbol'] == symbol].copy()
    
    print(f"\n{symbol} - TOP 5 BY MEAN PNL:")
    print("-" * 80)
    top5 = symbol_df.nlargest(5, 'mean_pnl')
    print(top5[['rule_name', 'mean_pnl', 'win_rate', 'mean_mfe', 'mean_mae', 
                'mean_holding_bars', 'exit_SL', 'exit_TP', 'exit_TRAIL']].to_string(index=False))
    
    print(f"\n{symbol} - TOP 5 BY WIN RATE:")
    print("-" * 80)
    top5_wr = symbol_df.nlargest(5, 'win_rate')
    print(top5_wr[['rule_name', 'win_rate', 'mean_pnl', 'mean_mfe', 'mean_mae']].to_string(index=False))

# Create visualization
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('Exit Rule Evaluation - 4H Timeframe', fontsize=16, fontweight='bold')

for idx, symbol in enumerate(['XAUUSD', 'BTCUSD']):
    symbol_df = df[df['symbol'] == symbol].copy()
    
    # Plot 1: Mean PnL by rule
    ax = axes[idx, 0]
    symbol_df_sorted = symbol_df.sort_values('mean_pnl', ascending=False)
    colors = ['green' if x > 0 else 'red' for x in symbol_df_sorted['mean_pnl']]
    ax.barh(range(len(symbol_df_sorted)), symbol_df_sorted['mean_pnl'], color=colors, alpha=0.7)
    ax.set_yticks(range(len(symbol_df_sorted)))
    ax.set_yticklabels(symbol_df_sorted['rule_name'], fontsize=8)
    ax.set_xlabel('Mean PnL')
    ax.set_title(f'{symbol} - Mean PnL by Rule')
    ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Win Rate vs Mean PnL
    ax = axes[idx, 1]
    scatter = ax.scatter(symbol_df['win_rate'], symbol_df['mean_pnl'], 
                        c=symbol_df['mean_holding_bars'], cmap='viridis', s=100, alpha=0.7)
    ax.set_xlabel('Win Rate')
    ax.set_ylabel('Mean PnL')
    ax.set_title(f'{symbol} - Win Rate vs Mean PnL')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax.grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=ax, label='Mean Holding Bars')
    
    # Add labels for top/bottom performers
    for _, row in symbol_df.nlargest(2, 'mean_pnl').iterrows():
        ax.annotate(row['rule_name'].split('_')[0], 
                   (row['win_rate'], row['mean_pnl']),
                   fontsize=7, alpha=0.7)
    
    # Plot 3: Exit Reason Distribution
    ax = axes[idx, 2]
    exit_cols = ['exit_SL', 'exit_TP', 'exit_TRAIL', 'exit_TIME_MAX', 'exit_RAW_END']
    exit_data = symbol_df[exit_cols].mean()
    ax.bar(range(len(exit_data)), exit_data.values, alpha=0.7)
    ax.set_xticks(range(len(exit_data)))
    ax.set_xticklabels([c.replace('exit_', '') for c in exit_cols], rotation=45)
    ax.set_ylabel('Average Count per Rule')
    ax.set_title(f'{symbol} - Exit Reason Distribution')
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('results/exit_rule_evaluation_4h.png', dpi=150, bbox_inches='tight')
print(f"\n\nVisualization saved to: results/exit_rule_evaluation_4h.png")

# Summary statistics
print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

for symbol in ['XAUUSD', 'BTCUSD']:
    symbol_df = df[df['symbol'] == symbol]
    
    print(f"\n{symbol}:")
    print(f"  Best mean PnL: {symbol_df['mean_pnl'].max():.4f} ({symbol_df.loc[symbol_df['mean_pnl'].idxmax(), 'rule_name']})")
    print(f"  Worst mean PnL: {symbol_df['mean_pnl'].min():.4f} ({symbol_df.loc[symbol_df['mean_pnl'].idxmin(), 'rule_name']})")
    print(f"  Best win rate: {symbol_df['win_rate'].max():.2%} ({symbol_df.loc[symbol_df['win_rate'].idxmax(), 'rule_name']})")
    print(f"  Mean MFE: {symbol_df['mean_mfe'].iloc[0]:.4f}")
    print(f"  Mean MAE: {symbol_df['mean_mae'].iloc[0]:.4f}")
    
    # Find best trailing rule
    trailing_rules = symbol_df[symbol_df['rule_name'].str.contains('Trail')]
    if len(trailing_rules) > 0:
        best_trail = trailing_rules.nlargest(1, 'mean_pnl').iloc[0]
        print(f"  Best trailing rule: {best_trail['rule_name']} (mean_pnl={best_trail['mean_pnl']:.4f}, win_rate={best_trail['win_rate']:.2%})")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)

