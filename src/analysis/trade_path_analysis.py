"""
Trade Path Analysis Module

This module provides tools to analyze the raw quality of trading signals
by tracking the complete price path of each trade, independent of any
portfolio or capital constraints.

Key features:
- No equity/margin/position size constraints
- Each trade is independent and hypothetical
- Tracks Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE)
- Records when MFE occurs to understand optimal exit timing
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import pandas as pd
import numpy as np


@dataclass
class TradePathConfig:
    """Configuration for trade path analysis"""
    max_loss_atr: float = 5.0  # Maximum loss in ATR units before forced exit
    max_holding_bars: int = None  # Maximum bars to hold (None = unlimited)
    price_col_for_pnl: str = "close"  # Price column to use for PnL calculation
    entry_price_col: str = "open"  # Price column for entry (default: open)


def analyze_trade_paths_long_only(
    bars: pd.DataFrame,
    signal_exec: pd.Series,
    atr: pd.Series,
    config: TradePathConfig
) -> pd.DataFrame:
    """
    Perform path-level analysis for a long-only strategy.
    
    This function simulates each trade independently, tracking its complete
    price path until exit. No capital or position sizing constraints are applied.
    
    Parameters
    ----------
    bars : pd.DataFrame
        Bar data with at least 'open', 'high', 'low', 'close' columns.
        Index should be timestamp.
    signal_exec : pd.Series
        Execution signals aligned with bars.index.
        Values: 1 = open long, 0 = no action.
        Assumes signals are already shifted to avoid look-ahead bias.
    atr : pd.Series
        ATR values aligned with bars.index.
    config : TradePathConfig
        Configuration for exit conditions and price columns.
    
    Returns
    -------
    pd.DataFrame
        One row per trade with columns:
        - entry_time, exit_time, direction
        - entry_price, exit_price, holding_bars
        - pnl_final (realized return)
        - mfe, mae (max favorable/adverse excursion in return units)
        - mfe_atr, mae_atr (MFE/MAE in ATR units)
        - t_mfe (bar index when MFE occurred)
        - exit_reason
    """
    # Ensure index alignment
    bars = bars.copy()
    signal_exec = signal_exec.reindex(bars.index, fill_value=0)
    atr = atr.reindex(bars.index)
    
    # Get price columns
    entry_col = config.entry_price_col
    price_col = config.price_col_for_pnl
    
    # Validate columns exist
    required_cols = [entry_col, price_col, 'high', 'low']
    for col in required_cols:
        if col not in bars.columns:
            raise ValueError(f"Required column '{col}' not found in bars DataFrame")
    
    trades = []
    current_trade = None
    
    for i in range(len(bars)):
        bar_time = bars.index[i]
        
        # Check if we have an open trade
        if current_trade is not None:
            # Update trade path
            current_price = bars[price_col].iloc[i]
            entry_price = current_trade['entry_price']
            entry_atr = current_trade['entry_atr']
            
            # Calculate floating PnL
            pnl_return = (current_price - entry_price) / entry_price
            pnl_atr = (current_price - entry_price) / entry_atr
            
            # Append to path
            current_trade['pnl_path'].append(pnl_return)
            current_trade['pnl_atr_path'].append(pnl_atr)
            current_trade['holding_bars'] += 1
            
            # Check exit conditions
            exit_triggered = False
            exit_reason = None
            exit_price = current_price
            
            # 1. Check ATR stop loss
            if pnl_atr <= -config.max_loss_atr:
                exit_triggered = True
                exit_reason = 'ATR_STOP'
            
            # 2. Check new signal (close current trade first)
            elif signal_exec.iloc[i] == 1:
                exit_triggered = True
                exit_reason = 'NEW_SIGNAL'

            # 3. Check max holding period (if specified)
            elif config.max_holding_bars is not None and current_trade['holding_bars'] >= config.max_holding_bars:
                exit_triggered = True
                exit_reason = 'TIME_MAX'
            
            # Execute exit if triggered
            if exit_triggered:
                trade_summary = _summarize_trade(
                    entry_time=current_trade['entry_time'],
                    exit_time=bar_time,
                    direction=1,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pnl_path=current_trade['pnl_path'],
                    pnl_atr_path=current_trade['pnl_atr_path'],
                    exit_reason=exit_reason
                )
                trades.append(trade_summary)
                current_trade = None
                
                # If exit was due to new signal, skip immediate re-entry
                # (we'll enter on next bar if signal persists)
                continue
        
        # Check for new entry (only if no current trade)
        if current_trade is None and signal_exec.iloc[i] == 1:
            entry_price = bars[entry_col].iloc[i]
            entry_atr = atr.iloc[i]
            
            # Skip if ATR is invalid
            if pd.isna(entry_atr) or entry_atr <= 0:
                continue
            
            current_trade = {
                'entry_time': bar_time,
                'entry_price': entry_price,
                'entry_atr': entry_atr,
                'pnl_path': [],
                'pnl_atr_path': [],
                'holding_bars': 0
            }
    
    # Close any remaining open trade at end of data
    if current_trade is not None:
        final_price = bars[price_col].iloc[-1]
        trade_summary = _summarize_trade(
            entry_time=current_trade['entry_time'],
            exit_time=bars.index[-1],
            direction=1,
            entry_price=current_trade['entry_price'],
            exit_price=final_price,
            pnl_path=current_trade['pnl_path'],
            pnl_atr_path=current_trade['pnl_atr_path'],
            exit_reason='END_OF_DATA'
        )
        trades.append(trade_summary)

    # Convert to DataFrame
    if len(trades) == 0:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            'entry_time', 'exit_time', 'direction',
            'entry_price', 'exit_price', 'holding_bars',
            'pnl_final', 'mfe', 'mae', 'mfe_atr', 'mae_atr',
            't_mfe', 'exit_reason'
        ])

    return pd.DataFrame(trades)


def _summarize_trade(
    entry_time,
    exit_time,
    direction: int,
    entry_price: float,
    exit_price: float,
    pnl_path: List[float],
    pnl_atr_path: List[float],
    exit_reason: str
) -> Dict:
    """
    Summarize a single trade's path into key metrics.

    Parameters
    ----------
    entry_time : timestamp
        Entry timestamp
    exit_time : timestamp
        Exit timestamp
    direction : int
        Trade direction (1 for long, -1 for short)
    entry_price : float
        Entry price
    exit_price : float
        Exit price
    pnl_path : List[float]
        List of floating PnL in return units at each bar
    pnl_atr_path : List[float]
        List of floating PnL in ATR units at each bar
    exit_reason : str
        Reason for exit

    Returns
    -------
    dict
        Trade summary with MFE, MAE, and other metrics
    """
    # Calculate final PnL
    if direction == 1:  # Long
        pnl_final = (exit_price - entry_price) / entry_price
    else:  # Short
        pnl_final = (entry_price - exit_price) / entry_price

    # Calculate MFE and MAE
    if len(pnl_path) > 0:
        mfe = max(pnl_path)  # Maximum Favorable Excursion
        mae = min(pnl_path)  # Maximum Adverse Excursion
        mfe_atr = max(pnl_atr_path)
        mae_atr = min(pnl_atr_path)

        # Find when MFE occurred (1-indexed: 1 = first bar after entry)
        t_mfe = pnl_path.index(mfe) + 1
    else:
        # Trade exited immediately (e.g., new signal on same bar)
        mfe = pnl_final
        mae = pnl_final
        mfe_atr = 0.0
        mae_atr = 0.0
        t_mfe = 0

    return {
        'entry_time': entry_time,
        'exit_time': exit_time,
        'direction': direction,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'holding_bars': len(pnl_path),
        'pnl_final': pnl_final,
        'mfe': mfe,
        'mae': mae,
        'mfe_atr': mfe_atr,
        'mae_atr': mae_atr,
        't_mfe': t_mfe,
        'exit_reason': exit_reason
    }


def summarize_trade_paths(trades_df: pd.DataFrame) -> Dict:
    """
    Compute summary statistics for trade path analysis.

    Parameters
    ----------
    trades_df : pd.DataFrame
        Output from analyze_trade_paths_long_only

    Returns
    -------
    dict
        Summary statistics including:
        - MFE/MAE distributions
        - t_mfe distribution (when max profit occurs)
        - Comparison of realized vs potential profit
        - Exit reason breakdown
    """
    if len(trades_df) == 0:
        return {'error': 'No trades to analyze'}

    # Separate winning and losing trades
    winners = trades_df[trades_df['pnl_final'] > 0]
    losers = trades_df[trades_df['pnl_final'] <= 0]

    summary = {
        # Basic stats
        'n_trades': len(trades_df),
        'n_winners': len(winners),
        'n_losers': len(losers),
        'win_rate': len(winners) / len(trades_df) if len(trades_df) > 0 else 0,

        # PnL stats
        'avg_pnl': trades_df['pnl_final'].mean(),
        'median_pnl': trades_df['pnl_final'].median(),
        'avg_winner': winners['pnl_final'].mean() if len(winners) > 0 else 0,
        'avg_loser': losers['pnl_final'].mean() if len(losers) > 0 else 0,

        # MFE stats (Maximum Favorable Excursion)
        'mfe_mean': trades_df['mfe'].mean(),
        'mfe_median': trades_df['mfe'].median(),
        'mfe_atr_mean': trades_df['mfe_atr'].mean(),
        'mfe_atr_median': trades_df['mfe_atr'].median(),
        'mfe_atr_q25': trades_df['mfe_atr'].quantile(0.25),
        'mfe_atr_q75': trades_df['mfe_atr'].quantile(0.75),

        # MAE stats (Maximum Adverse Excursion)
        'mae_mean': trades_df['mae'].mean(),
        'mae_median': trades_df['mae'].median(),
        'mae_atr_mean': trades_df['mae_atr'].mean(),
        'mae_atr_median': trades_df['mae_atr'].median(),
        'mae_atr_q25': trades_df['mae_atr'].quantile(0.25),
        'mae_atr_q75': trades_df['mae_atr'].quantile(0.75),

        # MFE for winners vs losers
        'mfe_winners_mean': winners['mfe'].mean() if len(winners) > 0 else 0,
        'mfe_losers_mean': losers['mfe'].mean() if len(losers) > 0 else 0,
        'mae_winners_mean': winners['mae'].mean() if len(winners) > 0 else 0,
        'mae_losers_mean': losers['mae'].mean() if len(losers) > 0 else 0,

        # Timing of MFE (when does max profit occur?)
        't_mfe_mean': trades_df['t_mfe'].mean(),
        't_mfe_median': trades_df['t_mfe'].median(),
        't_mfe_q25': trades_df['t_mfe'].quantile(0.25),
        't_mfe_q75': trades_df['t_mfe'].quantile(0.75),

        # Holding period
        'holding_bars_mean': trades_df['holding_bars'].mean(),
        'holding_bars_median': trades_df['holding_bars'].median(),

        # Profit capture efficiency (realized / potential)
        'profit_capture_ratio': trades_df['pnl_final'].mean() / trades_df['mfe'].mean() if trades_df['mfe'].mean() > 0 else 0,

        # Exit reason breakdown
        'exit_reasons': trades_df['exit_reason'].value_counts().to_dict()
    }

    return summary


def print_trade_path_summary(summary: Dict, title: str = "Trade Path Analysis Summary"):
    """
    Pretty print the trade path summary statistics.

    Parameters
    ----------
    summary : dict
        Output from summarize_trade_paths
    title : str
        Title for the report
    """
    if 'error' in summary:
        print(f"\n{title}")
        print("=" * 80)
        print(f"ERROR: {summary['error']}")
        return

    print(f"\n{title}")
    print("=" * 80)

    print(f"\n📊 Basic Statistics")
    print(f"  Total trades: {summary['n_trades']:,}")
    print(f"  Winners: {summary['n_winners']:,} ({summary['win_rate']*100:.1f}%)")
    print(f"  Losers: {summary['n_losers']:,}")

    print(f"\n💰 PnL Statistics")
    print(f"  Average PnL: {summary['avg_pnl']*100:.2f}%")
    print(f"  Median PnL: {summary['median_pnl']*100:.2f}%")
    print(f"  Avg Winner: {summary['avg_winner']*100:.2f}%")
    print(f"  Avg Loser: {summary['avg_loser']*100:.2f}%")

    print(f"\n📈 Maximum Favorable Excursion (MFE)")
    print(f"  Mean MFE: {summary['mfe_mean']*100:.2f}%")
    print(f"  Median MFE: {summary['mfe_median']*100:.2f}%")
    print(f"  Mean MFE (ATR): {summary['mfe_atr_mean']:.2f}")
    print(f"  Median MFE (ATR): {summary['mfe_atr_median']:.2f}")
    print(f"  MFE for winners: {summary['mfe_winners_mean']*100:.2f}%")
    print(f"  MFE for losers: {summary['mfe_losers_mean']*100:.2f}%")

    print(f"\n📉 Maximum Adverse Excursion (MAE)")
    print(f"  Mean MAE: {summary['mae_mean']*100:.2f}%")
    print(f"  Median MAE: {summary['mae_median']*100:.2f}%")
    print(f"  Mean MAE (ATR): {summary['mae_atr_mean']:.2f}")
    print(f"  Median MAE (ATR): {summary['mae_atr_median']:.2f}")

    print(f"\n⏱️  Timing of Maximum Profit")
    print(f"  Mean t_mfe: {summary['t_mfe_mean']:.1f} bars")
    print(f"  Median t_mfe: {summary['t_mfe_median']:.1f} bars")
    print(f"  25th percentile: {summary['t_mfe_q25']:.1f} bars")
    print(f"  75th percentile: {summary['t_mfe_q75']:.1f} bars")

    print(f"\n⏳ Holding Period")
    print(f"  Mean: {summary['holding_bars_mean']:.1f} bars")
    print(f"  Median: {summary['holding_bars_median']:.1f} bars")

    print(f"\n🎯 Profit Capture Efficiency")
    print(f"  Realized / Potential: {summary['profit_capture_ratio']*100:.1f}%")
    print(f"  (How much of the max profit we actually captured)")

    print(f"\n🚪 Exit Reasons")
    for reason, count in summary['exit_reasons'].items():
        pct = count / summary['n_trades'] * 100
        print(f"  {reason}: {count:,} ({pct:.1f}%)")

    print("=" * 80)


