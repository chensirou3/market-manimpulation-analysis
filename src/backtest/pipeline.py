"""
End-to-end backtesting pipeline.

Demonstrates how to integrate the manipulation detection toolkit
with a simple trading strategy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Dict

from ..utils.logging_utils import get_logger
from ..utils.paths import load_config
from ..data_prep.tick_loader import load_tick_data
from ..data_prep.bar_aggregator import ticks_to_bars
from ..data_prep.features_orderbook_proxy import add_orderbook_proxy_features
from ..factors.manipulation_score import compute_manipulation_score
from .interfaces import apply_manipulation_filter, calculate_performance_metrics, compare_strategies

logger = get_logger(__name__)


def simple_moving_average_strategy(
    bars: pd.DataFrame,
    fast_window: int = 10,
    slow_window: int = 30
) -> pd.Series:
    """
    Simple moving average crossover strategy.
    
    Args:
        bars: DataFrame with 'close' prices.
        fast_window: Fast MA window.
        slow_window: Slow MA window.
        
    Returns:
        pd.Series: Signals (+1 for long, -1 for short, 0 for neutral).
        
    Strategy:
        - Buy when fast MA crosses above slow MA
        - Sell when fast MA crosses below slow MA
    """
    fast_ma = bars['close'].rolling(window=fast_window).mean()
    slow_ma = bars['close'].rolling(window=slow_window).mean()
    
    signals = pd.Series(0, index=bars.index)
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma < slow_ma] = -1
    
    return signals


def run_demo_backtest(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_synthetic_data: bool = True
) -> Dict:
    """
    Run a complete demonstration backtest.
    
    This function demonstrates the full pipeline:
    1. Load tick data (or generate synthetic data)
    2. Aggregate to bars
    3. Compute features
    4. Calculate manipulation score
    5. Apply to a simple strategy
    6. Compare filtered vs unfiltered performance
    
    Args:
        symbol: Symbol to backtest (if using real data).
        start_date: Start date for backtest.
        end_date: End date for backtest.
        use_synthetic_data: If True, use synthetic data instead of loading real data.
        
    Returns:
        dict: Results including bars, signals, metrics, and comparison.
        
    Examples:
        >>> results = run_demo_backtest(use_synthetic_data=True)
        >>> print(results['comparison'])
    """
    logger.info("=" * 60)
    logger.info("Running Demo Backtest Pipeline")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config()
    
    # Step 1: Load or generate data
    if use_synthetic_data:
        logger.info("Generating synthetic tick data...")
        n_ticks = 50000
        np.random.seed(42)
        
        ticks = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01 09:30', periods=n_ticks, freq='1s'),
            'price': np.random.randn(n_ticks).cumsum() + 1850,
            'volume': np.random.randint(1, 100, n_ticks),
            'side': np.random.choice(['buy', 'sell'], n_ticks)
        })
        
        logger.info(f"Generated {len(ticks):,} synthetic ticks")
    else:
        logger.info(f"Loading tick data for {symbol}...")
        ticks = load_tick_data(symbol, start_date, end_date)
    
    # Step 2: Aggregate to bars
    logger.info("Aggregating ticks to bars...")
    timeframe = config.get('bars', {}).get('timeframe', '1min')
    bars = ticks_to_bars(ticks, timeframe=timeframe, compute_features=True)
    
    # Step 3: Add orderbook proxy features
    logger.info("Computing orderbook proxy features...")
    bars = add_orderbook_proxy_features(bars, ticks, window=20)
    
    # Step 4: Compute manipulation score
    logger.info("Computing manipulation score...")
    bars = compute_manipulation_score(bars, config.get('manipulation_score'), ticks)
    
    # Step 5: Generate strategy signals
    logger.info("Generating strategy signals (MA crossover)...")
    signals_raw = simple_moving_average_strategy(bars, fast_window=10, slow_window=30)
    
    # Step 6: Apply manipulation filter
    logger.info("Applying manipulation filter...")
    filter_config = config.get('backtest', {})
    threshold = filter_config.get('filter_threshold', 0.7)
    mode = filter_config.get('filter_mode', 'zero')
    
    signals_filtered = apply_manipulation_filter(
        signals_raw,
        bars['manip_score'],
        threshold=threshold,
        mode=mode
    )
    
    # Step 7: Calculate returns
    bars['returns'] = bars['close'].pct_change()
    
    # Step 8: Calculate performance metrics
    logger.info("Calculating performance metrics...")
    metrics_raw = calculate_performance_metrics(bars['returns'], signals_raw, filter_config)
    metrics_filtered = calculate_performance_metrics(bars['returns'], signals_filtered, filter_config)
    
    # Step 9: Compare strategies
    comparison = compare_strategies(bars['returns'], signals_raw, signals_filtered, filter_config)
    
    # Log results
    logger.info("\n" + "=" * 60)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"\nOriginal Strategy:")
    logger.info(f"  Total Return: {metrics_raw['total_return']:.2%}")
    logger.info(f"  Sharpe Ratio: {metrics_raw['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {metrics_raw['max_drawdown']:.2%}")
    logger.info(f"  Win Rate: {metrics_raw['win_rate']:.2%}")
    logger.info(f"  Trades: {metrics_raw['n_trades']}")
    
    logger.info(f"\nFiltered Strategy (threshold={threshold}, mode={mode}):")
    logger.info(f"  Total Return: {metrics_filtered['total_return']:.2%}")
    logger.info(f"  Sharpe Ratio: {metrics_filtered['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {metrics_filtered['max_drawdown']:.2%}")
    logger.info(f"  Win Rate: {metrics_filtered['win_rate']:.2%}")
    logger.info(f"  Trades: {metrics_filtered['n_trades']}")
    
    logger.info("\n" + "=" * 60)
    
    # Package results
    results = {
        'bars': bars,
        'ticks': ticks,
        'signals_raw': signals_raw,
        'signals_filtered': signals_filtered,
        'metrics_raw': metrics_raw,
        'metrics_filtered': metrics_filtered,
        'comparison': comparison
    }
    
    return results


def plot_backtest_results(results: Dict, save_path: Optional[str] = None) -> None:
    """
    Plot backtest results.
    
    Args:
        results: Results dict from run_demo_backtest.
        save_path: Optional path to save the figure.
    """
    bars = results['bars']
    signals_raw = results['signals_raw']
    signals_filtered = results['signals_filtered']
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # Plot 1: Price and signals
    ax1 = axes[0]
    ax1.plot(bars.index, bars['close'], label='Price', linewidth=1)
    ax1.scatter(bars.index[signals_raw == 1], bars['close'][signals_raw == 1], 
                color='green', marker='^', alpha=0.5, label='Buy (Raw)')
    ax1.scatter(bars.index[signals_raw == -1], bars['close'][signals_raw == -1], 
                color='red', marker='v', alpha=0.5, label='Sell (Raw)')
    ax1.set_ylabel('Price')
    ax1.set_title('Price and Trading Signals')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Manipulation score
    ax2 = axes[1]
    ax2.plot(bars.index, bars['manip_score'], label='Manipulation Score', color='orange', linewidth=1)
    ax2.axhline(y=0.7, color='red', linestyle='--', label='Threshold (0.7)')
    ax2.set_ylabel('Manip Score')
    ax2.set_title('Manipulation Score Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Cumulative returns
    ax3 = axes[2]
    returns_raw = signals_raw.shift(1) * bars['returns']
    returns_filtered = signals_filtered.shift(1) * bars['returns']
    
    cum_returns_raw = (1 + returns_raw).cumprod()
    cum_returns_filtered = (1 + returns_filtered).cumprod()
    
    ax3.plot(bars.index, cum_returns_raw, label='Original Strategy', linewidth=1.5)
    ax3.plot(bars.index, cum_returns_filtered, label='Filtered Strategy', linewidth=1.5)
    ax3.set_ylabel('Cumulative Return')
    ax3.set_xlabel('Time')
    ax3.set_title('Strategy Performance Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {save_path}")
    
    plt.show()


if __name__ == "__main__":
    print("=== Backtesting Pipeline Demo ===\n")
    
    # Run demo backtest
    results = run_demo_backtest(use_synthetic_data=True)
    
    # Display comparison
    print("\nStrategy Comparison:")
    print(results['comparison'])
    
    # Plot results
    print("\nGenerating plots...")
    plot_backtest_results(results)
    
    print("\nDemo complete!")

