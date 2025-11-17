"""
Portfolio-level backtest engine with pluggable exit rules.

This module implements a single-asset, long-only portfolio backtest
that supports static SL/TP and dynamic trailing stop logic.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

from .exit_rules_portfolio import PortfolioExitRule, get_bars_per_year


@dataclass
class Position:
    """Represents an open position."""
    entry_idx: int
    entry_time: pd.Timestamp
    entry_price: float
    entry_atr: float
    direction: int  # 1 for long
    
    # Exit thresholds
    sl_price: float
    tp_price: float
    max_exit_idx: int
    
    # Trailing state
    trailing_active: bool = False
    peak_pnl_atr: float = 0.0
    current_sl_atr: float = 0.0


def check_intrabar_exit(
    bar: pd.Series,
    position: Position,
    rule: PortfolioExitRule
) -> Tuple[bool, str, float]:
    """
    Check if position should exit within the current bar.
    
    Uses high/low to detect intrabar SL/TP hits.
    
    Args:
        bar: Current bar with 'open', 'high', 'low', 'close'
        position: Current position
        rule: Exit rule configuration
    
    Returns:
        (should_exit, exit_reason, exit_price)
    
    Exit priority:
        1. Stop-loss (static or trailing)
        2. Take-profit
        3. Time limit
        4. No exit
    """
    # Compute current PnL in ATR units
    # Use close for PnL calculation (conservative)
    pnl_atr = (bar['close'] - position.entry_price) / position.entry_atr
    
    # Update trailing stop if applicable
    if not np.isinf(rule.trail_trigger_atr):
        if pnl_atr >= rule.trail_trigger_atr:
            position.trailing_active = True
        
        if position.trailing_active:
            # Update peak
            position.peak_pnl_atr = max(position.peak_pnl_atr, pnl_atr)
            # Update dynamic SL
            position.current_sl_atr = position.peak_pnl_atr - rule.trail_lock_atr
    
    # Check SL (static or trailing)
    if position.trailing_active:
        # Trailing SL
        if pnl_atr <= position.current_sl_atr:
            # Use low to estimate exit price
            exit_price = max(
                bar['low'],
                position.entry_price + position.current_sl_atr * position.entry_atr
            )
            return True, 'TRAIL_SL', exit_price
    else:
        # Static SL
        if not np.isinf(rule.sl_atr_mult):
            if bar['low'] <= position.sl_price:
                return True, 'SL', position.sl_price
    
    # Check TP
    if not np.isinf(rule.tp_atr_mult):
        if bar['high'] >= position.tp_price:
            return True, 'TP', position.tp_price
    
    # No intrabar exit
    return False, '', 0.0


def run_portfolio_backtest_with_exit_rule(
    bars: pd.DataFrame,
    signal_exec: pd.Series,
    atr: pd.Series,
    rule: PortfolioExitRule,
    cost_per_trade: float = 0.0007,
    initial_equity: float = 10000.0
) -> Dict:
    """
    Run single-asset, long-only portfolio backtest with pluggable exit rule.
    
    Args:
        bars: DataFrame with columns ['open','high','low','close'], indexed by timestamp
        signal_exec: Series aligned with bars.index, values in {0,1}, long-only entry signals
        atr: Series aligned with bars.index, ATR values for SL/TP calculation
        rule: PortfolioExitRule specifying exit logic
        cost_per_trade: Round-trip transaction cost as fraction (e.g., 0.0007 = 7 bps)
        initial_equity: Starting capital
    
    Returns:
        Dictionary with:
            'equity_curve': pd.Series of equity over time
            'trades': pd.DataFrame of trade details
            'stats': dict of performance statistics
    
    Assumptions:
        - Entry at open[t] when signal_exec[t] == 1 and no position
        - Exit detection uses high/low for intrabar SL/TP
        - PnL calculation uses close for trailing logic
        - Transaction cost deducted at trade close
    """
    # Align data
    bars = bars.copy()
    signal_exec = signal_exec.reindex(bars.index, fill_value=0)
    atr = atr.reindex(bars.index).ffill().bfill()
    
    # Initialize
    equity = initial_equity
    equity_curve = []
    trades = []
    position = None
    
    bars_array = bars.reset_index()
    n_bars = len(bars_array)
    
    for i in range(n_bars):
        bar = bars_array.iloc[i]
        current_time = bar['timestamp'] if 'timestamp' in bar.index else bar.name
        signal = signal_exec.iloc[i]
        current_atr = atr.iloc[i]
        
        # Record equity
        if position is not None:
            # Mark-to-market
            unrealized_pnl = (bar['close'] - position.entry_price)
            current_equity = equity + unrealized_pnl
        else:
            current_equity = equity
        
        equity_curve.append({
            'timestamp': current_time,
            'equity': current_equity
        })
        
        # Check exit if in position
        if position is not None:
            should_exit = False
            exit_reason = ''
            exit_price = 0.0
            
            # Check intrabar exit (SL/TP)
            should_exit, exit_reason, exit_price = check_intrabar_exit(bar, position, rule)
            
            # Check time limit
            if not should_exit:
                holding_bars = i - position.entry_idx
                if holding_bars >= rule.max_holding_bars:
                    should_exit = True
                    exit_reason = 'TIME_MAX'
                    exit_price = bar['close']
            
            # Execute exit
            if should_exit:
                pnl = exit_price - position.entry_price
                pnl_pct = pnl / position.entry_price
                
                # Deduct transaction cost
                pnl_after_cost = pnl - (cost_per_trade * position.entry_price)
                pnl_pct_after_cost = pnl_after_cost / position.entry_price
                
                equity += pnl_after_cost
                
                trades.append({
                    'entry_time': position.entry_time,
                    'exit_time': current_time,
                    'entry_price': position.entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'pnl_after_cost': pnl_after_cost,
                    'pnl_pct_after_cost': pnl_pct_after_cost,
                    'direction': position.direction,
                    'exit_reason': exit_reason,
                    'holding_bars': i - position.entry_idx,
                    'entry_atr': position.entry_atr,
                    'trailing_activated': position.trailing_active,
                })
                
                position = None
        
        # Check entry if no position
        if position is None and signal == 1:
            entry_price = bar['open']
            entry_atr = current_atr
            
            # Calculate SL/TP prices
            if np.isinf(rule.sl_atr_mult):
                sl_price = 0.0  # No SL
            else:
                sl_price = entry_price - rule.sl_atr_mult * entry_atr
            
            if np.isinf(rule.tp_atr_mult):
                tp_price = np.inf  # No TP
            else:
                tp_price = entry_price + rule.tp_atr_mult * entry_atr
            
            max_exit_idx = min(i + rule.max_holding_bars, n_bars - 1)
            
            position = Position(
                entry_idx=i,
                entry_time=current_time,
                entry_price=entry_price,
                entry_atr=entry_atr,
                direction=1,
                sl_price=sl_price,
                tp_price=tp_price,
                max_exit_idx=max_exit_idx,
                current_sl_atr=-rule.sl_atr_mult,
            )
    
    # Close any remaining position at end
    if position is not None:
        bar = bars_array.iloc[-1]
        current_time = bar['timestamp'] if 'timestamp' in bar.index else bar.name
        exit_price = bar['close']
        
        pnl = exit_price - position.entry_price
        pnl_pct = pnl / position.entry_price
        pnl_after_cost = pnl - (cost_per_trade * position.entry_price)
        pnl_pct_after_cost = pnl_after_cost / position.entry_price
        
        equity += pnl_after_cost
        
        trades.append({
            'entry_time': position.entry_time,
            'exit_time': current_time,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'pnl_after_cost': pnl_after_cost,
            'pnl_pct_after_cost': pnl_pct_after_cost,
            'direction': position.direction,
            'exit_reason': 'END_OF_DATA',
            'holding_bars': len(bars_array) - 1 - position.entry_idx,
            'entry_atr': position.entry_atr,
            'trailing_activated': position.trailing_active,
        })
    
    # Convert to DataFrames
    equity_df = pd.DataFrame(equity_curve).set_index('timestamp')
    trades_df = pd.DataFrame(trades)
    
    # Compute statistics
    stats = compute_portfolio_stats(equity_df, trades_df, rule, initial_equity)

    return {
        'equity_curve': equity_df['equity'],
        'trades': trades_df,
        'stats': stats
    }


def compute_portfolio_stats(
    equity_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    rule: PortfolioExitRule,
    initial_equity: float
) -> Dict:
    """
    Compute portfolio performance statistics.

    Args:
        equity_df: DataFrame with 'equity' column
        trades_df: DataFrame with trade details
        rule: Exit rule configuration
        initial_equity: Starting capital

    Returns:
        Dictionary of performance metrics
    """
    if len(equity_df) == 0:
        return {
            'total_return': 0.0,
            'ann_return': 0.0,
            'ann_vol': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_pnl_per_trade': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
        }

    # Total return
    final_equity = equity_df['equity'].iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity

    # Annualized return and volatility
    equity_returns = equity_df['equity'].pct_change().dropna()

    if len(equity_returns) > 0:
        bars_per_year = get_bars_per_year(rule.bar_size)

        # Annualized return (geometric)
        n_bars = len(equity_df)
        years = n_bars / bars_per_year
        if years > 0:
            ann_return = (1 + total_return) ** (1 / years) - 1
        else:
            ann_return = 0.0

        # Annualized volatility
        ann_vol = equity_returns.std() * np.sqrt(bars_per_year)

        # Sharpe ratio (assuming 0 risk-free rate)
        if ann_vol > 0:
            sharpe = ann_return / ann_vol
        else:
            sharpe = 0.0
    else:
        ann_return = 0.0
        ann_vol = 0.0
        sharpe = 0.0

    # Maximum drawdown
    cummax = equity_df['equity'].cummax()
    drawdown = (equity_df['equity'] - cummax) / cummax
    max_drawdown = drawdown.min()

    # Trade statistics
    if len(trades_df) > 0:
        num_trades = len(trades_df)
        wins = trades_df[trades_df['pnl_after_cost'] > 0]
        losses = trades_df[trades_df['pnl_after_cost'] <= 0]

        win_rate = len(wins) / num_trades if num_trades > 0 else 0.0
        avg_pnl_per_trade = trades_df['pnl_pct_after_cost'].mean()

        avg_win = wins['pnl_pct_after_cost'].mean() if len(wins) > 0 else 0.0
        avg_loss = losses['pnl_pct_after_cost'].mean() if len(losses) > 0 else 0.0

        total_wins = wins['pnl_after_cost'].sum() if len(wins) > 0 else 0.0
        total_losses = abs(losses['pnl_after_cost'].sum()) if len(losses) > 0 else 0.0

        if total_losses > 0:
            profit_factor = total_wins / total_losses
        else:
            profit_factor = np.inf if total_wins > 0 else 0.0

        # Exit reason distribution
        exit_reasons = trades_df['exit_reason'].value_counts().to_dict()

        # Trailing activation rate
        if 'trailing_activated' in trades_df.columns:
            trailing_rate = trades_df['trailing_activated'].mean()
        else:
            trailing_rate = 0.0
    else:
        num_trades = 0
        win_rate = 0.0
        avg_pnl_per_trade = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        profit_factor = 0.0
        exit_reasons = {}
        trailing_rate = 0.0

    return {
        'total_return': total_return,
        'ann_return': ann_return,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'avg_pnl_per_trade': avg_pnl_per_trade,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'exit_reasons': exit_reasons,
        'trailing_activation_rate': trailing_rate,
    }

