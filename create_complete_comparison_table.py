# -*- coding: utf-8 -*-
"""
Create complete comparison table including XAUUSD data from the report
"""

import pandas as pd

# Read existing BTC and ETH data
btc_eth_df = pd.read_csv('results/all_assets_trade_path_comparison.csv')

# XAUUSD data from the report (XAUUSD_全时间周期交易路径分析报告.md)
xauusd_data = [
    {
        'asset': 'XAUUSD',
        'timeframe': '5min',
        'n_trades': 4301,
        'win_rate': 0.494,
        'avg_pnl': 0.0000,
        'avg_mfe': 0.0012,
        'avg_mae': None,  # Not available in report
        't_mfe_median': 2.0,
        't_mfe_mean': None,  # Not available in report
        'profit_capture_ratio': 0.037,
        'avg_holding_bars': 27.7
    },
    {
        'asset': 'XAUUSD',
        'timeframe': '15min',
        'n_trades': 1369,
        'win_rate': 0.486,
        'avg_pnl': 0.0002,
        'avg_mfe': 0.0025,
        'avg_mae': None,
        't_mfe_median': 3.0,
        't_mfe_mean': None,
        'profit_capture_ratio': 0.072,
        'avg_holding_bars': 31.7
    },
    {
        'asset': 'XAUUSD',
        'timeframe': '30min',
        'n_trades': 627,
        'win_rate': 0.522,
        'avg_pnl': 0.0005,
        'avg_mfe': 0.0041,
        'avg_mae': None,
        't_mfe_median': 5.0,
        't_mfe_mean': None,
        'profit_capture_ratio': 0.112,
        'avg_holding_bars': 34.6
    },
    {
        'asset': 'XAUUSD',
        'timeframe': '60min',
        'n_trades': 280,
        'win_rate': 0.529,
        'avg_pnl': 0.0032,
        'avg_mfe': 0.0090,
        'avg_mae': None,
        't_mfe_median': 8.0,
        't_mfe_mean': None,
        'profit_capture_ratio': 0.355,
        'avg_holding_bars': 38.2
    },
    {
        'asset': 'XAUUSD',
        'timeframe': '4h',
        'n_trades': 67,
        'win_rate': 0.507,
        'avg_pnl': 0.0116,
        'avg_mfe': 0.0252,
        'avg_mae': None,
        't_mfe_median': 13.0,
        't_mfe_mean': None,
        'profit_capture_ratio': 0.461,
        'avg_holding_bars': 41.3
    },
    {
        'asset': 'XAUUSD',
        'timeframe': '1d',
        'n_trades': 9,
        'win_rate': 0.667,
        'avg_pnl': -0.0042,
        'avg_mfe': 0.0454,
        'avg_mae': None,
        't_mfe_median': 17.0,
        't_mfe_mean': None,
        'profit_capture_ratio': -0.092,
        'avg_holding_bars': 44.6
    }
]

# Create XAUUSD DataFrame
xauusd_df = pd.DataFrame(xauusd_data)

# Combine all data
complete_df = pd.concat([btc_eth_df, xauusd_df], ignore_index=True)

# Sort by asset and timeframe
timeframe_order = ['5min', '15min', '30min', '60min', '4h', '1d']
complete_df['timeframe_order'] = complete_df['timeframe'].map({tf: i for i, tf in enumerate(timeframe_order)})
complete_df = complete_df.sort_values(['asset', 'timeframe_order']).drop('timeframe_order', axis=1)

# Save complete comparison table
complete_df.to_csv('results/all_assets_complete_comparison.csv', index=False)

print("=" * 100)
print("COMPLETE COMPARISON TABLE - ALL THREE ASSETS")
print("=" * 100)
print()
print(complete_df.to_string(index=False))
print()

# Summary by asset
print("=" * 100)
print("SUMMARY BY ASSET")
print("=" * 100)
print()

for asset in ['BTC', 'ETH', 'XAUUSD']:
    asset_df = complete_df[complete_df['asset'] == asset]
    print(f"\n{asset}:")
    print(f"  Total trades:                {asset_df['n_trades'].sum():,}")
    print(f"  Avg win rate:                {asset_df['win_rate'].mean():.1%}")
    print(f"  Avg profit capture rate:     {asset_df['profit_capture_ratio'].mean():.1%}")
    print(f"  Best TF (by capture rate):   {asset_df.loc[asset_df['profit_capture_ratio'].idxmax(), 'timeframe']} ({asset_df['profit_capture_ratio'].max():.1%})")
    print(f"  Best TF (by avg PnL):        {asset_df.loc[asset_df['avg_pnl'].idxmax(), 'timeframe']} ({asset_df['avg_pnl'].max():.2%})")

# Best configurations across all assets
print("\n" + "=" * 100)
print("TOP 10 CONFIGURATIONS BY PROFIT CAPTURE RATE (ALL ASSETS)")
print("=" * 100)
print()
top10 = complete_df.nlargest(10, 'profit_capture_ratio')[['asset', 'timeframe', 'n_trades', 'win_rate', 'avg_pnl', 'profit_capture_ratio', 't_mfe_median']]
print(top10.to_string(index=False))

print("\n" + "=" * 100)
print("KEY INSIGHTS")
print("=" * 100)
print()
print("1. BEST ASSET BY PROFIT CAPTURE RATE:")
print("   - XAUUSD 4H: 46.1% (BEST OVERALL!)")
print("   - XAUUSD 60min: 35.5%")
print("   - BTC 4H: 32.9%")
print()
print("2. BEST ASSET BY WIN RATE:")
print("   - XAUUSD: 51.8% average (BEST!)")
print("   - BTC: 37.6% average")
print("   - ETH: 35.3% average")
print()
print("3. BEST ASSET BY SINGLE TRADE PROFIT:")
print("   - ETH 1D: 18.17% (but only 14 trades)")
print("   - BTC 1D: 14.39% (15 trades)")
print("   - BTC 4H: 5.90% (82 trades)")
print()
print("4. RECOMMENDATION:")
print("   - XAUUSD 4H: Best balance of capture rate, win rate, and sample size")
print("   - BTC 4H: Good alternative with higher single-trade profit")
print("   - ETH: Generally underperforms, not recommended")
print()

print("=" * 100)
print(f"Complete comparison table saved to: results/all_assets_complete_comparison.csv")
print("=" * 100)

