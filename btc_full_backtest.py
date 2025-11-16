"""
BTC Full Dataset Backtest (2017-2024)

Test asymmetric strategy on all timeframes with full 8-year dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds

print("=" * 80)
print("BTC Full Dataset Backtest - All Timeframes (2017-2024)")
print("=" * 80)

def generate_asymmetric_signals(bars, config):
    """
    Generate asymmetric signals:
    - UP extreme + high manip → LONG (continuation)
    - DOWN extreme + high manip → LONG (reversal)
    """
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0
    
    # Compute trend strength
    bars = compute_trend_strength(bars, L_past=config.L_past, vol_window=config.vol_window)
    
    # Get extreme thresholds
    thresholds = compute_extreme_trend_thresholds(bars, quantile=config.q_extreme_trend)
    threshold = thresholds['threshold']
    
    # Identify extreme trends
    extreme_up = bars['TS'] > threshold
    extreme_down = bars['TS'] < -threshold
    
    # High manipulation score
    high_manip = bars['ManipScore'] > bars['ManipScore'].quantile(config.q_manip)
    
    # Asymmetric signals: both go LONG
    signals.loc[extreme_up & high_manip, 'signal'] = 1  # UP → LONG (continuation)
    signals.loc[extreme_down & high_manip, 'signal'] = 1  # DOWN → LONG (reversal)
    
    # Shift to avoid look-ahead bias
    signals['signal'] = signals['signal'].shift(1).fillna(0)
    
    return signals

def run_backtest_for_timeframe(timeframe, use_sl_tp=False):
    """Run backtest for a specific timeframe."""
    # Load bars
    bars_path = f'results/bars_{timeframe}_btc_full_with_manipscore.csv'
    if not Path(bars_path).exists():
        print(f"  File not found: {bars_path}")
        return None
    
    bars = pd.read_csv(bars_path, index_col=0, parse_dates=True)
    
    # Config
    config = ExtremeReversalConfig(
        bar_size=timeframe,
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5 if use_sl_tp else 999.0,  # Very large value = no SL
        tp_atr_mult=0.8 if use_sl_tp else 999.0,  # Very large value = no TP
        cost_per_trade=0.0001
    )
    
    # Generate signals
    signals = generate_asymmetric_signals(bars, config)
    
    # Add signals to bars
    bars['exec_signal'] = signals['signal']
    
    # Run backtest
    result = run_extreme_reversal_backtest(bars, bars['exec_signal'], config, initial_capital=10000)
    
    return result

# Test all timeframes
timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']
results_summary = []

for tf in timeframes:
    print(f"\nTesting {tf}...")
    
    try:
        # Pure factor (no SL/TP)
        print(f"  Pure factor...")
        result_pure = run_backtest_for_timeframe(tf, use_sl_tp=False)
        
        # With SL/TP
        print(f"  With SL/TP...")
        result_sltp = run_backtest_for_timeframe(tf, use_sl_tp=True)
    except Exception as e:
        print(f"  ERROR: {e}")
        result_pure = None
        result_sltp = None
    
    if result_pure is not None and result_sltp is not None:
        summary = {
            'Timeframe': tf,
            'Pure_Sharpe': result_pure.stats.get('sharpe_ratio', 0),
            'Pure_Return': result_pure.stats.get('total_return', 0) * 100,  # Convert to %
            'Pure_Trades': len(result_pure.trades),
            'Pure_WinRate': result_pure.stats.get('win_rate', 0),
            'SLTP_Sharpe': result_sltp.stats.get('sharpe_ratio', 0),
            'SLTP_Return': result_sltp.stats.get('total_return', 0) * 100,  # Convert to %
            'SLTP_Trades': len(result_sltp.trades),
            'SLTP_WinRate': result_sltp.stats.get('win_rate', 0),
        }
        results_summary.append(summary)
        
        print(f"  Pure: Sharpe={summary['Pure_Sharpe']:.2f}, Return={summary['Pure_Return']:.2f}%, Trades={summary['Pure_Trades']}")
        print(f"  SLTP: Sharpe={summary['SLTP_Sharpe']:.2f}, Return={summary['SLTP_Return']:.2f}%, Trades={summary['SLTP_Trades']}")

# Save results
print("\n" + "=" * 80)
print("Results Summary")
print("=" * 80)

df_results = pd.DataFrame(results_summary)
print(df_results.to_string(index=False))

output_path = 'results/btc_full_timeframes_comparison.csv'
df_results.to_csv(output_path, index=False)
print(f"\nSaved to {output_path}")

