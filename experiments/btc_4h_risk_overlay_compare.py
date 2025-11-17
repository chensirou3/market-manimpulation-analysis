# -*- coding: utf-8 -*-
"""
BTCUSD 4H Risk Overlay Comparison Experiment

Test two risk management overlays on the Phase 23 dynamic strength exit strategy:
1. Weak signal filtering - suppress entry signals labeled as 'weak'
2. Drawdown-based position scaling - reduce position size during deep drawdowns

Goal: Reduce max drawdown (from ~-74% to closer to -40%) with minimal sacrifice in returns.

Four variants tested:
- baseline: Dynamic strength exit, no filters
- weak_filter: Filter weak signals only
- dd_scaling: Drawdown-based scaling only
- combined: Both weak filter + DD scaling
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

# Import modules
from src.analysis.trade_strength_features import (
    compute_trade_entry_features,
    label_signal_strength,
)
from src.analysis.risk_overlays import (
    filter_weak_signals,
    apply_drawdown_based_scaling_to_trades,
    compute_portfolio_stats_from_equity
)
from src.backtest.portfolio_backtest_dynamic import run_portfolio_backtest_with_dynamic_exit
from src.strategies.backtest_reversal import compute_atr


def load_btc_4h_bars(start_date: str = "2017-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """Load BTCUSD 4H bars with ManipScore"""
    possible_paths = [
        project_root / "results/bars_4h_btc_full_with_manipscore.csv",
        project_root / "results/BTCUSD_4h_bars_with_manipscore_full.csv",
    ]
    
    for file_path in possible_paths:
        if file_path.exists():
            print(f"Loading BTCUSD 4H bars from: {file_path.name}")
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df = df.set_index('timestamp').sort_index()
            
            # Filter to test period
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            print(f"Loaded {len(df)} bars from {df.index[0]} to {df.index[-1]}")
            return df
    
    raise FileNotFoundError(f"Could not find BTCUSD 4H bars file. Tried: {possible_paths}")


def generate_btc_4h_long_signals_with_strength(
    bars: pd.DataFrame,
    L_past: int = 5,
    vol_window: int = 20
) -> pd.DataFrame:
    """
    Generate long-only extreme reversal signals with strength labels.
    
    Returns:
        DataFrame with columns:
        - 'signal_exec': {0,1} execution signal
        - 'signal_strength': {'strong','medium','weak'} for entry bars (empty otherwise)
        - 'entry_TS': TS at entry
        - 'entry_ManipScore': ManipScore at entry
    """
    if 'ManipScore' not in bars.columns:
        raise ValueError("Bars must have 'ManipScore' column")
    
    # Compute returns
    if 'returns' in bars.columns:
        ret = bars['returns']
    elif 'log_return' in bars.columns:
        ret = bars['log_return']
    else:
        ret = np.log(bars['close'] / bars['close'].shift(1))
    
    # Compute TS
    if 'TS' not in bars.columns:
        R_past = ret.rolling(window=L_past).sum()
        sigma = ret.rolling(window=vol_window).std()
        sigma = sigma.replace(0, np.nan)
        TS = R_past / sigma
        bars = bars.copy()
        bars['TS'] = TS
    else:
        TS = bars['TS']
    
    # Compute thresholds (90th percentile)
    ts_threshold = TS.abs().quantile(0.90)
    ms_threshold = bars['ManipScore'].quantile(0.90)
    
    # Asymmetric logic: UP=continuation, DOWN=reversal
    extreme_up = (TS > ts_threshold) & (ret > 0) & (bars['ManipScore'] > ms_threshold)
    extreme_down = (TS < -ts_threshold) & (ret < 0) & (bars['ManipScore'] > ms_threshold)
    
    signal_exec = (extreme_up | extreme_down).astype(int)
    
    # Label signal strength for entry bars
    # Create a DataFrame with entry features
    entry_indices = signal_exec[signal_exec == 1].index
    
    entry_features = pd.DataFrame(index=bars.index)
    entry_features['signal_exec'] = signal_exec
    entry_features['signal_strength'] = ''
    entry_features['entry_TS'] = np.nan
    entry_features['entry_ManipScore'] = np.nan
    
    if len(entry_indices) > 0:
        # For entry bars, record TS and ManipScore
        entry_features.loc[entry_indices, 'entry_TS'] = TS.loc[entry_indices].values
        entry_features.loc[entry_indices, 'entry_ManipScore'] = bars.loc[entry_indices, 'ManipScore'].values
        
        # Compute strength quantiles based on ALL entry signals
        entry_ts_abs = entry_features.loc[entry_indices, 'entry_TS'].abs()
        entry_ms = entry_features.loc[entry_indices, 'entry_ManipScore']
        
        ts_q30 = entry_ts_abs.quantile(0.30)
        ts_q70 = entry_ts_abs.quantile(0.70)
        ms_q30 = entry_ms.quantile(0.30)
        ms_q70 = entry_ms.quantile(0.70)
        
        # Label strength
        for idx in entry_indices:
            ts_abs = abs(entry_features.loc[idx, 'entry_TS'])
            ms = entry_features.loc[idx, 'entry_ManipScore']
            
            if ts_abs >= ts_q70 and ms >= ms_q70:
                strength = 'strong'
            elif ts_abs <= ts_q30 and ms <= ms_q30:
                strength = 'weak'
            else:
                strength = 'medium'
            
            entry_features.loc[idx, 'signal_strength'] = strength
    
    return entry_features


def main():
    print("=" * 100)
    print("BTCUSD 4H RISK OVERLAY COMPARISON EXPERIMENT")
    print("=" * 100)
    print()

    # [1] Load BTCUSD 4H bars
    print("[1/7] Loading BTCUSD 4H bars...")
    bars = load_btc_4h_bars()
    print()

    # [2] Compute ATR
    print("[2/7] Computing ATR...")
    atr = compute_atr(bars, window=14)
    print(f"ATR computed: mean={atr.mean():.2f}, median={atr.median():.2f}")
    print()

    # [3] Generate signals with strength labels
    print("[3/7] Generating long-only extreme reversal signals with strength labels...")
    signals_df = generate_btc_4h_long_signals_with_strength(bars)
    signal_exec = signals_df['signal_exec']
    signal_strength = signals_df['signal_strength']

    num_signals = signal_exec.sum()
    num_strong = (signal_strength == 'strong').sum()
    num_medium = (signal_strength == 'medium').sum()
    num_weak = (signal_strength == 'weak').sum()

    print(f"Total signals: {num_signals}")
    print(f"  Strong: {num_strong} ({num_strong/num_signals*100:.1f}%)")
    print(f"  Medium: {num_medium} ({num_medium/num_signals*100:.1f}%)")
    print(f"  Weak: {num_weak} ({num_weak/num_signals*100:.1f}%)")
    print()

    # [4] Prepare entry features for dynamic backtest
    print("[4/7] Preparing entry features for dynamic backtest...")
    entry_features = signals_df[signals_df['signal_exec'] == 1][['signal_strength', 'entry_TS', 'entry_ManipScore']].copy()
    entry_features['entry_time'] = entry_features.index
    entry_features = entry_features.reset_index(drop=True)
    print(f"Entry features prepared: {len(entry_features)} entries")
    print()

    # [5] Run four variants
    print("[5/7] Running backtests for four variants...")
    print()

    results = {}

    # ========== Variant 1: Baseline ==========
    print("  [A] Baseline (no filters)...")
    result_base = run_portfolio_backtest_with_dynamic_exit(
        bars=bars,
        signal_exec=signal_exec,
        atr=atr,
        entry_features=entry_features,
        symbol="BTCUSD",
        cost_per_trade=0.0007,
        initial_equity=10000.0
    )
    trades_base = result_base['trades']
    equity_base = result_base['equity_curve']
    stats_base = result_base['stats']

    print(f"    Sharpe: {stats_base['sharpe']:.2f}")
    print(f"    Total Return: {stats_base['total_return']*100:.2f}%")
    print(f"    Max Drawdown: {stats_base['max_drawdown']*100:.2f}%")
    print(f"    Num Trades: {stats_base['num_trades']}")
    print()

    results['baseline'] = {
        'trades': trades_base,
        'equity': equity_base,
        'stats': stats_base
    }

    # ========== Variant 2: Weak Filter Only ==========
    print("  [B] Weak filter only...")
    signal_exec_weak_filtered = filter_weak_signals(signal_exec, signal_strength)

    # Update entry features to exclude weak signals
    entry_features_weak = signals_df[signal_exec_weak_filtered == 1][['signal_strength', 'entry_TS', 'entry_ManipScore']].copy()
    entry_features_weak['entry_time'] = entry_features_weak.index
    entry_features_weak = entry_features_weak.reset_index(drop=True)

    result_weak = run_portfolio_backtest_with_dynamic_exit(
        bars=bars,
        signal_exec=signal_exec_weak_filtered,
        atr=atr,
        entry_features=entry_features_weak,
        symbol="BTCUSD",
        cost_per_trade=0.0007,
        initial_equity=10000.0
    )
    trades_weak = result_weak['trades']
    equity_weak = result_weak['equity_curve']
    stats_weak = result_weak['stats']

    print(f"    Sharpe: {stats_weak['sharpe']:.2f}")
    print(f"    Total Return: {stats_weak['total_return']*100:.2f}%")
    print(f"    Max Drawdown: {stats_weak['max_drawdown']*100:.2f}%")
    print(f"    Num Trades: {stats_weak['num_trades']}")
    print()

    results['weak_filter'] = {
        'trades': trades_weak,
        'equity': equity_weak,
        'stats': stats_weak
    }

    # ========== Variant 3: DD Scaling Only ==========
    print("  [C] Drawdown scaling only...")

    # Apply DD scaling to baseline trades
    equity_dd_scaled, trades_dd_scaled = apply_drawdown_based_scaling_to_trades(
        trades_base.copy(),
        initial_equity=10000.0,
        dd_level_1=-0.30,
        dd_level_2=-0.50,
        scale_level_1=1.0,
        scale_level_2=0.5,
        scale_level_3=0.0
    )

    stats_dd = compute_portfolio_stats_from_equity(
        equity_curve=equity_dd_scaled,
        trades_df=trades_dd_scaled,
        bar_size="4h"
    )

    print(f"    Sharpe: {stats_dd['sharpe']:.2f}")
    print(f"    Total Return: {stats_dd['total_return']*100:.2f}%")
    print(f"    Max Drawdown: {stats_dd['max_drawdown']*100:.2f}%")
    print(f"    Num Trades: {stats_dd['num_trades']}")
    print(f"    Trades at full size: {stats_dd['num_trades_full_size']}")
    print(f"    Trades at half size: {stats_dd['num_trades_half_size']}")
    print(f"    Trades paused: {stats_dd['num_trades_paused']}")
    print()

    results['dd_scaling'] = {
        'trades': trades_dd_scaled,
        'equity': equity_dd_scaled,
        'stats': stats_dd
    }

    # ========== Variant 4: Combined ==========
    print("  [D] Combined (weak filter + DD scaling)...")

    # Apply DD scaling to weak-filtered trades
    equity_comb_scaled, trades_comb_scaled = apply_drawdown_based_scaling_to_trades(
        trades_weak.copy(),
        initial_equity=10000.0,
        dd_level_1=-0.30,
        dd_level_2=-0.50,
        scale_level_1=1.0,
        scale_level_2=0.5,
        scale_level_3=0.0
    )

    stats_comb = compute_portfolio_stats_from_equity(
        equity_curve=equity_comb_scaled,
        trades_df=trades_comb_scaled,
        bar_size="4h"
    )

    print(f"    Sharpe: {stats_comb['sharpe']:.2f}")
    print(f"    Total Return: {stats_comb['total_return']*100:.2f}%")
    print(f"    Max Drawdown: {stats_comb['max_drawdown']*100:.2f}%")
    print(f"    Num Trades: {stats_comb['num_trades']}")
    print(f"    Trades at full size: {stats_comb['num_trades_full_size']}")
    print(f"    Trades at half size: {stats_comb['num_trades_half_size']}")
    print(f"    Trades paused: {stats_comb['num_trades_paused']}")
    print()

    results['combined'] = {
        'trades': trades_comb_scaled,
        'equity': equity_comb_scaled,
        'stats': stats_comb
    }

    # [6] Create summary table
    print("[6/7] Creating summary table...")

    summary_rows = []
    for variant_name in ['baseline', 'weak_filter', 'dd_scaling', 'combined']:
        row = {'variant': variant_name}
        row.update(results[variant_name]['stats'])
        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)

    # [7] Save results
    print("[7/7] Saving results...")

    output_path = project_root / "results/btc_4h_risk_overlay_compare_summary.csv"
    df_summary.to_csv(output_path, index=False)
    print(f"✅ Summary saved to: {output_path.name}")
    print()

    # Print summary table
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(df_summary.to_string(index=False))
    print()

    print("=" * 100)
    print("EXPERIMENT COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()

