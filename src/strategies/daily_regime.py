"""
Daily Regime Features

Compute daily-level trend and ManipScore features to define "extreme regime" conditions.
These are used as higher-timeframe filters for 4h trading signals.
"""

import pandas as pd
import numpy as np
from typing import Dict


def compute_daily_trend_features(
    bars_1d: pd.DataFrame,
    L_past: int = 5,
    vol_window: int = 20,
    return_col: str = 'returns'
) -> pd.DataFrame:
    """
    Compute daily trend features similar to 4h trend features.
    
    Features:
    - daily_R_past: cumulative return over L_past daily bars
    - daily_sigma: rolling std of daily returns over vol_window
    - daily_TS: daily_R_past / daily_sigma (trend strength)
    - daily_abs_R_past: |daily_R_past|
    - daily_abs_TS: |daily_TS|
    
    Args:
        bars_1d: Daily bars with returns
        L_past: Lookback window for cumulative return (default: 5 days)
        vol_window: Window for volatility estimation (default: 20 days)
        return_col: Name of return column (default: 'returns')
        
    Returns:
        Daily bars with added trend features
    """
    bars_1d = bars_1d.copy()
    
    # Cumulative return over L_past bars
    bars_1d['R_past'] = bars_1d[return_col].rolling(L_past).sum()
    
    # Rolling volatility
    bars_1d['sigma'] = bars_1d[return_col].rolling(vol_window).std()
    
    # Fill NaN sigma with forward fill, then with overall std
    bars_1d['sigma'] = bars_1d['sigma'].ffill().fillna(bars_1d[return_col].std())
    
    # Trend strength (normalized)
    bars_1d['TS'] = bars_1d['R_past'] / bars_1d['sigma']
    
    # Absolute values
    bars_1d['abs_R_past'] = bars_1d['R_past'].abs()
    bars_1d['abs_TS'] = bars_1d['TS'].abs()
    
    return bars_1d


def define_daily_extreme_regimes(
    bars_1d: pd.DataFrame,
    q_extreme_trend: float = 0.9,
    q_manip: float = 0.9,
    min_abs_R_past: float = None
) -> Dict:
    """
    Compute quantile-based thresholds for daily "extreme" regimes.
    
    An extreme regime is defined as:
    - High absolute trend strength: |R_past| >= threshold
    - High ManipScore: ManipScore >= threshold
    
    Args:
        bars_1d: Daily bars with trend features and ManipScore
        q_extreme_trend: Quantile for extreme trend (default: 0.9)
        q_manip: Quantile for high ManipScore (default: 0.9)
        min_abs_R_past: Minimum absolute R_past (optional)
        
    Returns:
        dict with thresholds:
        - T_extreme_trend: threshold for |R_past| or |TS|
        - T_high_manip: threshold for ManipScore
        - min_abs_R_past: minimum |R_past| filter
    """
    # Compute thresholds
    # Use abs_TS for normalized trend strength
    T_extreme_trend = bars_1d['abs_TS'].quantile(q_extreme_trend)
    T_high_manip = bars_1d['ManipScore'].quantile(q_manip)
    
    thresholds = {
        'T_extreme_trend': T_extreme_trend,
        'T_high_manip': T_high_manip,
        'min_abs_R_past': min_abs_R_past,
        'q_extreme_trend': q_extreme_trend,
        'q_manip': q_manip,
    }
    
    return thresholds


def identify_daily_extreme_regimes(
    bars_1d: pd.DataFrame,
    thresholds: Dict
) -> pd.DataFrame:
    """
    Identify daily extreme regimes based on thresholds.
    
    Adds columns:
    - daily_extreme_up: extreme UP regime (R_past > 0, high |TS|, high ManipScore)
    - daily_extreme_down: extreme DOWN regime (R_past < 0, high |TS|, high ManipScore)
    - daily_extreme_any: any extreme regime
    
    Args:
        bars_1d: Daily bars with trend features and ManipScore
        thresholds: Thresholds from define_daily_extreme_regimes()
        
    Returns:
        Daily bars with regime flags
    """
    bars_1d = bars_1d.copy()
    
    T_extreme_trend = thresholds['T_extreme_trend']
    T_high_manip = thresholds['T_high_manip']
    min_abs_R_past = thresholds.get('min_abs_R_past')
    
    # High trend strength
    high_trend = bars_1d['abs_TS'] >= T_extreme_trend
    
    # High ManipScore
    high_manip = bars_1d['ManipScore'] >= T_high_manip
    
    # Apply minimum R_past filter if specified
    if min_abs_R_past is not None:
        high_trend = high_trend & (bars_1d['abs_R_past'] >= min_abs_R_past)
    
    # Extreme UP regime
    bars_1d['extreme_up'] = (bars_1d['R_past'] > 0) & high_trend & high_manip
    
    # Extreme DOWN regime
    bars_1d['extreme_down'] = (bars_1d['R_past'] < 0) & high_trend & high_manip
    
    # Any extreme regime
    bars_1d['extreme_any'] = bars_1d['extreme_up'] | bars_1d['extreme_down']
    
    return bars_1d


def get_daily_regime_stats(bars_1d: pd.DataFrame) -> Dict:
    """
    Get statistics about daily extreme regimes.
    
    Returns:
        dict with:
        - n_days: total days
        - n_extreme_up: number of extreme UP days
        - n_extreme_down: number of extreme DOWN days
        - n_extreme_any: number of extreme days (any direction)
        - pct_extreme: percentage of extreme days
    """
    n_days = len(bars_1d)
    n_extreme_up = bars_1d['extreme_up'].sum() if 'extreme_up' in bars_1d.columns else 0
    n_extreme_down = bars_1d['extreme_down'].sum() if 'extreme_down' in bars_1d.columns else 0
    n_extreme_any = bars_1d['extreme_any'].sum() if 'extreme_any' in bars_1d.columns else 0
    pct_extreme = n_extreme_any / n_days * 100 if n_days > 0 else 0
    
    return {
        'n_days': n_days,
        'n_extreme_up': n_extreme_up,
        'n_extreme_down': n_extreme_down,
        'n_extreme_any': n_extreme_any,
        'pct_extreme': pct_extreme,
    }

