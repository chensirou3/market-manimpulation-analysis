"""
Backtesting interfaces module.

Defines interfaces and utility functions for integrating manipulation scores
with existing trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Union, Literal

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)

# Type aliases for clarity
StrategySignal = pd.Series  # Series with values like {-1, 0, +1} or continuous


def apply_manipulation_filter(
    signals: pd.Series,
    manip_score: pd.Series,
    threshold: float = 0.7,
    mode: Literal['zero', 'reduce', 'adaptive'] = 'zero',
    reduce_factor: float = 0.5
) -> pd.Series:
    """
    Apply manipulation score filter to trading signals.
    
    Args:
        signals: Original strategy signals (e.g., -1, 0, +1 or continuous).
        manip_score: Manipulation scores (0-1 range).
        threshold: Threshold above which to filter (default: 0.7).
        mode: Filtering mode:
            - 'zero': Set signal to 0 when score > threshold
            - 'reduce': Scale signal by reduce_factor when score > threshold
            - 'adaptive': Scale signal by (1 - manip_score) continuously
        reduce_factor: Factor to multiply signal by in 'reduce' mode (default: 0.5).
        
    Returns:
        pd.Series: Filtered signals.
        
    Examples:
        >>> # Zero mode: eliminate signals when manipulation detected
        >>> filtered = apply_manipulation_filter(signals, manip_score, threshold=0.7, mode='zero')
        
        >>> # Reduce mode: scale down signals
        >>> filtered = apply_manipulation_filter(signals, manip_score, threshold=0.7, mode='reduce', reduce_factor=0.5)
        
        >>> # Adaptive mode: continuous scaling
        >>> filtered = apply_manipulation_filter(signals, manip_score, mode='adaptive')
    """
    # Align indices
    signals_aligned, manip_aligned = signals.align(manip_score, join='inner')
    
    filtered = signals_aligned.copy()
    
    if mode == 'zero':
        # Set signal to 0 when manipulation score exceeds threshold
        filtered[manip_aligned > threshold] = 0
        n_filtered = (manip_aligned > threshold).sum()
        logger.info(f"Zero mode: Filtered {n_filtered} / {len(filtered)} signals (threshold={threshold})")
        
    elif mode == 'reduce':
        # Scale down signal when manipulation score exceeds threshold
        mask = manip_aligned > threshold
        filtered[mask] = filtered[mask] * reduce_factor
        n_reduced = mask.sum()
        logger.info(f"Reduce mode: Scaled {n_reduced} / {len(filtered)} signals by {reduce_factor}")
        
    elif mode == 'adaptive':
        # Continuously scale signal by (1 - manip_score)
        filtered = filtered * (1 - manip_aligned)
        logger.info(f"Adaptive mode: Applied continuous scaling")
        
    else:
        raise ValueError(f"Unknown filter mode: {mode}")
    
    return filtered


def calculate_performance_metrics(
    returns: pd.Series,
    signals: pd.Series,
    config: dict = None
) -> dict:
    """
    Calculate performance metrics for a strategy.
    
    Args:
        returns: Series of asset returns.
        signals: Series of strategy signals (positions).
        config: Configuration dict with transaction costs, etc.
        
    Returns:
        dict: Performance metrics.
        
    Metrics:
        - total_return: Cumulative return
        - sharpe_ratio: Annualized Sharpe ratio
        - max_drawdown: Maximum drawdown
        - win_rate: Fraction of profitable trades
        - n_trades: Number of trades
        
    Examples:
        >>> metrics = calculate_performance_metrics(returns, signals)
        >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
    """
    if config is None:
        config = {}
    
    commission = config.get('commission', 0.0002)
    
    # Align returns and signals
    returns_aligned, signals_aligned = returns.align(signals, join='inner')
    
    # Strategy returns (signal * return)
    strategy_returns = signals_aligned.shift(1) * returns_aligned
    
    # Account for transaction costs
    position_changes = signals_aligned.diff().abs()
    transaction_costs = position_changes * commission
    strategy_returns = strategy_returns - transaction_costs
    
    # Cumulative returns
    cumulative_returns = (1 + strategy_returns).cumprod()
    total_return = cumulative_returns.iloc[-1] - 1
    
    # Sharpe ratio (annualized, assuming 252 trading days)
    mean_return = strategy_returns.mean()
    std_return = strategy_returns.std()
    sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
    
    # Maximum drawdown
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Win rate
    n_trades = (position_changes > 0).sum()
    winning_trades = (strategy_returns > 0).sum()
    win_rate = winning_trades / len(strategy_returns) if len(strategy_returns) > 0 else 0
    
    metrics = {
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'n_trades': n_trades,
        'mean_return': mean_return,
        'std_return': std_return
    }
    
    return metrics


def compare_strategies(
    returns: pd.Series,
    signals_original: pd.Series,
    signals_filtered: pd.Series,
    config: dict = None
) -> pd.DataFrame:
    """
    Compare performance of original vs filtered strategy.
    
    Args:
        returns: Asset returns.
        signals_original: Original strategy signals.
        signals_filtered: Filtered strategy signals.
        config: Configuration dict.
        
    Returns:
        pd.DataFrame: Comparison table with metrics for both strategies.
        
    Examples:
        >>> comparison = compare_strategies(returns, signals_raw, signals_filtered)
        >>> print(comparison)
    """
    logger.info("Comparing original vs filtered strategy")
    
    metrics_original = calculate_performance_metrics(returns, signals_original, config)
    metrics_filtered = calculate_performance_metrics(returns, signals_filtered, config)
    
    comparison = pd.DataFrame({
        'Original': metrics_original,
        'Filtered': metrics_filtered
    })
    
    # Add improvement column
    comparison['Improvement'] = comparison['Filtered'] - comparison['Original']
    comparison['Improvement_pct'] = (comparison['Filtered'] / comparison['Original'] - 1) * 100
    
    return comparison


if __name__ == "__main__":
    # Demo usage
    print("=== Backtesting Interfaces Demo ===\n")
    
    # Create synthetic data
    n = 1000
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=n, freq='1min')
    returns = pd.Series(np.random.randn(n) * 0.001, index=dates)
    signals = pd.Series(np.random.choice([-1, 0, 1], n), index=dates)
    manip_score = pd.Series(np.random.rand(n), index=dates)
    
    # Inject some high manipulation scores
    manip_score.iloc[100:120] = 0.9
    manip_score.iloc[500:520] = 0.85
    
    print(f"Created {n} bars with signals and manipulation scores\n")
    
    # Apply filters
    print("Applying filters...\n")
    
    filtered_zero = apply_manipulation_filter(signals, manip_score, threshold=0.7, mode='zero')
    filtered_reduce = apply_manipulation_filter(signals, manip_score, threshold=0.7, mode='reduce', reduce_factor=0.5)
    filtered_adaptive = apply_manipulation_filter(signals, manip_score, mode='adaptive')
    
    # Calculate metrics
    print("Performance comparison:")
    comparison = compare_strategies(returns, signals, filtered_zero)
    print(comparison)

