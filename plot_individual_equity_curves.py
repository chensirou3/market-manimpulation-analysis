"""
Plot Individual Equity Curves for Each Asset

Creates separate detailed plots for BTC, ETH, and XAUUSD.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds

plt.style.use('seaborn-v0_8-darkgrid')

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

def get_equity_curve(bars_path, use_sl_tp=False):
    """Get equity curve for a specific file."""
    if not Path(bars_path).exists():
        return None, None
    
    bars = pd.read_csv(bars_path, index_col=0, parse_dates=True)
    
    # Extract timeframe from path
    if '5min' in bars_path:
        tf = '5min'
    elif '15min' in bars_path:
        tf = '15min'
    elif '30min' in bars_path:
        tf = '30min'
    elif '60min' in bars_path:
        tf = '60min'
    elif '4h' in bars_path:
        tf = '4h'
    elif '1d' in bars_path:
        tf = '1d'
    else:
        tf = 'unknown'
    
    config = ExtremeReversalConfig(
        bar_size=tf,
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5 if use_sl_tp else 999.0,
        tp_atr_mult=0.8 if use_sl_tp else 999.0,
        cost_per_trade=0.0001
    )
    
    signals = generate_asymmetric_signals(bars, config)
    bars['exec_signal'] = signals['signal']
    result = run_extreme_reversal_backtest(bars, bars['exec_signal'], config, initial_capital=10000)
    
    return result.equity_curve, result

def plot_asset_equity_curves(asset_name, timeframes_config, output_file):
    """Plot equity curves for a single asset."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    fig.suptitle(f'{asset_name} - Equity Curves Comparison', fontsize=16, fontweight='bold')
    
    for tf_name, file_path in timeframes_config.items():
        print(f"  Processing {tf_name}...")
        
        # Pure factor
        try:
            equity_pure, result_pure = get_equity_curve(file_path, use_sl_tp=False)
            if equity_pure is not None and len(equity_pure) > 0:
                sharpe = result_pure.stats.get('sharpe_ratio', 0)
                total_return = result_pure.stats.get('total_return', 0) * 100
                label = f"{tf_name} (Sharpe: {sharpe:.2f}, Return: {total_return:.1f}%)"
                ax1.plot(equity_pure.index, equity_pure.values, label=label, linewidth=2)
        except Exception as e:
            print(f"    Pure factor error: {e}")
        
        # With SL/TP
        try:
            equity_sltp, result_sltp = get_equity_curve(file_path, use_sl_tp=True)
            if equity_sltp is not None and len(equity_sltp) > 0:
                sharpe = result_sltp.stats.get('sharpe_ratio', 0)
                total_return = result_sltp.stats.get('total_return', 0) * 100
                label = f"{tf_name} (Sharpe: {sharpe:.2f}, Return: {total_return:.1f}%)"
                ax2.plot(equity_sltp.index, equity_sltp.values, label=label, linewidth=2)
        except Exception as e:
            print(f"    SL/TP error: {e}")
    
    # Format subplots
    ax1.set_title('Pure Factor (No SL/TP)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Equity ($)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=10000, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
    
    ax2.set_title('With Stop-Loss/Take-Profit', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Equity ($)', fontsize=12)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=10000, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  Saved: {output_file}")
    plt.close()

print("=" * 80)
print("Generating Individual Equity Curves")
print("=" * 80)

# BTC
print("\nBTC:")
btc_config = {
    '4h': 'results/bars_4h_btc_full_with_manipscore.csv',
    '60min': 'results/bars_60min_btc_full_with_manipscore.csv',
    '15min': 'results/bars_15min_btc_full_with_manipscore.csv',
    '5min': 'results/bars_5min_btc_full_with_manipscore.csv'
}
plot_asset_equity_curves('BTC', btc_config, 'results/equity_curve_btc.png')

# ETH
print("\nETH:")
eth_config = {
    '30min': 'results/bars_30min_eth_full_with_manipscore.csv',
    '60min': 'results/bars_60min_eth_full_with_manipscore.csv',
    '15min': 'results/bars_15min_eth_full_with_manipscore.csv',
    '5min': 'results/bars_5min_eth_full_with_manipscore.csv'
}
plot_asset_equity_curves('ETH', eth_config, 'results/equity_curve_eth.png')

# XAUUSD
print("\nXAUUSD:")
xauusd_config = {
    '4h': 'results/bars_4h_with_manipscore_full.csv',
    '60min': 'results/bars_60min_with_manipscore_full.csv',
    '30min': 'results/bars_30min_with_manipscore_full.csv',
    '15min': 'results/bars_15min_with_manipscore_full.csv'
}
plot_asset_equity_curves('XAUUSD', xauusd_config, 'results/equity_curve_xauusd.png')

print("\n" + "=" * 80)
print("All equity curves generated!")
print("=" * 80)

