"""
Example: Trade Path Analysis for BTC Pure Factor Strategy

This script demonstrates how to use the trade path analysis module
to understand the raw quality of our factor, independent of any
time-based exit or portfolio constraints.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.trade_path_analysis import (
    TradePathConfig,
    analyze_trade_paths_long_only,
    summarize_trade_paths,
    print_trade_path_summary
)
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.trend_features import compute_trend_strength


def compute_atr(bars: pd.DataFrame, window: int = 10) -> pd.Series:
    """Compute Average True Range"""
    high = bars['high']
    low = bars['low']
    close = bars['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    return atr


def generate_pure_factor_signals(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig
) -> pd.Series:
    """
    Generate pure factor signals (long-only).
    
    Returns a Series with values in {0, 1}:
    - 1 = open long
    - 0 = no action
    """
    # Compute trend features
    bars = compute_trend_strength(
        bars,
        L_past=config.L_past,
        vol_window=config.vol_window
    )
    
    # Ensure ManipScore exists
    if 'ManipScore' not in bars.columns:
        print("Warning: ManipScore not found, using placeholder")
        bars['ManipScore'] = np.random.randn(len(bars))
    
    # Compute thresholds
    threshold_ts = bars['TS'].abs().quantile(config.q_extreme_trend)
    threshold_manip = bars['ManipScore'].quantile(config.q_manip)
    
    # Identify extreme trends
    extreme_up = bars['TS'] > threshold_ts
    extreme_down = bars['TS'] < -threshold_ts
    
    # Identify high manipulation
    high_manip = bars['ManipScore'] > threshold_manip
    
    # Generate raw signals (both up and down extremes for long-only asymmetric)
    signal_raw = pd.Series(0, index=bars.index)
    signal_raw[(extreme_up | extreme_down) & high_manip] = 1
    
    # Shift to avoid look-ahead bias
    signal_exec = signal_raw.shift(1).fillna(0).astype(int)
    
    return signal_exec


def main():
    """Run trade path analysis on BTC 4H data"""
    
    print("\n" + "="*80)
    print("Trade Path Analysis - BTC 4H Pure Factor Strategy")
    print("="*80)
    
    # Load data
    data_path = Path("results/bars_4h_btc_full_with_manipscore.csv")
    
    if not data_path.exists():
        print(f"\nERROR: Data file not found: {data_path}")
        print("Please run BTC data processing first.")
        return
    
    print(f"\n📂 Loading data from: {data_path}")
    bars = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"   Loaded {len(bars):,} bars")
    print(f"   Period: {bars.index[0]} to {bars.index[-1]}")
    
    # Strategy configuration
    config = ExtremeReversalConfig(
        bar_size='4h',
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,  # This will be ignored in path analysis
        atr_window=10
    )
    
    print(f"\n⚙️  Strategy Configuration:")
    print(f"   L_past: {config.L_past}")
    print(f"   vol_window: {config.vol_window}")
    print(f"   q_extreme_trend: {config.q_extreme_trend}")
    print(f"   q_manip: {config.q_manip}")
    
    # Generate signals
    print(f"\n🎯 Generating signals...")
    signal_exec = generate_pure_factor_signals(bars, config)
    n_signals = signal_exec.sum()
    print(f"   Total signals: {n_signals:,}")
    print(f"   Signal rate: {n_signals/len(bars)*100:.2f}%")
    
    # Compute ATR
    print(f"\n📊 Computing ATR...")
    atr = compute_atr(bars, window=config.atr_window)
    print(f"   Mean ATR: ${atr.mean():.2f}")
    print(f"   Median ATR: ${atr.median():.2f}")
    
    # Configure trade path analysis
    tp_config = TradePathConfig(
        max_loss_atr=5.0,  # Allow up to 5 ATR loss before forced exit
        max_holding_bars=None,  # No time limit - let trades run until exit conditions
        price_col_for_pnl="close",  # Use close price for PnL calculation
        entry_price_col="open"  # Enter at open price
    )

    print(f"\n🔬 Trade Path Analysis Configuration:")
    print(f"   Max loss: {tp_config.max_loss_atr} ATR")
    print(f"   Max holding: {'Unlimited' if tp_config.max_holding_bars is None else f'{tp_config.max_holding_bars} bars'}")
    print(f"   Entry price: {tp_config.entry_price_col}")
    print(f"   PnL price: {tp_config.price_col_for_pnl}")
    
    # Run trade path analysis
    print(f"\n🚀 Running trade path analysis...")
    trades_df = analyze_trade_paths_long_only(bars, signal_exec, atr, tp_config)
    
    print(f"   Analyzed {len(trades_df):,} trades")
    
    # Compute summary statistics
    summary = summarize_trade_paths(trades_df)
    
    # Print summary
    print_trade_path_summary(summary, title="BTC 4H Pure Factor - Trade Path Analysis")
    
    # Save results
    output_path = Path("results/btc_4h_trade_path_analysis.csv")
    trades_df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")
    
    # Additional insights
    print(f"\n💡 Key Insights:")
    
    # Compare realized vs potential
    avg_realized = summary['avg_pnl'] * 100
    avg_potential = summary['mfe_mean'] * 100
    capture_rate = summary['profit_capture_ratio'] * 100
    
    print(f"\n   Profit Capture Analysis:")
    print(f"   - Average realized PnL: {avg_realized:.2f}%")
    print(f"   - Average potential (MFE): {avg_potential:.2f}%")
    print(f"   - Capture rate: {capture_rate:.1f}%")
    print(f"   → We're leaving {100-capture_rate:.1f}% of potential profit on the table!")
    
    # Timing analysis
    print(f"\n   Optimal Exit Timing:")
    print(f"   - Max profit typically occurs at bar {summary['t_mfe_median']:.0f}")
    print(f"   - Current time exit: 5 bars")
    if summary['t_mfe_median'] < 5:
        print(f"   → Consider SHORTER holding period (~{int(summary['t_mfe_median'])} bars)")
    elif summary['t_mfe_median'] > 5:
        print(f"   → Consider LONGER holding period (~{int(summary['t_mfe_median'])} bars)")
    else:
        print(f"   → Current 5-bar exit is close to optimal")
    
    # Exit reason analysis
    print(f"\n   Exit Reason Analysis:")
    for reason, count in summary['exit_reasons'].items():
        pct = count / summary['n_trades'] * 100
        print(f"   - {reason}: {pct:.1f}%")
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

