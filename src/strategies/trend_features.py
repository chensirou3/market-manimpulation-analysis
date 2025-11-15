"""
Trend strength feature computation for reversal strategy.

This module provides utilities to quantify recent trend strength
and identify extreme trend regimes.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def compute_trend_strength(
    bars: pd.DataFrame,
    L_past: int = 5,
    vol_window: int = 20,
    return_col: str = 'returns'
) -> pd.DataFrame:
    """
    计算趋势强度特征。
    
    Adds columns to the input DataFrame:
    - 'R_past': Cumulative return over L_past bars (past trend)
    - 'sigma': Rolling volatility over vol_window bars
    - 'TS': Trend strength = R_past / sigma (volatility-normalized)
    - 'abs_R_past': Absolute value of R_past
    - 'abs_TS': Absolute value of TS
    
    Args:
        bars: DataFrame with at least a return column
        L_past: Lookback window for cumulative return (default: 5)
        vol_window: Window for rolling volatility (default: 20)
        return_col: Name of the return column (default: 'returns')
    
    Returns:
        DataFrame with added trend strength columns
        
    Example:
        >>> bars = compute_trend_strength(bars, L_past=5, vol_window=20)
        >>> print(bars[['R_past', 'sigma', 'TS']].head())
    """
    bars = bars.copy()
    
    # Ensure return column exists
    if return_col not in bars.columns:
        raise ValueError(f"Return column '{return_col}' not found in DataFrame")
    
    # 1. Cumulative return over L_past bars (past trend)
    # R_past_t = sum of returns from t-L_past+1 to t
    bars['R_past'] = bars[return_col].rolling(window=L_past, min_periods=1).sum()
    
    # 2. Rolling volatility (standard deviation)
    bars['sigma'] = bars[return_col].rolling(window=vol_window, min_periods=1).std()
    
    # Handle zero or very small volatility
    bars['sigma'] = bars['sigma'].replace(0, np.nan)
    bars['sigma'] = bars['sigma'].fillna(method='ffill').fillna(bars[return_col].std())
    
    # 3. Volatility-normalized trend strength
    bars['TS'] = bars['R_past'] / bars['sigma']
    
    # 4. Absolute values for threshold comparison
    bars['abs_R_past'] = bars['R_past'].abs()
    bars['abs_TS'] = bars['TS'].abs()
    
    return bars


def compute_extreme_trend_thresholds(
    bars: pd.DataFrame,
    quantile: float = 0.9,
    use_normalized: bool = True,
    min_abs_R_past: Optional[float] = None
) -> Dict[str, float]:
    """
    计算极端趋势的阈值（基于分位数）。
    
    Compute thresholds for identifying extreme trend regimes
    based on quantiles of historical trend strength.
    
    Args:
        bars: DataFrame with trend strength columns (from compute_trend_strength)
        quantile: Quantile level for extreme threshold (default: 0.9)
                 Higher values = more extreme (fewer signals)
        use_normalized: If True, use TS (normalized), else use R_past (default: True)
        min_abs_R_past: Optional absolute minimum threshold for R_past
                       (e.g., 0.005 = 0.5% minimum move)
    
    Returns:
        Dictionary with threshold values:
        - 'threshold': Main threshold value
        - 'metric': Which metric was used ('TS' or 'R_past')
        - 'quantile': The quantile level used
        - 'min_abs_R_past': Absolute minimum if specified
        
    Example:
        >>> thresholds = compute_extreme_trend_thresholds(bars, quantile=0.9)
        >>> print(f"Extreme trend threshold: {thresholds['threshold']:.4f}")
    """
    if use_normalized:
        metric = 'abs_TS'
        metric_name = 'TS'
    else:
        metric = 'abs_R_past'
        metric_name = 'R_past'
    
    # Compute quantile threshold
    threshold = bars[metric].quantile(quantile)
    
    result = {
        'threshold': threshold,
        'metric': metric_name,
        'quantile': quantile,
        'min_abs_R_past': min_abs_R_past
    }
    
    return result


def identify_extreme_trends(
    bars: pd.DataFrame,
    thresholds: Dict[str, float],
    use_normalized: bool = True
) -> pd.DataFrame:
    """
    识别极端趋势时段。
    
    Identify bars that qualify as extreme trend regimes
    based on computed thresholds.
    
    Args:
        bars: DataFrame with trend strength columns
        thresholds: Threshold dictionary from compute_extreme_trend_thresholds
        use_normalized: Must match the setting used in threshold computation
    
    Returns:
        DataFrame with added columns:
        - 'extreme_trend': Boolean flag for extreme trend
        - 'trend_direction': +1 for up, -1 for down, 0 for no extreme trend
        
    Example:
        >>> bars = identify_extreme_trends(bars, thresholds)
        >>> print(f"Extreme trends: {bars['extreme_trend'].sum()}")
    """
    bars = bars.copy()
    
    metric = 'abs_TS' if use_normalized else 'abs_R_past'
    threshold = thresholds['threshold']
    min_abs_R_past = thresholds.get('min_abs_R_past')
    
    # Base extreme trend condition
    extreme_condition = bars[metric] >= threshold
    
    # Optional: Add absolute minimum R_past requirement
    if min_abs_R_past is not None:
        extreme_condition = extreme_condition & (bars['abs_R_past'] >= min_abs_R_past)
    
    bars['extreme_trend'] = extreme_condition
    
    # Determine trend direction for extreme trends
    bars['trend_direction'] = 0
    bars.loc[bars['extreme_trend'] & (bars['R_past'] > 0), 'trend_direction'] = 1   # Up
    bars.loc[bars['extreme_trend'] & (bars['R_past'] < 0), 'trend_direction'] = -1  # Down
    
    return bars

