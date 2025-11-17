"""
Static SL/TP Grid Search for 4H Timeframe

This script runs a comprehensive grid search over static SL/TP parameters
for XAUUSD, BTCUSD, and ETHUSD on the 4H timeframe.

Grid parameters:
- SL_MULTS: [1.5, 2.0, 2.5, 3.0]
- TP_MULTS: [1.0, 1.5, 2.0, 2.5]
- MAX_HOLDING_BARS: [10, 15, 20, 26]
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from tqdm import tqdm

from src.backtest.static_exit_backtest import (
    StaticExitConfig,
    run_static_exit_backtest,
    compute_atr
)
from src.strategies.extreme_reversal import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals
)


# Configuration
SYMBOLS_4H = ["XAUUSD", "BTCUSD", "ETHUSD"]
TIMEFRAME = "4h"

# Parameter grids
SL_MULTS = [1.5, 2.0, 2.5, 3.0]
TP_MULTS = [1.0, 1.5, 2.0, 2.5]
MAX_HOLDING_BARS = [10, 15, 20, 26]

# Strategy configuration for signal generation
STRATEGY_CONFIG = ExtremeReversalConfig(
    bar_size="4h",
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9,
    use_normalized_trend=True,
    min_abs_R_past=None,
    min_manip_score=None,
    use_daily_confluence=False,
    use_clustering_filter=False
)

# ATR window for exit calculations
ATR_WINDOW = 10

# Transaction cost
COST_PER_TRADE = 0.0007  # 7bp


def load_bars(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Load bar data for given symbol and timeframe.
    
    Args:
        symbol: Asset symbol (XAUUSD, BTCUSD, ETHUSD)
        timeframe: Timeframe string (4h)
    
    Returns:
        DataFrame with OHLCV and ManipScore
    """
    # Map symbol names to file names
    symbol_map = {
        'XAUUSD': 'xauusd',
        'BTCUSD': 'btc',
        'ETHUSD': 'eth'
    }
    
    file_symbol = symbol_map.get(symbol, symbol.lower())
    
    # Try different file naming patterns
    possible_files = [
        f"results/bars_{timeframe}_{file_symbol}_full_with_manipscore.csv",
        f"results/bars_{timeframe}_{file_symbol}_with_manipscore_full.csv",
        f"results/bars_{timeframe}_with_manipscore_full.csv"  # For XAUUSD
    ]
    
    for filepath in possible_files:
        full_path = project_root / filepath
        if full_path.exists():
            print(f"Loading {symbol} data from: {filepath}")
            df = pd.read_csv(full_path, parse_dates=['timestamp'])
            df = df.set_index('timestamp')
            return df
    
    raise FileNotFoundError(f"Could not find data file for {symbol} {timeframe}. Tried: {possible_files}")


def generate_signals(bars: pd.DataFrame, config: ExtremeReversalConfig) -> pd.Series:
    """
    Generate long-only execution signals.
    
    Args:
        bars: DataFrame with OHLCV and ManipScore
        config: Strategy configuration
    
    Returns:
        Series of execution signals (0 or 1)
    """
    # Generate signals using extreme reversal strategy
    df_with_signals = generate_extreme_reversal_signals(
        bars,
        config,
        return_col='returns',
        manip_col='ManipScore'
    )
    
    # Extract execution signal (long-only)
    # The strategy generates raw_signal which can be -1 (short), 0 (no signal), or +1 (long)
    # For long-only, we only take +1 signals
    if 'exec_signal' in df_with_signals.columns:
        signal_exec = (df_with_signals['exec_signal'] == 1).astype(int)
    elif 'raw_signal' in df_with_signals.columns:
        signal_exec = (df_with_signals['raw_signal'] == 1).astype(int)
    else:
        raise ValueError("No signal column found in generated signals")
    
    return signal_exec


def run_grid_search():
    """
    Run grid search over all parameter combinations.
    """
    results = []
    
    # Total number of combinations
    total_combinations = len(SYMBOLS_4H) * len(SL_MULTS) * len(TP_MULTS) * len(MAX_HOLDING_BARS)
    
    print("=" * 80)
    print("STATIC SL/TP GRID SEARCH - 4H TIMEFRAME")
    print("=" * 80)
    print(f"\nSymbols: {SYMBOLS_4H}")
    print(f"SL Multipliers: {SL_MULTS}")
    print(f"TP Multipliers: {TP_MULTS}")
    print(f"Max Holding Bars: {MAX_HOLDING_BARS}")
    print(f"\nTotal combinations: {total_combinations}")
    print("=" * 80)
    print()
    
    # Iterate over all combinations
    with tqdm(total=total_combinations, desc="Grid Search Progress") as pbar:
        for symbol in SYMBOLS_4H:
            # Load data once per symbol
            try:
                bars = load_bars(symbol, TIMEFRAME)
                print(f"\n{symbol}: Loaded {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")
            except FileNotFoundError as e:
                print(f"\nSkipping {symbol}: {e}")
                pbar.update(len(SL_MULTS) * len(TP_MULTS) * len(MAX_HOLDING_BARS))
                continue
            
            # Compute ATR
            atr = compute_atr(bars, window=ATR_WINDOW)
            
            # Generate signals once per symbol
            signal_exec = generate_signals(bars, STRATEGY_CONFIG)
            num_signals = signal_exec.sum()
            print(f"{symbol}: Generated {num_signals} long signals ({num_signals/len(bars)*100:.2f}% of bars)")
            
            # Grid search over SL/TP/MAX_HOLDING_BARS
            for sl_mult in SL_MULTS:
                for tp_mult in TP_MULTS:
                    for max_holding_bars in MAX_HOLDING_BARS:
                        # Create config
                        cfg = StaticExitConfig(
                            bar_size=TIMEFRAME,
                            sl_atr_mult=sl_mult,
                            tp_atr_mult=tp_mult,
                            max_holding_bars=max_holding_bars,
                            cost_per_trade=COST_PER_TRADE
                        )
                        
                        # Run backtest
                        result = run_static_exit_backtest(bars, signal_exec, atr, cfg)
                        stats = result['stats']
                        
                        # Append results
                        results.append({
                            'symbol': symbol,
                            'timeframe': TIMEFRAME,
                            'sl_mult': sl_mult,
                            'tp_mult': tp_mult,
                            'max_holding_bars': max_holding_bars,
                            'total_return': stats['total_return'],
                            'ann_return': stats['ann_return'],
                            'ann_vol': stats['ann_vol'],
                            'sharpe': stats['sharpe'],
                            'max_drawdown': stats['max_drawdown'],
                            'num_trades': stats['num_trades'],
                            'win_rate': stats['win_rate'],
                            'avg_pnl_per_trade': stats['avg_pnl_per_trade'],
                            'avg_winner': stats['avg_winner'],
                            'avg_loser': stats['avg_loser'],
                            'profit_factor': stats['profit_factor']
                        })
                        
                        pbar.update(1)
    
    return pd.DataFrame(results)


if __name__ == "__main__":
    # Run grid search
    df_results = run_grid_search()
    
    # Save results
    output_file = project_root / "results" / "static_sl_tp_grid_4h_summary.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n{'=' * 80}")
    print(f"Results saved to: {output_file}")
    print(f"{'=' * 80}\n")
    
    # Display top results by Sharpe ratio
    print("=" * 80)
    print("TOP 20 CONFIGURATIONS BY SHARPE RATIO")
    print("=" * 80)
    print()
    top_20 = df_results.nlargest(20, 'sharpe')
    print(top_20.to_string(index=False))
    print()
    
    # Display top results by total return
    print("=" * 80)
    print("TOP 20 CONFIGURATIONS BY TOTAL RETURN")
    print("=" * 80)
    print()
    top_20_return = df_results.nlargest(20, 'total_return')
    print(top_20_return[['symbol', 'sl_mult', 'tp_mult', 'max_holding_bars', 
                          'total_return', 'sharpe', 'max_drawdown', 'num_trades']].to_string(index=False))
    print()
    
    # Summary by symbol
    print("=" * 80)
    print("BEST CONFIGURATION PER SYMBOL (BY SHARPE)")
    print("=" * 80)
    print()
    for symbol in SYMBOLS_4H:
        symbol_df = df_results[df_results['symbol'] == symbol]
        if len(symbol_df) > 0:
            best = symbol_df.nlargest(1, 'sharpe').iloc[0]
            print(f"\n{symbol}:")
            print(f"  SL/TP/MaxBars: {best['sl_mult']:.1f} / {best['tp_mult']:.1f} / {best['max_holding_bars']}")
            print(f"  Sharpe: {best['sharpe']:.2f}")
            print(f"  Total Return: {best['total_return']:.2%}")
            print(f"  Ann Return: {best['ann_return']:.2%}")
            print(f"  Max DD: {best['max_drawdown']:.2%}")
            print(f"  Trades: {best['num_trades']}")
            print(f"  Win Rate: {best['win_rate']:.1%}")
    
    print("\n" + "=" * 80)
    print("GRID SEARCH COMPLETE!")
    print("=" * 80)

