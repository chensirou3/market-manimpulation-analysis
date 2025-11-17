"""
Example usage of static SL/TP backtest system

This script demonstrates how to use the static exit backtest module
for a single symbol with specific parameters.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from src.backtest.static_exit_backtest import (
    StaticExitConfig,
    run_static_exit_backtest,
    compute_atr
)
from src.strategies.extreme_reversal import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals
)


def main():
    """
    Example: Run static SL/TP backtest for XAUUSD 4H
    """
    print("=" * 80)
    print("STATIC SL/TP BACKTEST EXAMPLE - XAUUSD 4H")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data...")
    bars = pd.read_csv(
        project_root / "results" / "bars_4h_with_manipscore_full.csv",
        parse_dates=['timestamp']
    ).set_index('timestamp')
    
    print(f"Loaded {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")
    print(f"Columns: {bars.columns.tolist()}")
    print()
    
    # Compute ATR
    print("Computing ATR...")
    atr = compute_atr(bars, window=10)
    print(f"ATR computed. Mean: {atr.mean():.4f}, Median: {atr.median():.4f}")
    print()
    
    # Generate signals
    print("Generating signals...")
    strategy_config = ExtremeReversalConfig(
        bar_size="4h",
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        use_normalized_trend=True
    )
    
    df_with_signals = generate_extreme_reversal_signals(
        bars,
        strategy_config,
        return_col='returns',
        manip_col='ManipScore'
    )
    
    # Extract long-only signals
    if 'exec_signal' in df_with_signals.columns:
        signal_exec = (df_with_signals['exec_signal'] == 1).astype(int)
    elif 'raw_signal' in df_with_signals.columns:
        signal_exec = (df_with_signals['raw_signal'] == 1).astype(int)
    else:
        raise ValueError("No signal column found")
    
    num_signals = signal_exec.sum()
    print(f"Generated {num_signals} long signals ({num_signals/len(bars)*100:.2f}% of bars)")
    print()
    
    # Run backtest with specific parameters
    print("Running backtest...")
    print("Parameters:")
    print("  SL: 2.0 * ATR")
    print("  TP: 1.5 * ATR")
    print("  Max Holding: 20 bars")
    print("  Cost: 0.07%")
    print()
    
    config = StaticExitConfig(
        bar_size="4h",
        sl_atr_mult=2.0,
        tp_atr_mult=1.5,
        max_holding_bars=20,
        cost_per_trade=0.0007
    )
    
    result = run_static_exit_backtest(bars, signal_exec, atr, config)
    
    # Display results
    print("=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    print()
    
    stats = result['stats']
    print(f"Total Return:        {stats['total_return']:>10.2%}")
    print(f"Annualized Return:   {stats['ann_return']:>10.2%}")
    print(f"Annualized Vol:      {stats['ann_vol']:>10.2%}")
    print(f"Sharpe Ratio:        {stats['sharpe']:>10.2f}")
    print(f"Max Drawdown:        {stats['max_drawdown']:>10.2%}")
    print()
    print(f"Number of Trades:    {stats['num_trades']:>10d}")
    print(f"Win Rate:            {stats['win_rate']:>10.1%}")
    print(f"Avg PnL per Trade:   {stats['avg_pnl_per_trade']:>10.2%}")
    print(f"Avg Winner:          {stats['avg_winner']:>10.2%}")
    print(f"Avg Loser:           {stats['avg_loser']:>10.2%}")
    print(f"Profit Factor:       {stats['profit_factor']:>10.2f}")
    print()
    
    # Display trade details
    trades_df = result['trades']
    print("=" * 80)
    print("TRADE DETAILS (First 10 trades)")
    print("=" * 80)
    print()
    print(trades_df.head(10).to_string(index=False))
    print()
    
    # Exit reason breakdown
    print("=" * 80)
    print("EXIT REASON BREAKDOWN")
    print("=" * 80)
    print()
    exit_counts = trades_df['exit_reason'].value_counts()
    for reason, count in exit_counts.items():
        pct = count / len(trades_df) * 100
        print(f"{reason:>15s}: {count:>5d} ({pct:>5.1f}%)")
    print()
    
    # Equity curve summary
    equity_curve = result['equity_curve']
    print("=" * 80)
    print("EQUITY CURVE SUMMARY")
    print("=" * 80)
    print()
    print(f"Initial Equity:  ${equity_curve.iloc[0]:>12,.2f}")
    print(f"Final Equity:    ${equity_curve.iloc[-1]:>12,.2f}")
    print(f"Peak Equity:     ${equity_curve.max():>12,.2f}")
    print(f"Trough Equity:   ${equity_curve.min():>12,.2f}")
    print()
    
    print("=" * 80)
    print("EXAMPLE COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()

