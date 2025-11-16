"""
Plot Equity Curves for All Assets and Timeframes

This script generates equity curve visualizations for BTC, ETH, and XAUUSD
across different timeframes to compare performance visually.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds

# Set up matplotlib for better looking plots
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

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

def get_equity_curve(asset, timeframe, use_sl_tp=False):
    """Get equity curve for a specific asset and timeframe."""
    # Determine file path
    if asset == 'XAUUSD':
        bars_path = f'results/bars_{timeframe}_with_manipscore.csv'
    else:
        bars_path = f'results/bars_{timeframe}_{asset.lower()}_full_with_manipscore.csv'

    if not Path(bars_path).exists():
        print(f"  File not found: {bars_path}")
        return None, None

    bars = pd.read_csv(bars_path, index_col=0, parse_dates=True)

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
        cost_per_trade=0.0001
    )

    signals = generate_asymmetric_signals(bars, config)
    bars['exec_signal'] = signals['signal']
    result = run_extreme_reversal_backtest(bars, bars['exec_signal'], config, initial_capital=10000)

    # Use equity curve from result
    equity = result.equity_curve

    return equity, result

print("=" * 80)
print("Generating Equity Curves for All Assets")
print("=" * 80)

# Define assets and their best timeframes
assets_config = {
    'BTC': {'timeframes': ['4h', '60min', '15min'], 'best': '4h'},
    'ETH': {'timeframes': ['30min', '60min', '15min'], 'best': '30min'},
    'XAUUSD': {'timeframes': ['4h', '60min', '30min'], 'best': '4h'}
}

# Create figure with subplots
fig, axes = plt.subplots(3, 2, figsize=(18, 12))
fig.suptitle('Equity Curves - All Assets (Best Strategies)', fontsize=16, fontweight='bold')

for idx, (asset, config) in enumerate(assets_config.items()):
    print(f"\n{asset}:")
    
    # Pure factor
    ax_pure = axes[idx, 0]
    ax_sltp = axes[idx, 1]
    
    for tf in config['timeframes']:
        print(f"  Processing {tf}...")
        
        # Pure factor
        try:
            equity_pure, result_pure = get_equity_curve(asset, tf, use_sl_tp=False)
            if equity_pure is not None:
                label = f"{tf} (Sharpe: {result_pure.stats.get('sharpe_ratio', 0):.2f})"
                linewidth = 3 if tf == config['best'] else 1.5
                ax_pure.plot(equity_pure.index, equity_pure.values, label=label, linewidth=linewidth)
        except Exception as e:
            print(f"    Pure factor error: {e}")
        
        # With SL/TP
        try:
            equity_sltp, result_sltp = get_equity_curve(asset, tf, use_sl_tp=True)
            if equity_sltp is not None:
                label = f"{tf} (Sharpe: {result_sltp.stats.get('sharpe_ratio', 0):.2f})"
                linewidth = 3 if tf == config['best'] else 1.5
                ax_sltp.plot(equity_sltp.index, equity_sltp.values, label=label, linewidth=linewidth)
        except Exception as e:
            print(f"    SL/TP error: {e}")
    
    # Format pure factor subplot
    ax_pure.set_title(f'{asset} - Pure Factor', fontsize=12, fontweight='bold')
    ax_pure.set_xlabel('Date')
    ax_pure.set_ylabel('Equity ($)')
    ax_pure.legend(loc='best')
    ax_pure.grid(True, alpha=0.3)
    ax_pure.axhline(y=10000, color='gray', linestyle='--', alpha=0.5)
    
    # Format SL/TP subplot
    ax_sltp.set_title(f'{asset} - With SL/TP', fontsize=12, fontweight='bold')
    ax_sltp.set_xlabel('Date')
    ax_sltp.set_ylabel('Equity ($)')
    ax_sltp.legend(loc='best')
    ax_sltp.grid(True, alpha=0.3)
    ax_sltp.axhline(y=10000, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
output_path = 'results/equity_curves_all_assets.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\n{'=' * 80}")
print(f"Saved: {output_path}")
print("=" * 80)

plt.show()

