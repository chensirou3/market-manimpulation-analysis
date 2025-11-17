"""
Static SL/TP Exit Backtest Module

This module implements a clean backtester for long-only strategies with:
- Static stop-loss (SL) and take-profit (TP) based on ATR multiples
- Maximum holding bars constraint
- New signal exit rule
- No capital constraints (always enter when signal fires)
- Single position at a time (no pyramiding)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Tuple


@dataclass
class StaticExitConfig:
    """
    Configuration for static SL/TP exit rules.
    
    Parameters:
        bar_size: Timeframe ('5min', '15min', '30min', '60min', '4h', '1d')
        sl_atr_mult: Stop-loss as multiple of entry ATR (e.g., 1.5, 2.0, 2.5)
        tp_atr_mult: Take-profit as multiple of entry ATR (e.g., 1.0, 1.5, 2.0)
        max_holding_bars: Maximum bars to hold position (e.g., 10, 15, 20)
        cost_per_trade: Transaction cost per round-trip (default: 0.0007 = 7bp)
    """
    bar_size: str
    sl_atr_mult: float
    tp_atr_mult: float
    max_holding_bars: int
    cost_per_trade: float = 0.0007


def get_bars_per_year(bar_size: str) -> int:
    """
    Get number of bars per year for annualization.
    
    Args:
        bar_size: Timeframe string ('5min', '15min', '30min', '60min', '4h', '1d')
    
    Returns:
        Number of bars per year
    """
    bars_per_day = {
        '5min': 288,    # 24 * 60 / 5
        '15min': 96,    # 24 * 60 / 15
        '30min': 48,    # 24 * 60 / 30
        '60min': 24,    # 24
        '4h': 6,        # 24 / 4
        '1d': 1         # 1
    }
    
    if bar_size not in bars_per_day:
        raise ValueError(f"Unknown bar_size: {bar_size}. Must be one of {list(bars_per_day.keys())}")
    
    return bars_per_day[bar_size] * 365


def compute_atr(bars: pd.DataFrame, window: int = 10) -> pd.Series:
    """
    Compute Average True Range (ATR).
    
    Args:
        bars: DataFrame with 'high', 'low', 'close' columns
        window: Rolling window for ATR calculation
    
    Returns:
        Series of ATR values
    """
    high = bars['high']
    low = bars['low']
    close = bars['close']
    
    # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window, min_periods=1).mean()
    
    return atr


def run_static_exit_backtest(
    bars: pd.DataFrame,
    signal_exec: pd.Series,
    atr: pd.Series,
    config: StaticExitConfig
) -> Dict:
    """
    Run a long-only backtest with static SL/TP + max holding bars + new-signal exit.
    
    Args:
        bars: DataFrame with at least 'open', 'high', 'low', 'close', indexed by timestamp
        signal_exec: Series aligned with bars.index, values in {0, 1} (long-only entries)
        atr: Series aligned with bars.index, ATR at each bar
        config: StaticExitConfig specifying SL/TP multipliers and max holding bars
    
    Rules:
        - When no position and signal_exec[t] == 1 -> enter long at open[t]
        - For an open long:
            * Compute entry_price and entry_atr at entry bar
            * On each subsequent bar, check intrabar SL/TP using high/low:
                - If low[t] <= SL_price: SL hit; exit at SL_price
                - Else if high[t] >= TP_price: TP hit; exit at TP_price
                - Else if holding_bars >= max_holding_bars: exit at close[t]
                - Else if signal_exec[t] == 1 (new signal): exit at close[t] (reason='NEW_SIGNAL')
        - Only one position at a time
        - No capital constraints
    
    Returns:
        Dict with:
            - 'equity_curve': Series of equity (starting from 10000)
            - 'trades': DataFrame with trade details
            - 'stats': summary metrics dict
    """
    # Initialize
    equity = 10000.0
    equity_curve = []
    trades = []
    
    in_position = False
    entry_idx = None
    entry_price = None
    entry_atr = None
    sl_price = None
    tp_price = None
    holding_bars = 0

    # Iterate through bars
    for i in range(len(bars)):
        timestamp = bars.index[i]
        bar_open = bars['open'].iloc[i]
        bar_high = bars['high'].iloc[i]
        bar_low = bars['low'].iloc[i]
        bar_close = bars['close'].iloc[i]
        bar_atr = atr.iloc[i]
        signal = signal_exec.iloc[i]

        skip_entry_this_bar = False  # Reset at start of each bar

        # Check for exit if in position
        if in_position:
            holding_bars += 1
            exit_price = None
            exit_reason = None

            # Priority 1: Check SL (assume SL checked first if both SL and TP in same bar)
            if bar_low <= sl_price:
                exit_price = sl_price
                exit_reason = 'SL'
            # Priority 2: Check TP
            elif bar_high >= tp_price:
                exit_price = tp_price
                exit_reason = 'TP'
            # Priority 3: Check max holding bars
            elif holding_bars >= config.max_holding_bars:
                exit_price = bar_close
                exit_reason = 'MAX_BARS'
            # Priority 4: Check new signal
            elif signal == 1:
                exit_price = bar_close
                exit_reason = 'NEW_SIGNAL'
                skip_entry_this_bar = True  # Skip immediate re-entry on this bar

            # Execute exit if triggered
            if exit_price is not None:
                pnl_pct = (exit_price - entry_price) / entry_price - config.cost_per_trade
                pnl_dollar = equity * pnl_pct
                equity += pnl_dollar

                trades.append({
                    'entry_time': bars.index[entry_idx],
                    'exit_time': timestamp,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'holding_bars': holding_bars,
                    'pnl_pct': pnl_pct,
                    'pnl_dollar': pnl_dollar,
                    'exit_reason': exit_reason
                })

                in_position = False
                entry_idx = None
                entry_price = None
                entry_atr = None
                sl_price = None
                tp_price = None
                holding_bars = 0

        # Check for entry if not in position
        # Skip entry if we just exited due to NEW_SIGNAL on this bar
        if not in_position and signal == 1 and not skip_entry_this_bar:
            entry_idx = i
            entry_price = bar_open
            entry_atr = bar_atr
            sl_price = entry_price - config.sl_atr_mult * entry_atr
            tp_price = entry_price + config.tp_atr_mult * entry_atr
            holding_bars = 0
            in_position = True

        # Record equity
        equity_curve.append(equity)
    
    # Close any remaining position at end
    if in_position:
        exit_price = bars['close'].iloc[-1]
        pnl_pct = (exit_price - entry_price) / entry_price - config.cost_per_trade
        pnl_dollar = equity * pnl_pct
        equity += pnl_dollar
        
        trades.append({
            'entry_time': bars.index[entry_idx],
            'exit_time': bars.index[-1],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'holding_bars': holding_bars + 1,
            'pnl_pct': pnl_pct,
            'pnl_dollar': pnl_dollar,
            'exit_reason': 'END_OF_DATA'
        })
        
        equity_curve[-1] = equity
    
    # Convert to DataFrames/Series
    equity_curve = pd.Series(equity_curve, index=bars.index)
    trades_df = pd.DataFrame(trades)
    
    # Compute statistics
    stats = compute_backtest_stats(equity_curve, trades_df, config.bar_size)

    return {
        'equity_curve': equity_curve,
        'trades': trades_df,
        'stats': stats
    }


def compute_backtest_stats(equity_curve: pd.Series, trades_df: pd.DataFrame, bar_size: str) -> Dict:
    """
    Compute summary statistics for backtest results.

    Args:
        equity_curve: Series of equity values over time
        trades_df: DataFrame of trade records
        bar_size: Timeframe for annualization

    Returns:
        Dict of summary statistics
    """
    if len(equity_curve) == 0:
        return {
            'total_return': 0.0,
            'ann_return': 0.0,
            'ann_vol': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_pnl_per_trade': 0.0,
            'avg_winner': 0.0,
            'avg_loser': 0.0,
            'profit_factor': 0.0
        }

    # Total return
    initial_equity = equity_curve.iloc[0]
    final_equity = equity_curve.iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity

    # Compute returns
    equity_returns = equity_curve.pct_change().fillna(0)

    # Annualized return and volatility
    bars_per_year = get_bars_per_year(bar_size)
    mean_return = equity_returns.mean()
    ann_return = mean_return * bars_per_year
    ann_vol = equity_returns.std() * np.sqrt(bars_per_year)

    # Sharpe ratio
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    # Maximum drawdown
    cummax = equity_curve.cummax()
    drawdown = (equity_curve - cummax) / cummax
    max_drawdown = drawdown.min()

    # Trade statistics
    num_trades = len(trades_df)

    if num_trades == 0:
        return {
            'total_return': total_return,
            'ann_return': ann_return,
            'ann_vol': ann_vol,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_pnl_per_trade': 0.0,
            'avg_winner': 0.0,
            'avg_loser': 0.0,
            'profit_factor': 0.0
        }

    # Win rate
    winners = trades_df[trades_df['pnl_pct'] > 0]
    losers = trades_df[trades_df['pnl_pct'] <= 0]
    win_rate = len(winners) / num_trades if num_trades > 0 else 0.0

    # Average PnL
    avg_pnl_per_trade = trades_df['pnl_pct'].mean()
    avg_winner = winners['pnl_pct'].mean() if len(winners) > 0 else 0.0
    avg_loser = losers['pnl_pct'].mean() if len(losers) > 0 else 0.0

    # Profit factor
    total_wins = winners['pnl_pct'].sum() if len(winners) > 0 else 0.0
    total_losses = abs(losers['pnl_pct'].sum()) if len(losers) > 0 else 0.0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

    return {
        'total_return': total_return,
        'ann_return': ann_return,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'avg_pnl_per_trade': avg_pnl_per_trade,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'profit_factor': profit_factor
    }

