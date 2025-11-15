"""
4H Strategy Parameter Sensitivity Analysis

Test different parameter combinations for:
1. Daily confluence filter (different quantiles)
2. Clustering filter (different window sizes and min counts)

Goal: Find optimal filter parameters that improve signal quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.extreme_reversal_4h_enhanced import generate_4h_signals_with_filters
from src.strategies.backtest_reversal import run_extreme_reversal_backtest


def load_data():
    """Load 4h and daily bars"""
    bars_4h = pd.read_csv('results/bars_4h_with_manipscore_full.csv', index_col=0, parse_dates=True)
    bars_1d = pd.read_csv('results/bars_1d_with_manipscore_full.csv', index_col=0, parse_dates=True)
    return bars_4h, bars_1d


def test_clustering_params(bars_4h, bars_1d):
    """Test different clustering parameters"""
    print("\n" + "="*80)
    print("CLUSTERING PARAMETER SENSITIVITY")
    print("="*80)
    
    # Test different combinations
    param_grid = [
        # (window_W, min_count, q_high_manip)
        (4, 2, 0.85),  # More lenient
        (4, 2, 0.90),
        (6, 2, 0.85),
        (6, 2, 0.90),
        (6, 3, 0.85),
        (6, 3, 0.90),  # Current
        (8, 3, 0.85),
        (8, 3, 0.90),
        (8, 4, 0.90),
    ]
    
    results = []
    
    for W, min_count, q_manip in param_grid:
        print(f"\nTesting: W={W}, min_count={min_count}, q_manip={q_manip}")
        
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
            use_clustering_filter=True,
            clustering_q_high_manip=q_manip,
            clustering_window_W=W,
            clustering_min_count=min_count,
        )
        
        bars_with_signals = generate_4h_signals_with_filters(
            bars_4h.copy(),
            None,
            config,
            strategy_type='asymmetric'
        )
        
        n_signals = (bars_with_signals['exec_signal'] != 0).sum()
        print(f"  Signals: {n_signals}")
        
        if n_signals < 20:
            print("  ⚠️ Too few signals, skipping")
            continue
        
        result = run_extreme_reversal_backtest(
            bars_with_signals,
            bars_with_signals['exec_signal'],
            config,
            initial_capital=10000.0
        )
        
        stats = result.stats.copy()
        stats['W'] = W
        stats['min_count'] = min_count
        stats['q_manip'] = q_manip
        
        print(f"  Sharpe: {stats['sharpe_ratio']:.2f}, Return: {stats['total_return']*100:.2f}%, Win rate: {stats['win_rate']*100:.1f}%")
        
        results.append(stats)
    
    return pd.DataFrame(results)


def test_daily_params(bars_4h, bars_1d):
    """Test different daily confluence parameters"""
    print("\n" + "="*80)
    print("DAILY CONFLUENCE PARAMETER SENSITIVITY")
    print("="*80)
    
    # Test different quantiles
    param_grid = [
        # (q_extreme_trend, q_high_manip)
        (0.80, 0.80),  # More lenient
        (0.80, 0.85),
        (0.85, 0.85),
        (0.85, 0.90),
        (0.90, 0.85),
        (0.90, 0.90),  # Current
    ]
    
    results = []
    
    for q_trend, q_manip in param_grid:
        print(f"\nTesting: q_trend={q_trend}, q_manip={q_manip}")
        
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
            use_daily_confluence=True,
            daily_q_extreme_trend=q_trend,
            daily_q_high_manip=q_manip,
        )
        
        bars_with_signals = generate_4h_signals_with_filters(
            bars_4h.copy(),
            bars_1d,
            config,
            strategy_type='asymmetric'
        )
        
        n_signals = (bars_with_signals['exec_signal'] != 0).sum()
        print(f"  Signals: {n_signals}")
        
        if n_signals < 10:
            print("  ⚠️ Too few signals, skipping")
            continue
        
        result = run_extreme_reversal_backtest(
            bars_with_signals,
            bars_with_signals['exec_signal'],
            config,
            initial_capital=10000.0
        )
        
        stats = result.stats.copy()
        stats['q_trend'] = q_trend
        stats['q_manip'] = q_manip
        
        print(f"  Sharpe: {stats['sharpe_ratio']:.2f}, Return: {stats['total_return']*100:.2f}%, Win rate: {stats['win_rate']*100:.1f}%")
        
        results.append(stats)
    
    return pd.DataFrame(results)


def main():
    print("="*80)
    print("4H STRATEGY PARAMETER SENSITIVITY ANALYSIS")
    print("="*80)
    
    bars_4h, bars_1d = load_data()
    print(f"\nData loaded: {len(bars_4h):,} 4h bars, {len(bars_1d):,} daily bars")
    
    # Test clustering parameters
    df_clustering = test_clustering_params(bars_4h, bars_1d)
    if len(df_clustering) > 0:
        df_clustering.to_csv('results/4h_clustering_sensitivity.csv', index=False)
        print("\n✅ Saved: results/4h_clustering_sensitivity.csv")
    
    # Test daily parameters
    df_daily = test_daily_params(bars_4h, bars_1d)
    if len(df_daily) > 0:
        df_daily.to_csv('results/4h_daily_sensitivity.csv', index=False)
        print("\n✅ Saved: results/4h_daily_sensitivity.csv")
    
    print("\n" + "="*80)
    print("SENSITIVITY ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

