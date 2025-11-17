"""
Portfolio-level backtest comparison of exit rules for BTC/XAU 4H.

This script compares different exit strategies at the portfolio level:
1. Pure baseline (wide SL, no TP, no time limit)
2. Static SL5 + max 30 bars
3. Dynamic trailing stop (T3_L1.5_SL4)

Goal: Determine if dynamic trailing improves Sharpe, drawdown, and total return
compared to static exits.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

from src.backtest.exit_rules_portfolio import (
    PortfolioExitRule,
    PURE_BASELINE,
    STATIC_SL5_NOTP_30,
    TRAIL_T3_L1p5_SL4,
    TRAIL_T2_L1_SL3,
    STATIC_SL4_TP5_30,
)
from src.backtest.portfolio_backtest import run_portfolio_backtest_with_exit_rule
from src.strategies.extreme_reversal_4h_enhanced import generate_asymmetric_signals
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import compute_atr


def load_bars(symbol: str, timeframe: str = "4h") -> pd.DataFrame:
    """
    Load bar data with ManipScore.

    Args:
        symbol: Asset symbol (e.g., "BTCUSD", "XAUUSD")
        timeframe: Timeframe (default: "4h")

    Returns:
        DataFrame with OHLC, returns, ManipScore, indexed by timestamp
    """
    # Map symbol to file naming convention
    symbol_map = {
        "BTCUSD": "btc",
        "ETHUSD": "eth",
        "XAUUSD": "",  # XAUUSD uses generic file without symbol prefix
    }

    symbol_key = symbol_map.get(symbol, symbol.lower())

    # Try multiple possible file paths
    if symbol_key:
        possible_files = [
            f"results/bars_{timeframe}_{symbol_key}_with_manipscore_full.csv",
            f"results/{symbol}_{timeframe}_bars_with_manipscore_full.csv",
            f"results/{symbol.lower()}_{timeframe}_bars_with_manipscore_full.csv",
        ]
    else:
        # For XAUUSD, try generic file first
        possible_files = [
            f"results/bars_{timeframe}_with_manipscore_full.csv",
            f"results/{symbol}_{timeframe}_bars_with_manipscore_full.csv",
            f"results/{symbol.lower()}_{timeframe}_bars_with_manipscore_full.csv",
        ]

    for filepath in possible_files:
        full_path = project_root / filepath
        if full_path.exists():
            print(f"Loading {symbol} data from: {filepath}")
            df = pd.read_csv(full_path, parse_dates=['timestamp'])
            df = df.set_index('timestamp')
            return df

    raise FileNotFoundError(
        f"Could not find data file for {symbol} {timeframe}. "
        f"Tried: {possible_files}"
    )


def generate_signals(bars: pd.DataFrame, config: ExtremeReversalConfig) -> pd.Series:
    """
    Generate long-only execution signals using asymmetric strategy.
    
    Args:
        bars: DataFrame with OHLC, returns, ManipScore
        config: Strategy configuration
    
    Returns:
        Series of execution signals (0 or 1), index-aligned with bars
    """
    # Generate asymmetric signals (UP=continuation, DOWN=reversal)
    df_with_signals = generate_asymmetric_signals(
        bars,
        config,
        return_col='returns',
        manip_col='ManipScore'
    )
    
    # Extract execution signal
    signal_exec = df_with_signals['exec_signal'].fillna(0).astype(int)
    
    return signal_exec


def main():
    """Run portfolio backtest comparison."""
    
    # Configuration
    symbols = ["BTCUSD", "XAUUSD"]
    timeframe = "4h"
    
    # Exit rules to test
    rules = [
        PURE_BASELINE,
        STATIC_SL5_NOTP_30,
        TRAIL_T3_L1p5_SL4,
        TRAIL_T2_L1_SL3,
        STATIC_SL4_TP5_30,
    ]
    
    # Strategy config (asymmetric 4H)
    config = ExtremeReversalConfig(
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.90,
        q_manip=0.90,
        atr_window=10,
    )
    
    # Transaction cost
    cost_per_trade = 0.0007  # 7 bps round-trip
    initial_equity = 10000.0
    
    # Results storage
    rows = []
    
    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"Processing {symbol} {timeframe}")
        print(f"{'='*80}")
        
        # Load data
        try:
            bars = load_bars(symbol, timeframe)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
            continue
        
        # Filter period (2016-2024)
        bars = bars.loc["2016-01-01":"2024-12-31"]
        print(f"Data period: {bars.index[0]} to {bars.index[-1]}")
        print(f"Total bars: {len(bars)}")
        
        # Compute ATR if not present
        if "atr" not in bars.columns:
            print("Computing ATR...")
            atr = compute_atr(bars, window=config.atr_window)
        else:
            atr = bars["atr"]
        
        # Generate signals
        print("Generating signals...")
        signal_exec = generate_signals(bars, config)
        print(f"Total signals: {signal_exec.sum()}")
        print(f"Signal rate: {signal_exec.mean()*100:.2f}%")
        
        # Test each exit rule
        for rule in rules:
            print(f"\n  Testing rule: {rule.name}")
            
            result = run_portfolio_backtest_with_exit_rule(
                bars=bars,
                signal_exec=signal_exec,
                atr=atr,
                rule=rule,
                cost_per_trade=cost_per_trade,
                initial_equity=initial_equity,
            )
            
            stats = result["stats"]
            
            # Print summary
            print(f"    Trades: {stats['num_trades']}")
            print(f"    Total Return: {stats['total_return']*100:+.2f}%")
            print(f"    Sharpe: {stats['sharpe']:.2f}")
            print(f"    Max DD: {stats['max_drawdown']*100:.2f}%")
            print(f"    Win Rate: {stats['win_rate']*100:.1f}%")
            
            # Store results
            stats_row = {
                "symbol": symbol,
                "timeframe": timeframe,
                "rule_name": rule.name,
                "sl_atr_mult": rule.sl_atr_mult,
                "tp_atr_mult": rule.tp_atr_mult,
                "max_holding_bars": rule.max_holding_bars,
                "trail_trigger_atr": rule.trail_trigger_atr,
                "trail_lock_atr": rule.trail_lock_atr,
            }
            stats_row.update(stats)
            rows.append(stats_row)
            
            # Save detailed results
            trades_path = project_root / f"results/{symbol}_{timeframe}_{rule.name}_trades.csv"
            equity_path = project_root / f"results/{symbol}_{timeframe}_{rule.name}_equity.csv"
            
            result["trades"].to_csv(trades_path, index=False)
            result["equity_curve"].to_csv(equity_path, header=["equity"])
            
            print(f"    Saved trades to: {trades_path.name}")
            print(f"    Saved equity to: {equity_path.name}")
    
    # Save summary
    df_results = pd.DataFrame(rows)
    out_path = project_root / "results/portfolio_exit_rules_4h_compare_summary.csv"
    df_results.to_csv(out_path, index=False)
    
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}\n")
    
    # Display sorted by symbol and Sharpe
    display_cols = [
        'symbol', 'rule_name', 'num_trades', 'total_return', 'sharpe',
        'max_drawdown', 'win_rate', 'avg_pnl_per_trade'
    ]
    
    print(df_results[display_cols].sort_values(['symbol', 'sharpe'], ascending=[True, False]).to_string(index=False))

    print(f"\nSaved summary to: {out_path}")


if __name__ == "__main__":
    main()

