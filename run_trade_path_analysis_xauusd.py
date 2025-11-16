"""
Trade Path Analysis for XAUUSD 4H Data

This script runs trade path analysis on existing XAUUSD data
to demonstrate the module and understand factor quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

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


def generate_signals(bars: pd.DataFrame, config: ExtremeReversalConfig) -> pd.Series:
    """Generate pure factor signals (long-only asymmetric)"""
    
    # Compute trend features
    bars = compute_trend_strength(
        bars,
        L_past=config.L_past,
        vol_window=config.vol_window
    )
    
    # Identify extreme trends
    q_up = bars['R_past'].quantile(config.q_extreme_trend)
    q_down = bars['R_past'].quantile(1 - config.q_extreme_trend)
    
    extreme_up = bars['R_past'] >= q_up
    extreme_down = bars['R_past'] <= q_down
    
    # Identify high manipulation
    if 'manipscore' in bars.columns:
        q_manip = bars['manipscore'].quantile(config.q_manip)
        high_manip = bars['manipscore'] >= q_manip
    else:
        print("⚠️  Warning: No manipscore column, using all bars")
        high_manip = pd.Series(True, index=bars.index)
    
    # Generate signals (asymmetric: both up and down extremes → LONG)
    signal_raw = pd.Series(0, index=bars.index)
    signal_raw[(extreme_up | extreme_down) & high_manip] = 1
    
    # Shift to avoid look-ahead bias
    signal_exec = signal_raw.shift(1).fillna(0).astype(int)
    
    return signal_exec


def main():
    """Run trade path analysis on XAUUSD 4H data"""
    
    print("\n" + "="*80)
    print("Trade Path Analysis - XAUUSD 4H Pure Factor Strategy")
    print("="*80)
    
    # Try to find XAUUSD data
    possible_paths = [
        Path("results/bars_4h_with_manipscore_full.csv"),
        Path("results/bars_with_manipscore_2024-01-01_2024-03-31.csv"),
        Path("results/bars_with_manipscore_2024-01-01_2024-12-31.csv"),
    ]
    
    data_path = None
    for p in possible_paths:
        if p.exists():
            data_path = p
            break
    
    if data_path is None:
        print(f"\n❌ ERROR: No XAUUSD data file found")
        print("Tried:")
        for p in possible_paths:
            print(f"  - {p}")
        return
    
    print(f"\n📊 Loading data from: {data_path}")
    bars = pd.read_csv(data_path, index_col=0, parse_dates=True)
    print(f"   Loaded {len(bars):,} bars")
    print(f"   Date range: {bars.index[0]} to {bars.index[-1]}")
    print(f"   Columns: {list(bars.columns)}")
    
    # Resample to 4H if needed
    if '4h' not in str(data_path).lower():
        print(f"\n📈 Resampling to 4H...")
        bars_4h = bars.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Recompute returns
        bars_4h['returns'] = bars_4h['close'].pct_change()
        
        # Copy manipscore if exists (approximate)
        if 'manipscore' in bars.columns:
            bars_4h['manipscore'] = bars['manipscore'].resample('4H').last()
        
        bars = bars_4h
        print(f"   Resampled to {len(bars):,} 4H bars")
    
    # Strategy configuration
    config = ExtremeReversalConfig(
        bar_size='4h',
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,  # Not used in trade path analysis
        atr_window=10
    )
    
    print(f"\n🎯 Generating signals...")
    print(f"   L_past: {config.L_past}")
    print(f"   q_extreme_trend: {config.q_extreme_trend}")
    print(f"   q_manip: {config.q_manip}")
    
    signals = generate_signals(bars, config)
    n_signals = signals.sum()
    print(f"   Generated {n_signals} signals ({n_signals/len(bars)*100:.2f}%)")
    
    # Compute ATR
    print(f"\n📊 Computing ATR...")
    atr = compute_atr(bars, window=config.atr_window)
    print(f"   Mean ATR: ${atr.mean():.2f}")
    
    # Configure trade path analysis
    tp_config = TradePathConfig(
        max_loss_atr=5.0,
        max_holding_bars=None,  # No time limit
        price_col_for_pnl="close",
        entry_price_col="open"
    )
    
    print(f"\n🔬 Trade Path Analysis Configuration:")
    print(f"   Max loss: {tp_config.max_loss_atr} ATR")
    print(f"   Max holding: {'Unlimited' if tp_config.max_holding_bars is None else f'{tp_config.max_holding_bars} bars'}")
    
    # Run analysis
    print(f"\n🚀 Running trade path analysis...")
    trades_df = analyze_trade_paths_long_only(
        bars=bars,
        signal_exec=signals,
        atr=atr,
        config=tp_config
    )
    
    print(f"   Analyzed {len(trades_df)} trades")
    
    # Summarize and print
    print(f"\n" + "="*80)
    summary = summarize_trade_paths(trades_df)
    print_trade_path_summary(summary)
    print("="*80)
    
    # Save results
    output_path = Path("results/xauusd_4h_trade_path_analysis.csv")
    trades_df.to_csv(output_path, index=False)
    print(f"\n💾 Results saved to: {output_path}")
    
    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

