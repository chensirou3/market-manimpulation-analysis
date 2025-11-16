"""
Transaction Cost Sensitivity Analysis

Test how different transaction cost levels affect strategy performance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds

print("=" * 80)
print("Transaction Cost Sensitivity Analysis")
print("=" * 80)

def generate_asymmetric_signals(bars, config):
    """Generate asymmetric signals: UP=continuation, DOWN=reversal"""
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0
    
    bars = compute_trend_strength(bars, L_past=config.L_past, vol_window=config.vol_window)
    thresholds = compute_extreme_trend_thresholds(bars, quantile=config.q_extreme_trend)
    threshold = thresholds['threshold']
    
    extreme_up = bars['TS'] > threshold
    extreme_down = bars['TS'] < -threshold
    high_manip = bars['ManipScore'] > bars['ManipScore'].quantile(config.q_manip)
    
    signals.loc[extreme_up & high_manip, 'signal'] = 1
    signals.loc[extreme_down & high_manip, 'signal'] = 1
    signals['signal'] = signals['signal'].shift(1).fillna(0)
    
    return signals

def test_cost_sensitivity(asset, timeframe, use_sl_tp, cost_levels):
    """Test different cost levels for a specific strategy."""
    # Determine file path
    if asset == 'XAUUSD':
        bars_path = f'results/bars_{timeframe}_with_manipscore_full.csv'
    else:
        bars_path = f'results/bars_{timeframe}_{asset.lower()}_full_with_manipscore.csv'
    
    if not Path(bars_path).exists():
        print(f"  File not found: {bars_path}")
        return None
    
    bars = pd.read_csv(bars_path, index_col=0, parse_dates=True)
    
    results = []
    
    for cost in cost_levels:
        config = ExtremeReversalConfig(
            bar_size=timeframe,
            L_past=5,
            vol_window=20,
            q_extreme_trend=0.9,
            q_manip=0.9,
            holding_horizon=5,
            atr_window=10,
            sl_atr_mult=0.5 if use_sl_tp else 999.0,
            tp_atr_mult=0.8 if use_sl_tp else 999.0,
            cost_per_trade=cost
        )
        
        signals = generate_asymmetric_signals(bars, config)
        bars['exec_signal'] = signals['signal']
        result = run_extreme_reversal_backtest(bars, bars['exec_signal'], config, initial_capital=10000)
        
        results.append({
            'Cost_BP': cost * 10000,  # Convert to basis points
            'Cost_Pct': cost * 100,   # Convert to percentage
            'Sharpe': result.stats.get('sharpe_ratio', 0),
            'Total_Return': result.stats.get('total_return', 0) * 100,
            'Trades': len(result.trades),
            'Win_Rate': result.stats.get('win_rate', 0),
            'Max_DD': result.stats.get('max_drawdown', 0) * 100
        })
    
    return pd.DataFrame(results)

# Define cost levels to test
cost_levels = [
    0.0001,  # 1 bp - Current (optimistic)
    0.0003,  # 3 bp - Futures maker
    0.0005,  # 5 bp - Conservative
    0.001,   # 10 bp - Realistic
    0.002,   # 20 bp - Pessimistic
]

# Test cases: Best strategies for each asset
test_cases = [
    # BTC
    {'asset': 'BTC', 'timeframe': '4h', 'use_sl_tp': False, 'name': 'BTC 4h Pure'},
    {'asset': 'BTC', 'timeframe': '5min', 'use_sl_tp': True, 'name': 'BTC 5min+SL/TP'},
    
    # ETH
    {'asset': 'ETH', 'timeframe': '30min', 'use_sl_tp': True, 'name': 'ETH 30min+SL/TP'},
    {'asset': 'ETH', 'timeframe': '5min', 'use_sl_tp': True, 'name': 'ETH 5min+SL/TP'},
    
    # XAUUSD
    {'asset': 'XAUUSD', 'timeframe': '4h', 'use_sl_tp': True, 'name': 'XAUUSD 4h+SL/TP'},
]

all_results = {}

for case in test_cases:
    print(f"\nTesting: {case['name']}")
    print("-" * 80)
    
    try:
        df = test_cost_sensitivity(
            case['asset'],
            case['timeframe'],
            case['use_sl_tp'],
            cost_levels
        )
        
        if df is not None:
            all_results[case['name']] = df
            print(df.to_string(index=False))
            
            # Calculate impact
            baseline = df.iloc[0]['Total_Return']
            print(f"\nImpact Analysis (vs baseline {baseline:.2f}%):")
            for idx, row in df.iterrows():
                if idx > 0:
                    impact = ((row['Total_Return'] - baseline) / baseline) * 100
                    print(f"  {row['Cost_BP']:.1f} bp: {row['Total_Return']:.2f}% ({impact:+.1f}%)")
    
    except Exception as e:
        print(f"  ERROR: {e}")

# Save combined results
print("\n" + "=" * 80)
print("Saving Results")
print("=" * 80)

# Create summary comparison
summary_data = []
for name, df in all_results.items():
    for idx, row in df.iterrows():
        summary_data.append({
            'Strategy': name,
            'Cost_BP': row['Cost_BP'],
            'Sharpe': row['Sharpe'],
            'Return_Pct': row['Total_Return'],
            'Trades': row['Trades'],
            'Win_Rate': row['Win_Rate']
        })

summary_df = pd.DataFrame(summary_data)
output_path = 'results/cost_sensitivity_analysis.csv'
summary_df.to_csv(output_path, index=False)
print(f"Saved: {output_path}")

# Create pivot table for easy comparison
print("\n" + "=" * 80)
print("Summary: Return % by Cost Level")
print("=" * 80)

pivot = summary_df.pivot(index='Strategy', columns='Cost_BP', values='Return_Pct')
print(pivot.to_string())

print("\n" + "=" * 80)
print("Analysis Complete!")
print("=" * 80)

