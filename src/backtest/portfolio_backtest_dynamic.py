# -*- coding: utf-8 -*-
"""
Dynamic Portfolio Backtest Module

Portfolio-level backtest with signal-strength-based dynamic exit rules (Layer 3).

Each trade's exit rule is determined by its entry signal strength (strong/medium/weak).
"""

import pandas as pd
import numpy as np
from typing import Dict
from dataclasses import dataclass

from src.backtest.dynamic_exit_rules import get_portfolio_exit_rule_for_strength


@dataclass
class Position:
    """Represents an open position with its dynamic exit rule"""
    entry_time: pd.Timestamp
    entry_price: float
    direction: int  # +1 for long
    entry_atr: float
    signal_strength: str  # 'strong', 'medium', or 'weak'
    
    # Exit rule parameters (determined at entry based on strength)
    sl_atr_mult: float
    tp_atr_mult: float
    max_holding_bars: int
    trail_trigger_atr: float
    trail_lock_atr: float
    
    # Dynamic state
    bars_held: int = 0
    trailing_active: bool = False
    current_sl_atr: float = None  # Will be initialized
    
    def __post_init__(self):
        if self.current_sl_atr is None:
            self.current_sl_atr = -self.sl_atr_mult


def run_portfolio_backtest_with_dynamic_exit(
    bars: pd.DataFrame,
    signal_exec: pd.Series,
    atr: pd.Series,
    entry_features: pd.DataFrame,
    symbol: str,
    cost_per_trade: float = 0.0007,
    initial_equity: float = 10000.0
) -> Dict:
    """
    Run portfolio backtest with dynamic strength-based exit rules.
    
    Parameters:
        bars: DataFrame indexed by timestamp, with ['open','high','low','close']
        signal_exec: Series in {0,1}, index aligned with bars.index
        atr: Series aligned with bars.index
        entry_features: DataFrame with ['entry_time','signal_strength',...]
                       Maps entry times to signal strengths
        symbol: "BTCUSD" or "XAUUSD"
        cost_per_trade: Round-trip transaction cost (default: 7 bps)
        initial_equity: Starting equity (default: 10000)
    
    Returns:
        Dict with:
            'equity_curve': pd.Series
            'trades': pd.DataFrame
            'stats': dict
    
    Logic:
        - Walk through bars sequentially
        - When no position and signal_exec[t] == 1:
            * Determine signal_strength for this entry
            * Select exit rule based on strength
            * Open position with these rule parameters
        - While in position:
            * Apply exit logic using stored rule parameters
            * Check SL/TP/trailing/time limits
        - Track equity and trades
    """
    # Ensure bars is sorted by timestamp
    bars = bars.sort_index()
    
    # Create entry_time to signal_strength mapping
    strength_map = {}
    if 'entry_time' in entry_features.columns and 'signal_strength' in entry_features.columns:
        for _, row in entry_features.iterrows():
            strength_map[row['entry_time']] = row['signal_strength']
    
    # Initialize tracking
    equity = initial_equity
    equity_curve = []
    trades = []
    position = None
    
    # Walk through bars
    for t in bars.index:
        bar = bars.loc[t]
        atr_t = atr.loc[t] if t in atr.index else np.nan
        sig_t = signal_exec.loc[t] if t in signal_exec.index else 0
        
        # If no position and signal fires
        if position is None and sig_t == 1:
            # Determine signal strength for this entry
            signal_strength = strength_map.get(t, 'medium')  # Default to medium if not found
            
            # Get exit rule for this strength
            rule = get_portfolio_exit_rule_for_strength(symbol, signal_strength)
            
            # Open position
            position = Position(
                entry_time=t,
                entry_price=bar['open'],
                direction=1,  # Long only
                entry_atr=atr_t,
                signal_strength=signal_strength,
                sl_atr_mult=rule.sl_atr_mult,
                tp_atr_mult=rule.tp_atr_mult,
                max_holding_bars=rule.max_holding_bars,
                trail_trigger_atr=rule.trail_trigger_atr,
                trail_lock_atr=rule.trail_lock_atr
            )
            
            continue
        
        # If in position, check exits
        if position is not None:
            position.bars_held += 1
            
            # Compute current PnL
            pnl_pct = (bar['close'] - position.entry_price) / position.entry_price * position.direction
            pnl_atr = pnl_pct / position.entry_atr if position.entry_atr > 0 else 0.0
            
            # Check for exit
            exit_triggered, exit_reason, exit_price = check_dynamic_exit(
                bar, position, pnl_atr
            )
            
            if exit_triggered:
                # Close position
                final_pnl_pct = (exit_price - position.entry_price) / position.entry_price * position.direction
                final_pnl_pct -= cost_per_trade  # Subtract transaction costs
                
                equity *= (1 + final_pnl_pct)
                
                # Record trade
                trades.append({
                    'entry_time': position.entry_time,
                    'exit_time': t,
                    'signal_strength': position.signal_strength,
                    'entry_price': position.entry_price,
                    'exit_price': exit_price,
                    'pnl_pct': final_pnl_pct,
                    'holding_bars': position.bars_held,
                    'exit_reason': exit_reason
                })
                
                position = None
        
        # Record equity
        equity_curve.append({'timestamp': t, 'equity': equity})
    
    # Convert to DataFrames
    equity_df = pd.DataFrame(equity_curve).set_index('timestamp')
    trades_df = pd.DataFrame(trades)
    
    # Compute stats
    stats = compute_dynamic_portfolio_stats(equity_df, trades_df, initial_equity)
    
    return {
        'equity_curve': equity_df,
        'trades': trades_df,
        'stats': stats
    }


def check_dynamic_exit(
    bar: pd.Series,
    position: Position,
    pnl_atr: float
) -> tuple:
    """
    Check if position should exit based on dynamic exit rules.

    Parameters:
        bar: Current bar with ['open','high','low','close']
        position: Position object with exit rule parameters
        pnl_atr: Current PnL in ATR units

    Returns:
        (exit_triggered, exit_reason, exit_price)
    """
    # Check if trailing should activate
    if not position.trailing_active and pnl_atr >= position.trail_trigger_atr:
        position.trailing_active = True
        position.current_sl_atr = pnl_atr - position.trail_lock_atr

    # If trailing active, update SL
    if position.trailing_active:
        position.current_sl_atr = max(position.current_sl_atr, pnl_atr - position.trail_lock_atr)

    # Check stop loss
    if pnl_atr <= position.current_sl_atr:
        exit_reason = 'TRAIL' if position.trailing_active else 'SL'
        return True, exit_reason, bar['close']

    # Check take profit
    if pnl_atr >= position.tp_atr_mult:
        return True, 'TP', bar['close']

    # Check time limit
    if position.bars_held >= position.max_holding_bars:
        return True, 'TIME_MAX', bar['close']

    return False, None, None


def compute_dynamic_portfolio_stats(
    equity_df: pd.DataFrame,
    trades_df: pd.DataFrame,
    initial_equity: float
) -> Dict:
    """
    Compute portfolio statistics for dynamic exit backtest.

    Parameters:
        equity_df: DataFrame with equity curve
        trades_df: DataFrame with trade records
        initial_equity: Starting equity

    Returns:
        Dict with performance metrics
    """
    if len(equity_df) == 0:
        return {
            'total_return': 0.0,
            'num_trades': 0,
            'win_rate': 0.0,
            'avg_pnl_per_trade': 0.0
        }

    final_equity = equity_df['equity'].iloc[-1]
    total_return = (final_equity - initial_equity) / initial_equity

    # Compute returns
    equity_df['returns'] = equity_df['equity'].pct_change().fillna(0)

    # Annualized metrics (assuming 4H bars, ~6 bars per day, ~252 trading days)
    bars_per_year = 6 * 252
    total_bars = len(equity_df)
    years = total_bars / bars_per_year if bars_per_year > 0 else 1

    ann_return = total_return / years if years > 0 else 0.0
    ann_vol = equity_df['returns'].std() * np.sqrt(bars_per_year)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    # Max drawdown
    cummax = equity_df['equity'].cummax()
    drawdown = (equity_df['equity'] - cummax) / cummax
    max_drawdown = drawdown.min()

    # Trade statistics
    num_trades = len(trades_df)
    if num_trades > 0:
        win_rate = (trades_df['pnl_pct'] > 0).mean()
        avg_pnl_per_trade = trades_df['pnl_pct'].mean()

        # By signal strength
        strength_stats = {}
        for strength in ['strong', 'medium', 'weak']:
            strength_trades = trades_df[trades_df['signal_strength'] == strength]
            if len(strength_trades) > 0:
                strength_stats[f'{strength}_count'] = len(strength_trades)
                strength_stats[f'{strength}_win_rate'] = (strength_trades['pnl_pct'] > 0).mean()
                strength_stats[f'{strength}_avg_pnl'] = strength_trades['pnl_pct'].mean()
            else:
                strength_stats[f'{strength}_count'] = 0
                strength_stats[f'{strength}_win_rate'] = 0.0
                strength_stats[f'{strength}_avg_pnl'] = 0.0
    else:
        win_rate = 0.0
        avg_pnl_per_trade = 0.0
        strength_stats = {}

    return {
        'total_return': total_return,
        'ann_return': ann_return,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades,
        'win_rate': win_rate,
        'avg_pnl_per_trade': avg_pnl_per_trade,
        **strength_stats
    }

