# -*- coding: utf-8 -*-
"""
Risk Overlay Module

Implements risk management overlays for the trading strategy:
1. Weak signal filtering - suppress entry signals labeled as 'weak'
2. Drawdown-based position scaling - reduce position size during deep drawdowns

These overlays are designed to reduce maximum drawdown with minimal impact on long-term returns.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


def filter_weak_signals(
    signal_exec: pd.Series,
    signal_strength: pd.Series
) -> pd.Series:
    """
    Filter out weak entry signals.
    
    Parameters:
        signal_exec: Series of {0,1} entry signals, aligned with bars.index
        signal_strength: Series of {'strong','medium','weak'} for entry bars
                        (NaN or empty string for non-entry bars)
    
    Returns:
        signal_exec_filtered: Same index as signal_exec, values in {0,1}
                             Where signal_strength == 'weak' and signal_exec == 1,
                             set to 0; otherwise keep original value
    
    Logic:
        - Only affects entry decisions (signal_exec)
        - Exit logic remains unchanged
        - Conservative: if signal_strength is NaN or empty, keep original signal
    
    No look-ahead bias:
        - signal_strength is determined at entry time using only past data
        - Filtering happens before position is opened
    """
    if not signal_exec.index.equals(signal_strength.index):
        raise ValueError("signal_exec and signal_strength must have the same index")
    
    signal_exec_filtered = signal_exec.copy()
    
    # Suppress signals where strength is 'weak'
    weak_mask = (signal_strength == 'weak') & (signal_exec == 1)
    signal_exec_filtered[weak_mask] = 0
    
    return signal_exec_filtered


def apply_drawdown_based_scaling_to_trades(
    trades: pd.DataFrame,
    initial_equity: float = 10000.0,
    dd_level_1: float = -0.30,
    dd_level_2: float = -0.50,
    scale_level_1: float = 1.0,
    scale_level_2: float = 0.5,
    scale_level_3: float = 0.0,
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Apply drawdown-based position scaling at the trade level.
    
    Parameters:
        trades: DataFrame with one row per trade, must include:
                - 'pnl_pct': trade's unscaled return in decimal (e.g. 0.05 for +5%)
                - 'entry_time': timestamp of entry (for indexing equity curve)
        initial_equity: Starting capital
        dd_level_1: Drawdown threshold for first scaling level (e.g. -0.30 = -30%)
        dd_level_2: Drawdown threshold for second scaling level (e.g. -0.50 = -50%)
        scale_level_1: Position scale when dd > dd_level_1 (default: 1.0 = full size)
        scale_level_2: Position scale when dd_level_2 < dd <= dd_level_1 (default: 0.5 = half size)
        scale_level_3: Position scale when dd <= dd_level_2 (default: 0.0 = pause trading)
    
    Returns:
        equity_curve: pd.Series indexed by trade number (or entry_time)
        trades_scaled: trades DataFrame with additional columns:
                      - 'scale': position scale applied to this trade
                      - 'scaled_pnl_pct': scale * pnl_pct
                      - 'equity_before': equity before this trade
                      - 'equity_after': equity after this trade
                      - 'drawdown': drawdown at entry of this trade
    
    Logic:
        For each trade i:
        1. Compute current drawdown: dd = equity_i / equity_peak_i - 1
        2. Determine scale based on dd:
           - if dd > dd_level_1:           scale = scale_level_1 (e.g. 1.0)
           - elif dd > dd_level_2:         scale = scale_level_2 (e.g. 0.5)
           - else:                         scale = scale_level_3 (e.g. 0.0)
        3. Apply scaled PnL: equity_{i+1} = equity_i * (1 + scale * pnl_pct_i)
        4. Update equity peak
    
    No look-ahead bias:
        - Drawdown is computed using equity BEFORE the current trade
        - Scale is determined before trade PnL is applied
        - Only uses information available at trade entry time
    """
    if 'pnl_pct' not in trades.columns:
        raise ValueError("trades DataFrame must contain 'pnl_pct' column")
    
    trades_scaled = trades.copy()
    
    # Initialize tracking
    equity = initial_equity
    equity_peak = initial_equity
    equity_history = [initial_equity]  # Include initial equity
    
    scales = []
    scaled_pnls = []
    equity_befores = []
    equity_afters = []
    drawdowns = []
    
    for idx, row in trades_scaled.iterrows():
        pnl_pct = row['pnl_pct']
        
        # Compute current drawdown BEFORE this trade
        drawdown = equity / equity_peak - 1.0
        
        # Determine position scale based on drawdown
        if drawdown > dd_level_1:
            scale = scale_level_1
        elif drawdown > dd_level_2:
            scale = scale_level_2
        else:
            scale = scale_level_3
        
        # Apply scaled PnL
        scaled_pnl_pct = scale * pnl_pct
        equity_before = equity
        equity_after = equity * (1.0 + scaled_pnl_pct)
        
        # Update equity and peak
        equity = equity_after
        equity_peak = max(equity_peak, equity)
        
        # Record
        scales.append(scale)
        scaled_pnls.append(scaled_pnl_pct)
        equity_befores.append(equity_before)
        equity_afters.append(equity_after)
        drawdowns.append(drawdown)
        equity_history.append(equity)
    
    # Add columns to trades DataFrame
    trades_scaled['scale'] = scales
    trades_scaled['scaled_pnl_pct'] = scaled_pnls
    trades_scaled['equity_before'] = equity_befores
    trades_scaled['equity_after'] = equity_afters
    trades_scaled['drawdown'] = drawdowns
    
    # Create equity curve
    # Index by trade number (0 = initial equity, 1 = after first trade, etc.)
    equity_curve = pd.Series(equity_history, index=range(len(equity_history)))
    
    return equity_curve, trades_scaled


def compute_portfolio_stats_from_equity(
    equity_curve: pd.Series,
    trades_df: pd.DataFrame,
    bar_size: str = "4h"
) -> Dict:
    """
    Compute portfolio statistics from equity curve and trades DataFrame.

    Parameters:
        equity_curve: Series of equity values over time
        trades_df: DataFrame with trade-level data, must include:
                  - 'scaled_pnl_pct' (or 'pnl_pct' if no scaling applied)
                  - 'scale' (optional, for scaling statistics)
        bar_size: Bar size for annualization (e.g. "4h", "1d")

    Returns:
        Dict with statistics:
            - total_return: Total return over the period
            - ann_return: Annualized return
            - ann_vol: Annualized volatility
            - sharpe: Sharpe ratio
            - max_drawdown: Maximum drawdown
            - num_trades: Number of trades
            - win_rate: Percentage of profitable trades
            - avg_pnl_per_trade: Average PnL per trade
            - avg_win: Average winning trade
            - avg_loss: Average losing trade
            - profit_factor: Total wins / Total losses
            - num_trades_full_size: Number of trades at full size (scale=1.0)
            - num_trades_half_size: Number of trades at half size (scale=0.5)
            - num_trades_paused: Number of trades at zero size (scale=0.0)
    """
    # Determine PnL column
    if 'scaled_pnl_pct' in trades_df.columns:
        pnl_col = 'scaled_pnl_pct'
    elif 'pnl_pct' in trades_df.columns:
        pnl_col = 'pnl_pct'
    else:
        raise ValueError("trades_df must contain 'scaled_pnl_pct' or 'pnl_pct' column")

    # Total return
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0

    # Annualized return
    num_trades = len(trades_df)
    if num_trades == 0:
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
            'num_trades_full_size': 0,
            'num_trades_half_size': 0,
            'num_trades_paused': 0,
        }

    # Estimate time period from equity curve length
    # Assume equity_curve has one entry per trade + initial
    # For annualization, we need to estimate years
    # Use a simple approximation: assume average holding period
    bars_per_year = {"5min": 105120, "15min": 35040, "30min": 17520,
                     "1h": 8760, "4h": 2190, "1d": 365}

    # Rough estimate: assume each trade holds for ~10 bars on average
    avg_bars_per_trade = 10
    total_bars = num_trades * avg_bars_per_trade
    years = total_bars / bars_per_year.get(bar_size, 2190)
    years = max(years, 0.1)  # Minimum 0.1 years to avoid division by zero

    ann_return = (1 + total_return) ** (1 / years) - 1

    # Annualized volatility
    trade_returns = trades_df[pnl_col].values
    if len(trade_returns) > 1:
        trade_vol = np.std(trade_returns, ddof=1)
        # Annualize assuming trades are independent
        trades_per_year = num_trades / years
        ann_vol = trade_vol * np.sqrt(trades_per_year)
    else:
        ann_vol = 0.0

    # Sharpe ratio
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    # Max drawdown
    equity_peak = equity_curve.expanding().max()
    drawdowns = equity_curve / equity_peak - 1.0
    max_drawdown = drawdowns.min()

    # Win rate
    wins = trade_returns > 0
    win_rate = wins.mean() if len(trade_returns) > 0 else 0.0

    # Average PnL per trade
    avg_pnl_per_trade = trade_returns.mean() if len(trade_returns) > 0 else 0.0

    # Average win/loss
    winning_trades = trade_returns[trade_returns > 0]
    losing_trades = trade_returns[trade_returns < 0]
    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0.0
    avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0.0

    # Profit factor
    total_wins = winning_trades.sum() if len(winning_trades) > 0 else 0.0
    total_losses = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0.0
    profit_factor = total_wins / total_losses if total_losses > 0 else (np.inf if total_wins > 0 else 0.0)

    # Scaling statistics
    if 'scale' in trades_df.columns:
        num_trades_full_size = (trades_df['scale'] == 1.0).sum()
        num_trades_half_size = (trades_df['scale'] == 0.5).sum()
        num_trades_paused = (trades_df['scale'] == 0.0).sum()
    else:
        num_trades_full_size = num_trades
        num_trades_half_size = 0
        num_trades_paused = 0

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
        'num_trades_full_size': int(num_trades_full_size),
        'num_trades_half_size': int(num_trades_half_size),
        'num_trades_paused': int(num_trades_paused),
    }

