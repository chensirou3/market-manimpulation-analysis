# -*- coding: utf-8 -*-
"""
Generate comprehensive summary report for trade path analysis
"""

import pandas as pd
import numpy as np

# Read the comparison data
df = pd.read_csv('results/all_assets_trade_path_comparison.csv')

print("=" * 100)
print("BTC vs ETH TRADE PATH ANALYSIS - COMPREHENSIVE SUMMARY")
print("=" * 100)
print()

# Overall comparison table
print("=" * 100)
print("FULL COMPARISON TABLE")
print("=" * 100)
print()
print(df.to_string(index=False))
print()

# Key metrics by timeframe
print("=" * 100)
print("KEY METRICS BY TIMEFRAME")
print("=" * 100)

for tf in ['5min', '15min', '30min', '60min', '4h', '1d']:
    print(f"\n{'=' * 60}")
    print(f"Timeframe: {tf}")
    print(f"{'=' * 60}")
    
    subset = df[df['timeframe'] == tf]
    
    for _, row in subset.iterrows():
        print(f"\n{row['asset']}:")
        print(f"  Trades:              {row['n_trades']:,}")
        print(f"  Win Rate:            {row['win_rate']:.1%}")
        print(f"  Avg PnL:             {row['avg_pnl']:.2%}")
        print(f"  Avg MFE:             {row['avg_mfe']:.2%}")
        print(f"  Avg MAE:             {row['avg_mae']:.2%}")
        print(f"  Profit Capture:      {row['profit_capture_ratio']:.1%}")
        print(f"  t_mfe (median):      {row['t_mfe_median']:.0f} bars")
        print(f"  t_mfe (mean):        {row['t_mfe_mean']:.0f} bars")
        print(f"  Avg Holding:         {row['avg_holding_bars']:.0f} bars")

# Best performing configurations
print("\n" + "=" * 100)
print("TOP 5 CONFIGURATIONS BY PROFIT CAPTURE RATE")
print("=" * 100)
print()
top5 = df.nlargest(5, 'profit_capture_ratio')[['asset', 'timeframe', 'n_trades', 'avg_pnl', 'profit_capture_ratio', 't_mfe_median']]
print(top5.to_string(index=False))

print("\n" + "=" * 100)
print("TOP 5 CONFIGURATIONS BY AVERAGE PNL")
print("=" * 100)
print()
top5_pnl = df.nlargest(5, 'avg_pnl')[['asset', 'timeframe', 'n_trades', 'avg_pnl', 'profit_capture_ratio', 't_mfe_median']]
print(top5_pnl.to_string(index=False))

# Summary statistics
print("\n" + "=" * 100)
print("SUMMARY STATISTICS")
print("=" * 100)
print()

for asset in ['BTC', 'ETH']:
    asset_df = df[df['asset'] == asset]
    print(f"\n{asset}:")
    print(f"  Best timeframe (by capture rate): {asset_df.loc[asset_df['profit_capture_ratio'].idxmax(), 'timeframe']}")
    print(f"  Best timeframe (by avg PnL):      {asset_df.loc[asset_df['avg_pnl'].idxmax(), 'timeframe']}")
    print(f"  Total trades across all TFs:      {asset_df['n_trades'].sum():,}")
    print(f"  Avg win rate:                     {asset_df['win_rate'].mean():.1%}")
    print(f"  Avg profit capture rate:          {asset_df['profit_capture_ratio'].mean():.1%}")

print("\n" + "=" * 100)
print("KEY INSIGHTS")
print("=" * 100)
print()
print("1. TIMEFRAME EFFECT:")
print("   - Longer timeframes have MUCH higher profit capture rates")
print("   - 4H and 1D capture 20-33% of potential profit vs 4-20% for shorter TFs")
print()
print("2. ASSET COMPARISON:")
print("   - BTC generally outperforms ETH in profit capture efficiency")
print("   - BTC 4H: 32.9% capture rate vs ETH 4H: 21.9%")
print()
print("3. OPTIMAL HOLDING TIME:")
print("   - Short TFs (5-60min): Need 10-15 bars to reach max profit")
print("   - Long TFs (4H-1D): Only need 5.5-27 bars to reach max profit")
print()
print("4. RECOMMENDATION:")
print("   - FOCUS ON 4H AND 1D TIMEFRAMES for both BTC and ETH")
print("   - Consider dynamic exit based on t_mfe distribution")
print("   - Short TF strategies need aggressive profit-taking")
print()

print("=" * 100)
print("END OF REPORT")
print("=" * 100)

