"""
Extreme Manipulation Reversal Strategy.

This strategy exploits the empirical finding that extreme trends
combined with high ManipScore tend to reverse in the short term.

Key insight:
- Extreme up-move + high ManipScore → expect reversal DOWN (short signal)
- Extreme down-move + high ManipScore → expect reversal UP (long signal)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

from .trend_features import (
    compute_trend_strength,
    compute_extreme_trend_thresholds,
    identify_extreme_trends
)


@dataclass
class ExtremeReversalConfig:
    """
    Configuration for Extreme Reversal Strategy.

    Timeframe:
        bar_size: Bar timeframe ('5min', '15min', '30min', '60min', '4h', etc.)
                 All window parameters are in BARS, so time horizon scales with bar_size.

    Trend parameters:
        L_past: Lookback window for cumulative return (default: 5 bars)
        vol_window: Window for rolling volatility (default: 20 bars)
        q_extreme_trend: Quantile for extreme trend threshold (default: 0.9)
        use_normalized_trend: Use volatility-normalized TS instead of raw R_past
        min_abs_R_past: Optional absolute minimum for R_past (e.g., 0.005 = 0.5%)

    ManipScore parameters:
        q_manip: Quantile for high ManipScore threshold (default: 0.9)
        min_manip_score: Optional absolute minimum ManipScore override

    Multi-timeframe filters (NEW):
        use_daily_confluence: Enable daily regime filter (default: False)
        daily_q_extreme_trend: Quantile for daily extreme trend (default: 0.9)
        daily_q_high_manip: Quantile for daily high ManipScore (default: 0.9)
        daily_min_abs_R_past: Optional minimum daily |R_past| (default: None)

    Clustering filters (NEW):
        use_clustering_filter: Enable clustering filter (default: False)
        clustering_q_high_manip: Quantile for high ManipScore in clustering (default: 0.9)
        clustering_window_W: Rolling window for clustering (default: 6 bars)
        clustering_min_count: Minimum count for clustered events (default: 3)

    Execution parameters:
        holding_horizon: Maximum holding period in bars (default: 5)
        atr_window: Window for ATR calculation (default: 10)
        sl_atr_mult: Stop-loss as multiple of ATR (default: 0.5)
        tp_atr_mult: Take-profit as multiple of ATR (default: 0.8)
        cost_per_trade: Transaction cost per round-trip (default: 0.0001 = 1bp)
    """
    # Timeframe
    bar_size: str = "5min"

    # Trend parameters
    L_past: int = 5
    vol_window: int = 20
    q_extreme_trend: float = 0.9
    use_normalized_trend: bool = True
    min_abs_R_past: Optional[float] = None

    # ManipScore parameters
    q_manip: float = 0.9
    min_manip_score: Optional[float] = None

    # Multi-timeframe filters (NEW)
    use_daily_confluence: bool = False
    daily_q_extreme_trend: float = 0.9
    daily_q_high_manip: float = 0.9
    daily_min_abs_R_past: Optional[float] = None

    # Clustering filters (NEW)
    use_clustering_filter: bool = False
    clustering_q_high_manip: float = 0.9
    clustering_window_W: int = 6
    clustering_min_count: int = 3

    # Execution parameters
    holding_horizon: int = 5
    atr_window: int = 10
    sl_atr_mult: float = 0.5
    tp_atr_mult: float = 0.8
    cost_per_trade: float = 0.0001


def generate_extreme_reversal_signals(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig,
    return_col: str = 'returns',
    manip_col: str = 'manip_score'
) -> pd.DataFrame:
    """
    生成极端反转策略信号。
    
    Generate trading signals for the Extreme Reversal Strategy.
    
    Signal logic:
    - If extreme_trend AND high_manip:
        - If R_past > 0 (extreme UP): signal = -1 (SHORT, expect reversal down)
        - If R_past < 0 (extreme DOWN): signal = +1 (LONG, expect reversal up)
    - Else: signal = 0 (no trade)
    
    Args:
        bars: DataFrame with at least 'returns' and 'manip_score' columns
        config: ExtremeReversalConfig object
        return_col: Name of return column (default: 'returns')
        manip_col: Name of ManipScore column (default: 'manip_score')
    
    Returns:
        DataFrame with added columns:
        - All trend strength columns (R_past, sigma, TS, etc.)
        - 'extreme_trend': Boolean flag
        - 'high_manip': Boolean flag
        - 'raw_signal': Signal at bar t (based on info up to t)
        - 'exec_signal': Execution signal (shifted to avoid look-ahead bias)
        
    Example:
        >>> config = ExtremeReversalConfig(L_past=5, q_extreme_trend=0.9)
        >>> bars_with_signals = generate_extreme_reversal_signals(bars, config)
        >>> print(f"Signals generated: {(bars_with_signals['exec_signal'] != 0).sum()}")
    """
    bars = bars.copy()
    
    # Validate required columns
    if return_col not in bars.columns:
        raise ValueError(f"Return column '{return_col}' not found")
    if manip_col not in bars.columns:
        raise ValueError(f"ManipScore column '{manip_col}' not found")
    
    # Step 1: Compute trend strength features
    bars = compute_trend_strength(
        bars,
        L_past=config.L_past,
        vol_window=config.vol_window,
        return_col=return_col
    )
    
    # Step 2: Compute extreme trend thresholds
    trend_thresholds = compute_extreme_trend_thresholds(
        bars,
        quantile=config.q_extreme_trend,
        use_normalized=config.use_normalized_trend,
        min_abs_R_past=config.min_abs_R_past
    )
    
    # Step 3: Identify extreme trends
    bars = identify_extreme_trends(
        bars,
        trend_thresholds,
        use_normalized=config.use_normalized_trend
    )
    
    # Step 4: Identify high ManipScore regimes
    manip_threshold = bars[manip_col].quantile(config.q_manip)
    
    # Optional: Override with absolute minimum
    if config.min_manip_score is not None:
        manip_threshold = max(manip_threshold, config.min_manip_score)
    
    bars['high_manip'] = bars[manip_col] >= manip_threshold
    
    # Step 5: Generate raw signals
    # Initialize with zeros
    bars['raw_signal'] = 0
    
    # Condition: extreme trend AND high manip
    signal_condition = bars['extreme_trend'] & bars['high_manip']
    
    # Reversal logic:
    # - Extreme UP (R_past > 0) + high manip → SHORT (-1)
    # - Extreme DOWN (R_past < 0) + high manip → LONG (+1)
    bars.loc[signal_condition & (bars['R_past'] > 0), 'raw_signal'] = -1  # Short
    bars.loc[signal_condition & (bars['R_past'] < 0), 'raw_signal'] = 1   # Long
    
    # Step 6: Shift signal to avoid look-ahead bias
    # Execute at next bar's open based on signal from previous bar
    bars['exec_signal'] = bars['raw_signal'].shift(1).fillna(0).astype(int)
    
    # Store thresholds for reference
    bars.attrs['trend_threshold'] = trend_thresholds
    bars.attrs['manip_threshold'] = manip_threshold
    bars.attrs['config'] = config
    
    return bars

