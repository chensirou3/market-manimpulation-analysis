"""
Simple test for trade path analysis module with synthetic data
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


def create_synthetic_data(n_bars=1000, seed=42):
    """Create synthetic bar data for testing"""
    np.random.seed(seed)
    
    # Generate timestamps
    timestamps = pd.date_range('2020-01-01', periods=n_bars, freq='4H')
    
    # Generate price data with trend + noise
    trend = np.linspace(40000, 50000, n_bars)
    noise = np.random.randn(n_bars) * 500
    close = trend + noise
    
    # Generate OHLC
    high = close + np.abs(np.random.randn(n_bars) * 200)
    low = close - np.abs(np.random.randn(n_bars) * 200)
    open_price = close + np.random.randn(n_bars) * 100
    
    # Create DataFrame
    bars = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close
    }, index=timestamps)
    
    return bars


def create_synthetic_signals(bars, signal_rate=0.05, seed=42):
    """Create synthetic trading signals"""
    np.random.seed(seed)
    
    # Random signals with specified rate
    signals = pd.Series(0, index=bars.index)
    n_signals = int(len(bars) * signal_rate)
    signal_indices = np.random.choice(len(bars), size=n_signals, replace=False)
    signals.iloc[signal_indices] = 1
    
    return signals


def compute_atr(bars, window=10):
    """Compute ATR"""
    high = bars['high']
    low = bars['low']
    close = bars['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    return atr


def main():
    print("\n" + "="*80)
    print("Testing Trade Path Analysis Module")
    print("="*80)
    
    # Create synthetic data
    print("\n📊 Creating synthetic data...")
    bars = create_synthetic_data(n_bars=1000)
    print(f"   Generated {len(bars):,} bars")
    print(f"   Price range: ${bars['close'].min():.0f} - ${bars['close'].max():.0f}")
    
    # Create signals
    print("\n🎯 Creating synthetic signals...")
    signals = create_synthetic_signals(bars, signal_rate=0.05)
    print(f"   Generated {signals.sum():,} signals ({signals.sum()/len(bars)*100:.1f}%)")
    
    # Compute ATR
    print("\n📈 Computing ATR...")
    atr = compute_atr(bars, window=10)
    print(f"   Mean ATR: ${atr.mean():.2f}")
    
    # Configure analysis
    config = TradePathConfig(
        max_loss_atr=5.0,
        max_holding_bars=None,  # No time limit - let trades run
        price_col_for_pnl="close",
        entry_price_col="open"
    )

    print("\n⚙️  Configuration:")
    print(f"   Max loss: {config.max_loss_atr} ATR")
    print(f"   Max holding: {'Unlimited' if config.max_holding_bars is None else f'{config.max_holding_bars} bars'}")
    
    # Run analysis
    print("\n🚀 Running trade path analysis...")
    trades_df = analyze_trade_paths_long_only(bars, signals, atr, config)
    
    print(f"   Analyzed {len(trades_df):,} trades")
    
    if len(trades_df) > 0:
        # Show sample trades
        print("\n📋 Sample trades:")
        print(trades_df.head(10).to_string())
        
        # Compute summary
        summary = summarize_trade_paths(trades_df)
        
        # Print summary
        print_trade_path_summary(summary, title="Synthetic Data - Trade Path Analysis")
        
        # Additional analysis
        print("\n🔍 Detailed Analysis:")
        print(f"\n   MFE Distribution (ATR units):")
        print(f"   - Min: {trades_df['mfe_atr'].min():.2f}")
        print(f"   - 25%: {trades_df['mfe_atr'].quantile(0.25):.2f}")
        print(f"   - 50%: {trades_df['mfe_atr'].quantile(0.50):.2f}")
        print(f"   - 75%: {trades_df['mfe_atr'].quantile(0.75):.2f}")
        print(f"   - Max: {trades_df['mfe_atr'].max():.2f}")
        
        print(f"\n   MAE Distribution (ATR units):")
        print(f"   - Min: {trades_df['mae_atr'].min():.2f}")
        print(f"   - 25%: {trades_df['mae_atr'].quantile(0.25):.2f}")
        print(f"   - 50%: {trades_df['mae_atr'].quantile(0.50):.2f}")
        print(f"   - 75%: {trades_df['mae_atr'].quantile(0.75):.2f}")
        print(f"   - Max: {trades_df['mae_atr'].max():.2f}")
        
        print(f"\n   Timing of MFE (bars after entry):")
        print(f"   - Min: {trades_df['t_mfe'].min():.0f}")
        print(f"   - 25%: {trades_df['t_mfe'].quantile(0.25):.0f}")
        print(f"   - 50%: {trades_df['t_mfe'].quantile(0.50):.0f}")
        print(f"   - 75%: {trades_df['t_mfe'].quantile(0.75):.0f}")
        print(f"   - Max: {trades_df['t_mfe'].max():.0f}")
        
        # Save results
        output_path = Path("results/test_trade_path_analysis.csv")
        output_path.parent.mkdir(exist_ok=True)
        trades_df.to_csv(output_path, index=False)
        print(f"\n💾 Results saved to: {output_path}")
    else:
        print("\n⚠️  No trades generated!")
    
    print("\n" + "="*80)
    print("Test complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

