"""
Trade Path Analysis for XAUUSD - All Timeframes

This script runs trade path analysis on XAUUSD data across multiple timeframes
to understand how factor quality varies with timeframe.
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
    elif 'manip_score' in bars.columns:
        q_manip = bars['manip_score'].quantile(config.q_manip)
        high_manip = bars['manip_score'] >= q_manip
    else:
        print("⚠️  Warning: No manipscore column, using all bars")
        high_manip = pd.Series(True, index=bars.index)
    
    # Generate signals (asymmetric: both up and down extremes → LONG)
    signal_raw = pd.Series(0, index=bars.index)
    signal_raw[(extreme_up | extreme_down) & high_manip] = 1
    
    # Shift to avoid look-ahead bias
    signal_exec = signal_raw.shift(1).fillna(0).astype(int)
    
    return signal_exec


def load_and_combine_data():
    """Load all XAUUSD data files and combine them"""

    print("\nLoading XAUUSD data files...")
    
    # Find all data files
    data_files = sorted(Path('results').glob('bars_with_manipscore_*.csv'))
    
    if len(data_files) == 0:
        print("❌ No data files found!")
        return None
    
    print(f"   Found {len(data_files)} files")
    
    # Load and combine
    dfs = []
    for f in data_files:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        dfs.append(df)
        print(f"   Loaded {f.name}: {len(df):,} bars")
    
    # Combine
    bars_5min = pd.concat(dfs, ignore_index=False)
    bars_5min = bars_5min.sort_index()
    
    # Remove duplicates
    bars_5min = bars_5min[~bars_5min.index.duplicated(keep='first')]
    
    print(f"\nCombined data:")
    print(f"   Total bars: {len(bars_5min):,}")
    print(f"   Date range: {bars_5min.index[0]} to {bars_5min.index[-1]}")
    print(f"   Columns: {list(bars_5min.columns)}")
    
    return bars_5min


def resample_to_timeframe(bars_5min: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample 5min bars to target timeframe"""
    
    # Resample OHLCV
    bars = bars_5min.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    # Recompute returns
    bars['returns'] = bars['close'].pct_change()
    
    # Copy manipscore if exists (use last value in period)
    if 'manipscore' in bars_5min.columns:
        bars['manipscore'] = bars_5min['manipscore'].resample(timeframe).last()
    elif 'manip_score' in bars_5min.columns:
        bars['manip_score'] = bars_5min['manip_score'].resample(timeframe).last()
    
    return bars


def analyze_timeframe(bars: pd.DataFrame, timeframe_name: str, timeframe_code: str):
    """Run trade path analysis for a specific timeframe"""
    
    print("\n" + "="*80)
    print(f"Analyzing {timeframe_name}")
    print("="*80)
    
    # Resample if needed
    if timeframe_code != '5min':
        print(f"\nResampling to {timeframe_name}...")
        bars_tf = resample_to_timeframe(bars, timeframe_code)
        print(f"   Resampled to {len(bars_tf):,} bars")
    else:
        bars_tf = bars.copy()

    # Strategy configuration
    config = ExtremeReversalConfig(
        bar_size=timeframe_name,
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10
    )

    print(f"\nGenerating signals...")
    signals = generate_signals(bars_tf, config)
    n_signals = signals.sum()
    print(f"   Generated {n_signals} signals ({n_signals/len(bars_tf)*100:.2f}%)")

    if n_signals == 0:
        print("WARNING: No signals generated, skipping...")
        return None

    # Compute ATR
    atr = compute_atr(bars_tf, window=config.atr_window)

    # Configure trade path analysis
    tp_config = TradePathConfig(
        max_loss_atr=5.0,
        max_holding_bars=None,
        price_col_for_pnl="close",
        entry_price_col="open"
    )

    # Run analysis
    print(f"\nRunning trade path analysis...")
    trades_df = analyze_trade_paths_long_only(
        bars=bars_tf,
        signal_exec=signals,
        atr=atr,
        config=tp_config
    )
    
    print(f"   Analyzed {len(trades_df)} trades")
    
    # Summarize
    summary = summarize_trade_paths(trades_df)
    
    # Save results
    output_path = Path(f"results/xauusd_{timeframe_name}_trade_path_analysis.csv")
    trades_df.to_csv(output_path, index=False)
    
    return summary


def main():
    """Run analysis for all timeframes"""
    
    print("\n" + "="*80)
    print("XAUUSD Trade Path Analysis - All Timeframes")
    print("="*80)
    
    # Load data
    bars_5min = load_and_combine_data()
    
    if bars_5min is None:
        return
    
    # Define timeframes to analyze
    timeframes = {
        '5min': '5min',
        '15min': '15min',
        '30min': '30min',
        '60min': '1H',
        '4h': '4H',
        '1d': '1D'
    }
    
    # Run analysis for each timeframe
    results = {}
    
    for tf_name, tf_code in timeframes.items():
        summary = analyze_timeframe(bars_5min, tf_name, tf_code)
        if summary is not None:
            results[tf_name] = summary
            print("\n" + "-"*80)
            print_trade_path_summary(summary)
            print("-"*80)
    
    # Create comparison table
    print("\n" + "="*80)
    print("Summary Comparison Across Timeframes")
    print("="*80)
    
    comparison_data = []
    for tf_name, summary in results.items():
        comparison_data.append({
            'Timeframe': tf_name,
            'Trades': summary['n_trades'],
            'Win_Rate': f"{summary['win_rate']*100:.1f}%",
            'Avg_PnL': f"{summary['avg_pnl']*100:.2f}%",
            'Avg_MFE': f"{summary['mfe_mean']*100:.2f}%",
            't_mfe_median': f"{summary['t_mfe_median']:.0f}",
            'Profit_Capture': f"{summary['profit_capture_ratio']*100:.1f}%",
            'Avg_Holding': f"{summary['holding_bars_mean']:.1f}"
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    print("\n" + df_comparison.to_string(index=False))
    
    # Save comparison
    output_path = Path("results/xauusd_all_timeframes_comparison.csv")
    df_comparison.to_csv(output_path, index=False)
    print(f"\nComparison saved to: {output_path}")

    print(f"\nAnalysis complete for all timeframes!")


if __name__ == "__main__":
    main()

