"""
Backtesting engine for Extreme Reversal Strategy.

Implements bar-based simulation with:
- Time-based exits (holding horizon)
- ATR-based stop-loss and take-profit
- Transaction costs
- Detailed trade logging
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from .extreme_reversal import ExtremeReversalConfig


@dataclass
class Trade:
    """Single trade record."""
    entry_time: datetime
    entry_price: float
    direction: int  # +1 for long, -1 for short
    size: float = 1.0
    
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # 'SL', 'TP', 'TIME', 'SIGNAL'
    
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    bars_held: Optional[int] = None
    
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None


@dataclass
class BacktestResult:
    """Backtest results container."""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    stats: Dict = field(default_factory=dict)
    bars_with_trades: Optional[pd.DataFrame] = None


def compute_atr(
    bars: pd.DataFrame,
    window: int = 10,
    high_col: str = 'high',
    low_col: str = 'low',
    close_col: str = 'close'
) -> pd.Series:
    """
    计算平均真实波幅 (ATR)。
    
    Compute Average True Range.
    
    Args:
        bars: DataFrame with OHLC data
        window: ATR window (default: 10)
        high_col, low_col, close_col: Column names
    
    Returns:
        Series with ATR values
    """
    high = bars[high_col]
    low = bars[low_col]
    close = bars[close_col]
    
    # True Range components
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    # True Range = max of the three
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR = rolling mean of TR
    atr = tr.rolling(window=window, min_periods=1).mean()
    
    return atr


def run_extreme_reversal_backtest(
    bars: pd.DataFrame,
    exec_signals: pd.Series,
    config: ExtremeReversalConfig,
    initial_capital: float = 10000.0,
    open_col: str = 'open',
    high_col: str = 'high',
    low_col: str = 'low',
    close_col: str = 'close'
) -> BacktestResult:
    """
    运行极端反转策略回测。
    
    Run backtest for Extreme Reversal Strategy with:
    - Single position at a time (no pyramiding)
    - Time-based exit (holding_horizon)
    - ATR-based SL/TP
    - Transaction costs
    
    Args:
        bars: DataFrame with OHLC data
        exec_signals: Series with execution signals (+1, -1, 0)
        config: ExtremeReversalConfig
        initial_capital: Starting capital (default: 10000)
        open_col, high_col, low_col, close_col: OHLC column names
    
    Returns:
        BacktestResult with trades, equity curve, and statistics
        
    Example:
        >>> result = run_extreme_reversal_backtest(bars, signals, config)
        >>> print(f"Total return: {result.stats['total_return']:.2%}")
        >>> print(f"Sharpe ratio: {result.stats['sharpe_ratio']:.2f}")
    """
    # Compute ATR
    atr = compute_atr(bars, window=config.atr_window, 
                     high_col=high_col, low_col=low_col, close_col=close_col)
    
    # Initialize
    trades = []
    equity = initial_capital
    equity_curve = []
    current_position = None
    
    bars_array = bars.reset_index()
    n_bars = len(bars_array)
    
    for i in range(n_bars):
        bar = bars_array.iloc[i]
        signal = exec_signals.iloc[i] if i < len(exec_signals) else 0
        
        # Check if we have an open position
        if current_position is not None:
            trade = current_position
            bars_held = i - trade.entry_bar_idx
            
            # Check exit conditions
            exit_triggered = False
            exit_price = None
            exit_reason = None
            
            # 1. Check SL/TP within this bar
            if trade.direction == 1:  # Long
                # Check stop loss
                if bar[low_col] <= trade.sl_price:
                    exit_price = trade.sl_price
                    exit_reason = 'SL'
                    exit_triggered = True
                # Check take profit
                elif bar[high_col] >= trade.tp_price:
                    exit_price = trade.tp_price
                    exit_reason = 'TP'
                    exit_triggered = True
            else:  # Short
                # Check stop loss
                if bar[high_col] >= trade.sl_price:
                    exit_price = trade.sl_price
                    exit_reason = 'SL'
                    exit_triggered = True
                # Check take profit
                elif bar[low_col] <= trade.tp_price:
                    exit_price = trade.tp_price
                    exit_reason = 'TP'
                    exit_triggered = True
            
            # 2. Check time-based exit
            if not exit_triggered and bars_held >= config.holding_horizon:
                exit_price = bar[open_col]  # Exit at next bar's open
                exit_reason = 'TIME'
                exit_triggered = True
            
            # 3. Check opposite signal (optional: close on reverse signal)
            # For now, we only use time/SL/TP
            
            # Execute exit if triggered
            if exit_triggered:
                trade.exit_time = bar.name if hasattr(bar, 'name') else bar['timestamp']
                trade.exit_price = exit_price
                trade.exit_reason = exit_reason
                trade.bars_held = bars_held
                
                # Calculate PnL
                if trade.direction == 1:
                    pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
                else:
                    pnl_pct = (trade.entry_price - exit_price) / trade.entry_price
                
                # Subtract transaction costs
                pnl_pct -= config.cost_per_trade
                
                trade.pnl_pct = pnl_pct
                trade.pnl = equity * pnl_pct
                
                # Update equity
                equity += trade.pnl
                
                trades.append(trade)
                current_position = None
        
        # Check for new entry signal (only if flat)
        if current_position is None and signal != 0:
            entry_price = bar[open_col]
            atr_val = atr.iloc[i]
            
            # Create new trade
            trade = Trade(
                entry_time=bar.name if hasattr(bar, 'name') else bar['timestamp'],
                entry_price=entry_price,
                direction=int(signal),
                size=1.0
            )
            trade.entry_bar_idx = i
            
            # Set SL/TP based on ATR
            if signal == 1:  # Long
                trade.sl_price = entry_price - config.sl_atr_mult * atr_val
                trade.tp_price = entry_price + config.tp_atr_mult * atr_val
            else:  # Short
                trade.sl_price = entry_price + config.sl_atr_mult * atr_val
                trade.tp_price = entry_price - config.tp_atr_mult * atr_val
            
            current_position = trade
        
        # Record equity
        equity_curve.append(equity)
    
    # Close any remaining position at end
    if current_position is not None:
        trade = current_position
        last_bar = bars_array.iloc[-1]
        trade.exit_time = last_bar.name if hasattr(last_bar, 'name') else last_bar['timestamp']
        trade.exit_price = last_bar[close_col]
        trade.exit_reason = 'END'
        trade.bars_held = n_bars - trade.entry_bar_idx
        
        if trade.direction == 1:
            pnl_pct = (trade.exit_price - trade.entry_price) / trade.entry_price
        else:
            pnl_pct = (trade.entry_price - trade.exit_price) / trade.entry_price
        
        pnl_pct -= config.cost_per_trade
        trade.pnl_pct = pnl_pct
        trade.pnl = equity * pnl_pct
        equity += trade.pnl
        
        trades.append(trade)
        equity_curve.append(equity)
    
    # Create equity curve series
    equity_series = pd.Series(equity_curve, index=bars.index)
    
    # Compute statistics
    stats = compute_performance_stats(trades, equity_series, initial_capital)
    
    # Create result
    result = BacktestResult(
        trades=trades,
        equity_curve=equity_series,
        stats=stats
    )

    return result


def compute_performance_stats(
    trades: List[Trade],
    equity_curve: pd.Series,
    initial_capital: float,
    bars_per_year: int = 252 * 288  # 252 days * 288 5-min bars
) -> Dict:
    """
    计算回测性能统计指标。

    Compute comprehensive performance statistics.

    Args:
        trades: List of Trade objects
        equity_curve: Equity curve series
        initial_capital: Starting capital
        bars_per_year: Number of bars per year for annualization

    Returns:
        Dictionary with performance metrics
    """
    stats = {}

    if len(trades) == 0:
        return {
            'n_trades': 0,
            'total_return': 0.0,
            'message': 'No trades executed'
        }

    # Basic metrics
    stats['n_trades'] = len(trades)
    stats['initial_capital'] = initial_capital
    stats['final_capital'] = equity_curve.iloc[-1]
    stats['total_return'] = (stats['final_capital'] - initial_capital) / initial_capital

    # Returns
    returns = equity_curve.pct_change().dropna()

    # Annualized metrics
    n_bars = len(equity_curve)
    years = n_bars / bars_per_year

    if years > 0:
        stats['annualized_return'] = (1 + stats['total_return']) ** (1 / years) - 1
    else:
        stats['annualized_return'] = 0.0

    if len(returns) > 0:
        stats['annualized_volatility'] = returns.std() * np.sqrt(bars_per_year)

        # Sharpe ratio (assuming 0 risk-free rate)
        if stats['annualized_volatility'] > 0:
            stats['sharpe_ratio'] = stats['annualized_return'] / stats['annualized_volatility']
        else:
            stats['sharpe_ratio'] = 0.0
    else:
        stats['annualized_volatility'] = 0.0
        stats['sharpe_ratio'] = 0.0

    # Drawdown
    cummax = equity_curve.expanding().max()
    drawdown = (equity_curve - cummax) / cummax
    stats['max_drawdown'] = drawdown.min()

    # Drawdown duration
    is_drawdown = drawdown < 0
    if is_drawdown.any():
        dd_periods = is_drawdown.astype(int).groupby((~is_drawdown).cumsum()).sum()
        stats['max_drawdown_duration'] = dd_periods.max()
    else:
        stats['max_drawdown_duration'] = 0

    # Trade statistics
    trade_pnls = [t.pnl for t in trades if t.pnl is not None]
    trade_pnl_pcts = [t.pnl_pct for t in trades if t.pnl_pct is not None]

    if len(trade_pnls) > 0:
        stats['avg_pnl'] = np.mean(trade_pnls)
        stats['avg_pnl_pct'] = np.mean(trade_pnl_pcts)

        winners = [p for p in trade_pnls if p > 0]
        losers = [p for p in trade_pnls if p < 0]

        stats['n_winners'] = len(winners)
        stats['n_losers'] = len(losers)
        stats['win_rate'] = len(winners) / len(trade_pnls) if len(trade_pnls) > 0 else 0

        stats['avg_winner'] = np.mean(winners) if len(winners) > 0 else 0
        stats['avg_loser'] = np.mean(losers) if len(losers) > 0 else 0

        # Profit factor
        total_wins = sum(winners) if len(winners) > 0 else 0
        total_losses = abs(sum(losers)) if len(losers) > 0 else 0

        if total_losses > 0:
            stats['profit_factor'] = total_wins / total_losses
        else:
            stats['profit_factor'] = np.inf if total_wins > 0 else 0

    # Holding period
    bars_held = [t.bars_held for t in trades if t.bars_held is not None]
    if len(bars_held) > 0:
        stats['avg_bars_held'] = np.mean(bars_held)
        stats['max_bars_held'] = np.max(bars_held)

    # Exit reasons
    exit_reasons = [t.exit_reason for t in trades if t.exit_reason is not None]
    stats['exit_reasons'] = pd.Series(exit_reasons).value_counts().to_dict()

    return stats


def print_backtest_summary(result: BacktestResult):
    """
    打印回测结果摘要。

    Print formatted backtest summary.

    Args:
        result: BacktestResult object
    """
    stats = result.stats

    print("=" * 80)
    print("回测结果摘要 / Backtest Summary")
    print("=" * 80)
    print()

    print("📊 总体表现 / Overall Performance")
    print("-" * 80)
    print(f"  初始资金:        {stats.get('initial_capital', 0):>12,.2f}")
    print(f"  最终资金:        {stats.get('final_capital', 0):>12,.2f}")
    print(f"  总收益:          {stats.get('total_return', 0):>12.2%}")
    print(f"  年化收益:        {stats.get('annualized_return', 0):>12.2%}")
    print(f"  年化波动率:      {stats.get('annualized_volatility', 0):>12.2%}")
    print(f"  Sharpe比率:      {stats.get('sharpe_ratio', 0):>12.2f}")
    print(f"  最大回撤:        {stats.get('max_drawdown', 0):>12.2%}")
    print()

    print("📈 交易统计 / Trade Statistics")
    print("-" * 80)
    print(f"  交易次数:        {stats.get('n_trades', 0):>12}")
    print(f"  胜率:            {stats.get('win_rate', 0):>12.2%}")
    print(f"  盈利次数:        {stats.get('n_winners', 0):>12}")
    print(f"  亏损次数:        {stats.get('n_losers', 0):>12}")
    print(f"  平均盈利:        {stats.get('avg_winner', 0):>12.2f}")
    print(f"  平均亏损:        {stats.get('avg_loser', 0):>12.2f}")
    print(f"  盈亏比:          {stats.get('profit_factor', 0):>12.2f}")
    print(f"  平均持仓周期:    {stats.get('avg_bars_held', 0):>12.1f} bars")
    print()

    if 'exit_reasons' in stats:
        print("🚪 退出原因 / Exit Reasons")
        print("-" * 80)
        for reason, count in stats['exit_reasons'].items():
            pct = count / stats['n_trades'] * 100
            print(f"  {reason:10s}:      {count:>6} ({pct:>5.1f}%)")

    print()
    print("=" * 80)


