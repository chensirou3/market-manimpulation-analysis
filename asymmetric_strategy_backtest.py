"""
Asymmetric Strategy Backtest - All Timeframes

Test asymmetric strategy (UP=continuation, DOWN=reversal) on all timeframes.

Compare:
1. Pure factor (no SL/TP)
2. With SL/TP (risk-managed)

For all timeframes: 5min, 15min, 30min, 60min
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass

from src.strategies import (
    compute_trend_strength,
    compute_extreme_trend_thresholds,
    ExtremeReversalConfig
)
from src.strategies.backtest_reversal import run_extreme_reversal_backtest


@dataclass
class AsymmetricConfig:
    """Configuration for Asymmetric Strategy"""
    bar_size: str = "30min"
    
    # Trend parameters
    L_past: int = 5
    vol_window: int = 20
    q_extreme_trend: float = 0.9
    min_abs_R_past: float = 0.003
    
    # ManipScore parameters
    q_manip: float = 0.9
    min_manip_score: float = 0.7
    
    # Execution parameters
    holding_horizon: int = 5
    atr_window: int = 10
    sl_atr_mult: float = 0.5
    tp_atr_mult: float = 0.8
    cost_per_trade: float = 0.0001


def load_bars(bar_size):
    """Load bars for a specific timeframe"""
    results_dir = Path('results')
    files = sorted(results_dir.glob(f'bars_{bar_size}_with_manipscore_*.csv'))
    
    dfs = []
    for file in files:
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0).sort_index()
    return bars


def generate_asymmetric_signals(bars, config):
    """
    Generate asymmetric strategy signals.
    
    Logic:
    - Extreme UP + high manip → LONG (+1, follow trend)
    - Extreme DOWN + high manip → LONG (+1, reversal/bounce)
    """
    bars = bars.copy()
    
    # Compute trend features
    bars = compute_trend_strength(bars, L_past=config.L_past, vol_window=config.vol_window)
    
    # Compute thresholds
    thresholds = compute_extreme_trend_thresholds(
        bars,
        quantile=config.q_extreme_trend,
        use_normalized=True,
        min_abs_R_past=config.min_abs_R_past
    )
    
    # Identify extreme trends
    threshold_val = thresholds['threshold']
    extreme_up = (bars['R_past'] > 0) & (bars['abs_TS'] >= threshold_val)
    extreme_down = (bars['R_past'] < 0) & (bars['abs_TS'] >= threshold_val)
    
    # Apply minimum absolute R_past filter
    if thresholds['min_abs_R_past'] is not None:
        min_R = thresholds['min_abs_R_past']
        extreme_up = extreme_up & (bars['abs_R_past'] >= min_R)
        extreme_down = extreme_down & (bars['abs_R_past'] >= min_R)
    
    # High ManipScore
    if config.min_manip_score is not None:
        manip_threshold = max(
            bars['ManipScore'].quantile(config.q_manip),
            config.min_manip_score
        )
    else:
        manip_threshold = bars['ManipScore'].quantile(config.q_manip)
    
    high_manip = bars['ManipScore'] >= manip_threshold
    
    # Generate signals - ASYMMETRIC
    bars['raw_signal'] = 0
    bars['extreme_trend'] = False
    bars['high_manip'] = high_manip
    
    # Both UP and DOWN → LONG
    signal_condition = (extreme_up | extreme_down) & high_manip
    bars.loc[signal_condition, 'raw_signal'] = 1
    bars.loc[signal_condition, 'extreme_trend'] = True
    
    # Shift signal to avoid look-ahead bias
    bars['exec_signal'] = bars['raw_signal'].shift(1).fillna(0)
    
    return bars


def run_pure_backtest(bars, config):
    """Run backtest without SL/TP"""
    # Compute forward returns
    bars['forward_return'] = bars['returns'].shift(-1).rolling(config.holding_horizon).sum().shift(-config.holding_horizon+1)
    
    # Compute strategy returns
    bars['strategy_return'] = bars['exec_signal'] * bars['forward_return']
    
    # Filter to trades
    trades = bars[bars['exec_signal'] != 0].copy()
    
    if len(trades) == 0:
        return None
    
    # Compute stats
    n_trades = len(trades)
    total_return = trades['strategy_return'].sum()
    avg_return = trades['strategy_return'].mean()
    std_return = trades['strategy_return'].std()
    
    winners = trades[trades['strategy_return'] > 0]
    losers = trades[trades['strategy_return'] < 0]
    
    win_rate = len(winners) / n_trades if n_trades > 0 else 0
    avg_winner = winners['strategy_return'].mean() if len(winners) > 0 else 0
    avg_loser = losers['strategy_return'].mean() if len(losers) > 0 else 0
    
    sharpe = (avg_return / std_return) * np.sqrt(n_trades) if std_return > 0 else 0
    
    return {
        'n_trades': n_trades,
        'total_return': total_return,
        'avg_return': avg_return,
        'win_rate': win_rate,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'sharpe': sharpe,
    }


def run_managed_backtest(bars, config):
    """Run backtest with SL/TP"""
    result = run_extreme_reversal_backtest(
        bars,
        bars['exec_signal'],
        config,
        initial_capital=10000.0
    )
    
    return result


def main():
    print("="*80)
    print("ASYMMETRIC STRATEGY - FULL BACKTEST")
    print("="*80)
    print()
    print("Strategy: UP=continuation, DOWN=reversal (both LONG)")
    print()
    
    bar_sizes = ['5min', '15min', '30min', '60min']
    
    pure_results = []
    managed_results = []
    
    for bar_size in bar_sizes:
        print(f"\n{'='*80}")
        print(f"Testing {bar_size}")
        print(f"{'='*80}\n")
        
        # Load data
        print(f"Loading {bar_size} data...")
        bars = load_bars(bar_size)
        print(f"Loaded {len(bars):,} bars")
        print()
        
        # Create config
        config = AsymmetricConfig(bar_size=bar_size)
        
        # Generate signals
        print("Generating asymmetric signals...")
        bars_with_signals = generate_asymmetric_signals(bars, config)
        
        n_signals = (bars_with_signals['exec_signal'] != 0).sum()
        print(f"Generated {n_signals:,} signals")
        print()
        
        if n_signals < 10:
            print("⚠️ Too few signals, skipping...")
            continue
        
        # 1. Pure backtest (no SL/TP)
        print("Running PURE backtest (no SL/TP)...")
        pure_perf = run_pure_backtest(bars_with_signals.copy(), config)
        
        if pure_perf:
            print(f"  Trades: {pure_perf['n_trades']:,}")
            print(f"  Total return: {pure_perf['total_return']*100:.2f}%")
            print(f"  Avg return: {pure_perf['avg_return']*10000:.2f} bps")
            print(f"  Win rate: {pure_perf['win_rate']*100:.1f}%")
            print(f"  Sharpe: {pure_perf['sharpe']:.2f}")
            print()
            
            pure_results.append({
                'bar_size': bar_size,
                'type': 'pure',
                **pure_perf
            })
        
        # 2. Managed backtest (with SL/TP)
        print("Running MANAGED backtest (with SL/TP)...")
        managed_result = run_managed_backtest(bars_with_signals.copy(), config)
        
        print(f"  Trades: {managed_result.stats['n_trades']:,}")
        print(f"  Total return: {managed_result.stats['total_return']*100:.2f}%")
        print(f"  Sharpe: {managed_result.stats['sharpe_ratio']:.2f}")
        print(f"  Win rate: {managed_result.stats['win_rate']*100:.1f}%")
        print(f"  Max drawdown: {managed_result.stats['max_drawdown']*100:.2f}%")
        print()
        
        managed_results.append({
            'bar_size': bar_size,
            'type': 'managed',
            **managed_result.stats
        })
        
        print(f"✅ {bar_size} complete")
    
    # Save results
    df_pure = pd.DataFrame(pure_results)
    df_managed = pd.DataFrame(managed_results)
    
    df_pure.to_csv('results/asymmetric_pure_results.csv', index=False)
    df_managed.to_csv('results/asymmetric_managed_results.csv', index=False)
    
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print()
    
    # Pure results
    print("PURE FACTOR (No SL/TP):")
    print(f"{'Timeframe':<10} {'Trades':<10} {'Avg Return':<15} {'Win Rate':<12} {'Sharpe':<10}")
    print("-"*80)
    for _, row in df_pure.iterrows():
        print(f"{row['bar_size']:<10} {row['n_trades']:<10} {row['avg_return']*10000:>8.2f} bps   {row['win_rate']*100:>6.1f}%     {row['sharpe']:>6.2f}")
    
    print()
    print("MANAGED (With SL/TP):")
    print(f"{'Timeframe':<10} {'Trades':<10} {'Total Ret':<12} {'Sharpe':<10} {'Win Rate':<12} {'Max DD':<10}")
    print("-"*80)
    for _, row in df_managed.iterrows():
        print(f"{row['bar_size']:<10} {row['n_trades']:<10} {row['total_return']*100:>6.2f}%    {row['sharpe_ratio']:>6.2f}    {row['win_rate']*100:>6.1f}%     {row['max_drawdown']*100:>6.2f}%")
    
    print("\n✅ Saved:")
    print("  - results/asymmetric_pure_results.csv")
    print("  - results/asymmetric_managed_results.csv")
    
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

