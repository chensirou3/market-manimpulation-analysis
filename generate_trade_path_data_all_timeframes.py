# -*- coding: utf-8 -*-
"""
Generate Trade Path Data with Step-by-Step PnL

Re-runs trade path analysis and outputs path-level data (one row per step per trade)
instead of summary data (one row per trade).

This is needed for the per-trade exit rule evaluation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from src.strategies.extreme_reversal import ExtremeReversalConfig, generate_extreme_reversal_signals
from src.analysis.trade_path_analysis import TradePathConfig, analyze_trade_paths_long_only


def compute_atr(bars: pd.DataFrame, window: int = 10) -> pd.Series:
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


def expand_trade_paths_to_steps(trades_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Expand trade summary data (with pnl_path lists) into step-by-step format.
    
    Input: DataFrame with columns including 'pnl_path', 'pnl_atr_path'
    Output: DataFrame with one row per step per trade
    
    Columns:
        - trade_id: unique identifier for each trade
        - step: 1, 2, 3, ... (1 = first bar after entry)
        - direction: +1 for long
        - pnl: floating PnL in return units at this step
        - pnl_atr: floating PnL in ATR units at this step
        - entry_time, exit_time (for reference)
    """
    # Note: The current trade_path_analysis output doesn't include pnl_path in CSV
    # We need to modify the analysis to save it, or re-run with path data
    
    # For now, let's create a workaround: re-run the analysis and capture paths
    raise NotImplementedError(
        "Current trade_path_analysis.csv doesn't include step-by-step paths. "
        "Need to re-run analysis with path export enabled."
    )


def run_trade_path_analysis_with_steps(
    symbol: str,
    timeframe: str,
    bars: pd.DataFrame,
    signal_exec: pd.Series,
    atr: pd.Series
) -> pd.DataFrame:
    """
    Run trade path analysis and return step-by-step path data.

    Simplified implementation that directly generates path data without using
    the existing analyze_trade_paths_long_only function.

    Returns:
        DataFrame with columns: trade_id, step, direction, pnl, pnl_atr, entry_time, exit_time
    """
    all_steps = []
    trade_id = 0
    current_trade = None

    entry_col = "open"
    price_col = "close"

    for i in range(len(bars)):
        bar_time = bars.index[i]
        bar_open = bars[entry_col].iloc[i]
        bar_price = bars[price_col].iloc[i]
        bar_low = bars['low'].iloc[i]
        signal = signal_exec.iloc[i]
        bar_atr = atr.iloc[i]

        # Skip if ATR is invalid
        if pd.isna(bar_atr) or bar_atr <= 0:
            continue

        # If in trade, update path
        if current_trade is not None:
            current_trade['step'] += 1

            # Calculate floating PnL
            pnl = (bar_price - current_trade['entry_price']) / current_trade['entry_price']
            pnl_atr = (bar_price - current_trade['entry_price']) / current_trade['entry_atr']

            # Record this step
            all_steps.append({
                'trade_id': current_trade['trade_id'],
                'step': current_trade['step'],
                'direction': 1,  # Long only
                'pnl': pnl,
                'pnl_atr': pnl_atr,
                'entry_time': current_trade['entry_time'],
                'exit_time': bar_time,  # Potential exit time
                'exit_reason': 'OPEN'  # Still open
            })

            # Check exit conditions
            exit_triggered = False
            exit_reason = None

            # 1. Check ATR stop loss (-5 ATR)
            if pnl_atr <= -5.0:
                exit_triggered = True
                exit_reason = 'ATR_STOP'

            # 2. Check new signal (close current trade first)
            elif signal == 1:
                exit_triggered = True
                exit_reason = 'NEW_SIGNAL'

            if exit_triggered:
                # Update last step with exit reason
                all_steps[-1]['exit_reason'] = exit_reason
                current_trade = None
                continue  # Skip entry check on this bar if exiting due to new signal

        # Check for new entry (only if no current trade)
        if current_trade is None and signal == 1:
            trade_id += 1
            current_trade = {
                'trade_id': trade_id,
                'entry_time': bar_time,
                'entry_price': bar_open,
                'entry_atr': bar_atr,
                'step': 0
            }

    # Close any remaining trade at end
    if current_trade is not None and len(all_steps) > 0:
        # Mark last step as end of data
        for i in range(len(all_steps) - 1, -1, -1):
            if all_steps[i]['trade_id'] == current_trade['trade_id']:
                all_steps[i]['exit_reason'] = 'END_OF_DATA'
                break

    return pd.DataFrame(all_steps)


def main():
    """Generate step-by-step trade path data for all symbols and timeframes"""

    print("=" * 80)
    print("GENERATING STEP-BY-STEP TRADE PATH DATA - ALL TIMEFRAMES")
    print("=" * 80)
    print()

    # Define all symbol-timeframe combinations
    symbols_timeframes = [
        # XAUUSD
        ("XAUUSD", "5min", "results/bars_5min_with_manipscore_full.csv"),
        ("XAUUSD", "15min", "results/bars_15min_with_manipscore_full.csv"),
        ("XAUUSD", "30min", "results/bars_30min_with_manipscore_full.csv"),
        ("XAUUSD", "60min", "results/bars_60min_with_manipscore_full.csv"),
        ("XAUUSD", "4h", "results/bars_4h_with_manipscore_full.csv"),
        ("XAUUSD", "1d", "results/bars_1d_with_manipscore_full.csv"),

        # BTCUSD
        ("BTCUSD", "5min", "results/bars_5min_btc_full_with_manipscore.csv"),
        ("BTCUSD", "15min", "results/bars_15min_btc_full_with_manipscore.csv"),
        ("BTCUSD", "30min", "results/bars_30min_btc_full_with_manipscore.csv"),
        ("BTCUSD", "60min", "results/bars_60min_btc_full_with_manipscore.csv"),
        ("BTCUSD", "4h", "results/bars_4h_btc_full_with_manipscore.csv"),
        ("BTCUSD", "1d", "results/bars_1d_btc_full_with_manipscore.csv"),

        # ETHUSD
        ("ETHUSD", "5min", "results/bars_5min_eth_full_with_manipscore.csv"),
        ("ETHUSD", "15min", "results/bars_15min_eth_full_with_manipscore.csv"),
        ("ETHUSD", "30min", "results/bars_30min_eth_full_with_manipscore.csv"),
        ("ETHUSD", "60min", "results/bars_60min_eth_full_with_manipscore.csv"),
        ("ETHUSD", "4h", "results/bars_4h_eth_full_with_manipscore.csv"),
        ("ETHUSD", "1d", "results/bars_1d_eth_full_with_manipscore.csv"),
    ]
    
    total_processed = 0
    total_failed = 0

    for symbol, timeframe, data_path in symbols_timeframes:
        print(f"\n{'='*80}")
        print(f"Processing {symbol} {timeframe}")
        print(f"{'='*80}")

        if not Path(data_path).exists():
            print(f"  ⚠️  SKIP: Data file not found: {data_path}")
            total_failed += 1
            continue

        try:
            # Load data
            bars = pd.read_csv(data_path, parse_dates=['timestamp'])
            bars = bars.set_index('timestamp')
            print(f"  ✓ Loaded {len(bars)} bars")

            # Compute ATR
            atr = compute_atr(bars, window=10)

            # Strategy config
            strategy_config = ExtremeReversalConfig(
                bar_size=timeframe,
                L_past=5,
                vol_window=20,
                q_extreme_trend=0.9,
                q_manip=0.9,
                use_normalized_trend=True
            )

            # Generate signals
            df_with_signals = generate_extreme_reversal_signals(
                bars,
                strategy_config,
                return_col='returns',
                manip_col='ManipScore'
            )

            signal_exec = (df_with_signals['exec_signal'] == 1).astype(int)
            print(f"  ✓ Generated {signal_exec.sum()} signals")

            # Run trade path analysis with step-by-step output
            path_df = run_trade_path_analysis_with_steps(
                symbol, timeframe, bars, signal_exec, atr
            )

            num_trades = path_df['trade_id'].nunique()
            print(f"  ✓ Generated {len(path_df)} step rows for {num_trades} trades")

            # Save
            output_path = f"results/{symbol.lower()}_{timeframe}_trade_path_steps.csv"
            path_df.to_csv(output_path, index=False)
            print(f"  ✓ Saved to: {output_path}")

            total_processed += 1

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            total_failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print(f"\n✅ Successfully processed: {total_processed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total: {total_processed + total_failed}")


if __name__ == "__main__":
    main()

