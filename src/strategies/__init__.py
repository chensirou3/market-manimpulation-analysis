"""
Trading strategies module.
"""

from .trend_features import (
    compute_trend_strength,
    compute_extreme_trend_thresholds
)

from .extreme_reversal import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals
)

from .backtest_reversal import (
    BacktestResult,
    run_extreme_reversal_backtest,
    compute_performance_stats,
    print_backtest_summary
)

__all__ = [
    'compute_trend_strength',
    'compute_extreme_trend_thresholds',
    'ExtremeReversalConfig',
    'generate_extreme_reversal_signals',
    'BacktestResult',
    'run_extreme_reversal_backtest',
    'compute_performance_stats',
    'print_backtest_summary',
]

