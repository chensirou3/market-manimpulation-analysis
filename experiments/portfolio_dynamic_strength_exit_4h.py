# -*- coding: utf-8 -*-
"""
Portfolio Dynamic Strength-Based Exit Comparison (4H)

Compare three exit strategies at portfolio level:
1. Pure baseline (wide SL, no TP, no time limit)
2. Best static/trailing rule from previous experiments
3. Dynamic strength-based exit (Layer 3)

For BTCUSD 4H and XAUUSD 4H.
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
    attach_strength_to_trade_paths
)
from src.backtest.portfolio_backtest import run_portfolio_backtest_with_exit_rule
from src.backtest.portfolio_backtest_dynamic import run_portfolio_backtest_with_dynamic_exit
from src.backtest.exit_rules_portfolio import PortfolioExitRule


def load_bars(symbol: str, timeframe: str = "4h", L_past: int = 5, vol_window: int = 20) -> pd.DataFrame:
    """Load 4H bars with ManipScore and compute TS if needed"""
    # Try different naming conventions
    symbol_lower = symbol.lower().replace('usd', '')  # btc, xau, eth

    possible_paths = [
        project_root / f"results/{symbol}_{timeframe}_bars_with_manipscore_full.csv",
        project_root / f"results/bars_{timeframe}_{symbol_lower}_with_manipscore_full.csv",
        project_root / f"results/bars_{timeframe}_{symbol_lower}_full_with_manipscore.csv",
        project_root / f"results/bars_{timeframe}_with_manipscore_full.csv",  # For XAUUSD
    ]

    for file_path in possible_paths:
        if file_path.exists():
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp').sort_index()

            # Compute TS if not present
            if 'TS' not in df.columns:
                # Compute returns if not present
                if 'returns' in df.columns:
                    ret = df['returns']
                elif 'log_return' in df.columns:
                    ret = df['log_return']
                else:
                    ret = np.log(df['close'] / df['close'].shift(1))

                # TS = R_past / sigma
                R_past = ret.rolling(window=L_past).sum()
                sigma = ret.rolling(window=vol_window).std()
                sigma = sigma.replace(0, np.nan)
                df['TS'] = R_past / sigma

            return df

    raise FileNotFoundError(f"Could not find bars file for {symbol} {timeframe}. Tried: {possible_paths}")


def ensure_atr(bars: pd.DataFrame, window: int = 14) -> pd.Series:
    """Compute or load ATR"""
    if 'atr' in bars.columns:
        return bars['atr']
    
    # Compute ATR
    high = bars['high']
    low = bars['low']
    close = bars['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    return atr


def generate_4h_long_signals(bars: pd.DataFrame, L_past: int = 5, vol_window: int = 20) -> pd.Series:
    """
    Generate 4H long-only extreme reversal signals (asymmetric).

    Logic:
        - Extreme UP (TS > threshold, ret > 0, ManipScore > threshold) → LONG (+1, continuation)
        - Extreme DOWN (TS < -threshold, ret < 0, ManipScore > threshold) → LONG (+1, reversal)
    """
    # Ensure ManipScore exists
    if 'ManipScore' not in bars.columns:
        raise ValueError("Bars must have 'ManipScore' column")

    # Compute returns if not present
    if 'returns' in bars.columns:
        ret = bars['returns']
    elif 'log_return' in bars.columns:
        ret = bars['log_return']
    else:
        ret = np.log(bars['close'] / bars['close'].shift(1))

    # Compute TS if not present
    if 'TS' not in bars.columns:
        # TS = R_past / sigma
        # R_past = cumulative return over L_past bars
        R_past = ret.rolling(window=L_past).sum()

        # sigma = rolling volatility over vol_window bars
        sigma = ret.rolling(window=vol_window).std()

        # Avoid division by zero
        sigma = sigma.replace(0, np.nan)

        TS = R_past / sigma
    else:
        TS = bars['TS']

    # Compute thresholds (90th percentile of |TS|)
    ts_threshold = TS.abs().quantile(0.90)
    ms_threshold = bars['ManipScore'].quantile(0.90)

    # Asymmetric logic
    extreme_up = (TS > ts_threshold) & (ret > 0) & (bars['ManipScore'] > ms_threshold)
    extreme_down = (TS < -ts_threshold) & (ret < 0) & (bars['ManipScore'] > ms_threshold)

    signal = (extreme_up | extreme_down).astype(int)

    return signal


def load_trade_paths(symbol: str, timeframe: str = "4h") -> pd.DataFrame:
    """Load trade path data"""
    symbol_lower = symbol.lower().replace('usd', '')  # btc, xau, eth

    possible_paths = [
        project_root / f"results/{symbol}_{timeframe}_trade_path.csv",
        project_root / f"results/{symbol_lower}_{timeframe}_trade_path_steps.csv",
        project_root / f"results/{symbol_lower}_{timeframe}_trade_path_analysis.csv",
    ]

    for file_path in possible_paths:
        if file_path.exists():
            df = pd.read_csv(file_path)

            # Convert time columns to datetime
            for col in ['timestamp', 'entry_time', 'exit_time']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])

            # If we have entry_time but not timestamp, use entry_time as timestamp
            if 'timestamp' not in df.columns and 'entry_time' in df.columns:
                df['timestamp'] = df['entry_time']

            return df

    raise FileNotFoundError(f"Trade path file not found for {symbol} {timeframe}. Tried: {possible_paths}")


def get_baseline_rules(symbol: str) -> tuple:
    """
    Get baseline exit rules for comparison.
    
    Returns:
        (pure_rule, best_rule)
    """
    if symbol == "BTCUSD":
        pure_rule = PortfolioExitRule(
            name="PURE_BASELINE",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
        
        best_rule = PortfolioExitRule(
            name="BEST_STATIC_Trail_T2_L1_SL3",
            bar_size="4h",
            sl_atr_mult=3.0,
            tp_atr_mult=np.inf,
            max_holding_bars=20,
            trail_trigger_atr=2.0,
            trail_lock_atr=1.0
        )
    else:  # XAUUSD
        pure_rule = PortfolioExitRule(
            name="PURE_BASELINE",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
        
        best_rule = PortfolioExitRule(
            name="BEST_STATIC_SL5_NoTP",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=30,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
    
    return pure_rule, best_rule


def build_stats_row(symbol: str, variant: str, stats: dict) -> dict:
    """Build a row for summary table"""
    return {
        'symbol': symbol,
        'variant': variant,
        'total_return': stats.get('total_return', 0.0),
        'ann_return': stats.get('ann_return', 0.0),
        'ann_vol': stats.get('ann_vol', 0.0),
        'sharpe': stats.get('sharpe', 0.0),
        'max_drawdown': stats.get('max_drawdown', 0.0),
        'num_trades': stats.get('num_trades', 0),
        'win_rate': stats.get('win_rate', 0.0),
        'avg_pnl_per_trade': stats.get('avg_pnl_per_trade', 0.0),
        # Strength-specific stats (only for dynamic variant)
        'strong_count': stats.get('strong_count', 0),
        'strong_win_rate': stats.get('strong_win_rate', 0.0),
        'strong_avg_pnl': stats.get('strong_avg_pnl', 0.0),
        'medium_count': stats.get('medium_count', 0),
        'medium_win_rate': stats.get('medium_win_rate', 0.0),
        'medium_avg_pnl': stats.get('medium_avg_pnl', 0.0),
        'weak_count': stats.get('weak_count', 0),
        'weak_win_rate': stats.get('weak_win_rate', 0.0),
        'weak_avg_pnl': stats.get('weak_avg_pnl', 0.0),
    }


def main():
    """
    Main experiment: compare pure, best_static, and dynamic_strength exits
    for BTCUSD 4H and XAUUSD 4H.
    """
    print("=" * 80)
    print("Portfolio Dynamic Strength-Based Exit Comparison (4H)")
    print("=" * 80)

    symbols = ["BTCUSD", "XAUUSD"]
    timeframe = "4h"
    rows = []

    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"Processing {symbol} {timeframe}")
        print(f"{'='*80}")

        # Load data
        print(f"Loading bars for {symbol}...")
        bars = load_bars(symbol, timeframe)

        # Filter date range (2016-2024)
        bars = bars.loc['2016-01-01':'2024-12-31']

        print(f"  Loaded {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")

        # Compute ATR
        atr = ensure_atr(bars)

        # Generate signals
        print(f"Generating signals...")
        signal_exec = generate_4h_long_signals(bars)
        num_signals = signal_exec.sum()
        print(f"  Generated {num_signals} signals")

        # Compute entry features directly from signals
        print(f"Computing entry features from signals...")

        # Get signal timestamps
        signal_times = bars.index[signal_exec == 1]

        if len(signal_times) > 0:
            # Create entry features DataFrame
            entry_data = []
            for i, entry_time in enumerate(signal_times):
                if entry_time in bars.index:
                    bar = bars.loc[entry_time]
                    entry_data.append({
                        'trade_id': i + 1,
                        'entry_time': entry_time,
                        'entry_TS': bar.get('TS', np.nan),
                        'entry_ManipScore': bar.get('ManipScore', np.nan)
                    })

            entry_features = pd.DataFrame(entry_data)
            entry_features = label_signal_strength(entry_features)

            # Print strength distribution
            strength_dist = entry_features['signal_strength'].value_counts()
            print(f"  Signal strength distribution:")
            for strength, count in strength_dist.items():
                pct = count / len(entry_features) * 100
                print(f"    {strength}: {count} ({pct:.1f}%)")
        else:
            print(f"  WARNING: No signals found for {symbol}")
            entry_features = None

        # Get baseline rules
        pure_rule, best_rule = get_baseline_rules(symbol)

        # 1) Pure baseline
        print(f"\n[1/3] Running PURE baseline...")
        result_pure = run_portfolio_backtest_with_exit_rule(
            bars, signal_exec, atr, pure_rule
        )
        rows.append(build_stats_row(symbol, "pure", result_pure["stats"]))
        print(f"  Sharpe: {result_pure['stats']['sharpe']:.2f}, "
              f"Total Return: {result_pure['stats']['total_return']*100:.2f}%")

        # 2) Best static/trailing baseline
        print(f"\n[2/3] Running BEST_STATIC baseline...")
        result_best = run_portfolio_backtest_with_exit_rule(
            bars, signal_exec, atr, best_rule
        )
        rows.append(build_stats_row(symbol, "best_static", result_best["stats"]))
        print(f"  Sharpe: {result_best['stats']['sharpe']:.2f}, "
              f"Total Return: {result_best['stats']['total_return']*100:.2f}%")

        # 3) Dynamic strength-based exit
        if entry_features is not None:
            print(f"\n[3/3] Running DYNAMIC_STRENGTH exit...")
            result_dyn = run_portfolio_backtest_with_dynamic_exit(
                bars, signal_exec, atr, entry_features, symbol
            )
            rows.append(build_stats_row(symbol, "dynamic_strength", result_dyn["stats"]))
            print(f"  Sharpe: {result_dyn['stats']['sharpe']:.2f}, "
                  f"Total Return: {result_dyn['stats']['total_return']*100:.2f}%")

            # Print strength breakdown
            stats = result_dyn['stats']
            print(f"\n  Strength breakdown:")
            for strength in ['strong', 'medium', 'weak']:
                count = stats.get(f'{strength}_count', 0)
                wr = stats.get(f'{strength}_win_rate', 0.0)
                avg_pnl = stats.get(f'{strength}_avg_pnl', 0.0)
                print(f"    {strength}: {count} trades, WR={wr*100:.1f}%, Avg PnL={avg_pnl*100:.2f}%")

            # Save detailed results
            result_dyn['trades'].to_csv(
                project_root / f"results/{symbol}_4h_dynamic_strength_trades.csv",
                index=False
            )
            result_dyn['equity_curve'].to_csv(
                project_root / f"results/{symbol}_4h_dynamic_strength_equity.csv"
            )
        else:
            print(f"\n[3/3] Skipping DYNAMIC_STRENGTH exit (no trade path data)")

    # Save summary
    df_summary = pd.DataFrame(rows)

    # Format percentages
    pct_cols = ['total_return', 'ann_return', 'ann_vol', 'max_drawdown', 'win_rate',
                'avg_pnl_per_trade', 'strong_win_rate', 'strong_avg_pnl',
                'medium_win_rate', 'medium_avg_pnl', 'weak_win_rate', 'weak_avg_pnl']

    output_path = project_root / "results/portfolio_dynamic_strength_exit_4h_summary.csv"
    df_summary.to_csv(output_path, index=False)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(df_summary[['symbol', 'variant', 'total_return', 'sharpe', 'win_rate',
                      'num_trades', 'max_drawdown']].to_string(index=False))

    print(f"\n✅ Results saved to: {output_path}")
    print(f"✅ Detailed trades and equity curves saved to results/")


if __name__ == "__main__":
    main()

