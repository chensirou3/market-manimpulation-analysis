"""
4H Strategy Enhancement Study: Daily Confluence + Clustering Filters

This experiment compares 4 variants of the 4h extreme reversal strategy:
A) Baseline 4h strategy (no extra filters)
B) 4h + daily confluence filter
C) 4h + clustering filter
D) 4h + daily confluence + clustering (both filters)

Goal: Determine if multi-timeframe and clustering filters improve signal quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.extreme_reversal_4h_enhanced import generate_4h_signals_with_filters
from src.strategies.backtest_reversal import run_extreme_reversal_backtest


def load_4h_bars():
    """Load 4h bars with ManipScore"""
    file_path = Path('results/bars_4h_with_manipscore_full.csv')
    bars = pd.read_csv(file_path, index_col=0, parse_dates=True)
    return bars


def load_daily_bars():
    """Load daily bars with ManipScore"""
    file_path = Path('results/bars_1d_with_manipscore_full.csv')
    bars = pd.read_csv(file_path, index_col=0, parse_dates=True)
    return bars


def run_variant(
    bars_4h: pd.DataFrame,
    bars_1d: pd.DataFrame,
    variant_name: str,
    use_daily: bool,
    use_clustering: bool,
    strategy_type: str = 'asymmetric'
) -> dict:
    """
    Run a single strategy variant.

    Args:
        bars_4h: 4h bars
        bars_1d: Daily bars
        variant_name: Name of variant
        use_daily: Enable daily confluence filter
        use_clustering: Enable clustering filter
        strategy_type: 'reversal' or 'asymmetric' (default: 'asymmetric')

    Returns:
        dict with results
    """
    print(f"\n{'='*80}")
    print(f"Running: {variant_name} ({strategy_type})")
    print(f"{'='*80}\n")

    # Create config
    config = ExtremeReversalConfig(
        bar_size='4h',
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5,
        tp_atr_mult=0.8,
        # Filter flags
        use_daily_confluence=use_daily,
        daily_q_extreme_trend=0.9,
        daily_q_high_manip=0.9,
        use_clustering_filter=use_clustering,
        clustering_q_high_manip=0.9,
        clustering_window_W=6,
        clustering_min_count=3,
    )

    # Generate signals
    bars_with_signals = generate_4h_signals_with_filters(
        bars_4h.copy(),
        bars_1d if use_daily else None,
        config,
        strategy_type=strategy_type
    )
    
    n_signals = (bars_with_signals['exec_signal'] != 0).sum()
    print(f"\nTotal signals: {n_signals}")
    
    if n_signals < 10:
        print("⚠️ Too few signals, skipping backtest")
        return None
    
    # Run backtest
    print("\nRunning backtest...")
    result = run_extreme_reversal_backtest(
        bars_with_signals,
        bars_with_signals['exec_signal'],
        config,
        initial_capital=10000.0
    )
    
    # Extract stats
    stats = result.stats.copy()
    stats['variant'] = variant_name
    stats['use_daily'] = use_daily
    stats['use_clustering'] = use_clustering
    
    print(f"\nResults:")
    print(f"  Sharpe: {stats['sharpe_ratio']:.2f}")
    print(f"  Total return: {stats['total_return']*100:.2f}%")
    print(f"  Win rate: {stats['win_rate']*100:.1f}%")
    print(f"  Max drawdown: {stats['max_drawdown']*100:.2f}%")
    print(f"  Trades: {stats['n_trades']}")
    
    return stats


def main():
    print("="*80)
    print("4H STRATEGY ENHANCEMENT STUDY")
    print("="*80)
    print()
    print("Strategy: ASYMMETRIC (UP=continuation, DOWN=reversal)")
    print()
    print("Testing 4 variants:")
    print("  A) Baseline (no filters)")
    print("  B) + Daily confluence")
    print("  C) + Clustering")
    print("  D) + Daily + Clustering")
    print()

    # Load data
    print("Loading data...")
    bars_4h = load_4h_bars()
    bars_1d = load_daily_bars()
    print(f"  4h bars: {len(bars_4h):,}")
    print(f"  Daily bars: {len(bars_1d):,}")
    print(f"  Date range: {bars_4h.index[0]} to {bars_4h.index[-1]}")
    print()

    # Define variants
    variants = [
        ('A_Baseline', False, False),
        ('B_Daily', True, False),
        ('C_Clustering', False, True),
        ('D_Daily_Clustering', True, True),
    ]

    # Run all variants
    all_results = []

    for variant_name, use_daily, use_clustering in variants:
        result = run_variant(
            bars_4h,
            bars_1d,
            variant_name,
            use_daily,
            use_clustering,
            strategy_type='asymmetric'
        )

        if result is not None:
            all_results.append(result)
    
    # Save results
    if len(all_results) > 0:
        df_results = pd.DataFrame(all_results)
        
        output_file = Path('results/4h_filter_comparison_stats.csv')
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ Saved: {output_file}")
        
        # Print comparison table
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        print()
        print(f"{'Variant':<20} {'Signals':<10} {'Sharpe':<10} {'Total Ret':<12} {'Win Rate':<12} {'Max DD':<10}")
        print("-"*80)
        
        for _, row in df_results.iterrows():
            print(f"{row['variant']:<20} {row['n_trades']:<10} {row['sharpe_ratio']:>8.2f}  {row['total_return']*100:>8.2f}%   {row['win_rate']*100:>8.1f}%     {row['max_drawdown']*100:>8.2f}%")
    
    print("\n" + "="*80)
    print("STUDY COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

