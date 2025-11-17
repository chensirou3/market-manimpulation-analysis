"""
Trend Filter Module

Implements moving average-based trend filters for regime detection.
Used to suppress entry signals during downtrends to reduce drawdowns.

Author: Market Manipulation Analysis Project
Date: 2025-01-17
Phase: 24 - Trend Filter Testing
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_trend_filter_ma(
    bars_4h: pd.DataFrame,
    ma_length: int = 200,
    use_daily: bool = True
) -> pd.Series:
    """
    Compute a trend filter series for BTCUSD 4H based on moving average.
    
    The trend filter identifies uptrend regimes where:
        trend_up[t] = True if close[t] > MA[t], False otherwise
    
    Parameters
    ----------
    bars_4h : pd.DataFrame
        4H bar data with DatetimeIndex and 'close' column
    ma_length : int, default=200
        Moving average length (in days if use_daily=True, in 4H bars if False)
    use_daily : bool, default=True
        If True:
            - Resample 4H bars to daily closes (last close of each day)
            - Compute MA over 'ma_length' daily closes
            - Forward-fill MA back to 4H index
        If False:
            - Compute rolling mean over 'ma_length' 4H closes directly
    
    Returns
    -------
    trend_up : pd.Series
        Boolean series aligned with bars_4h.index
        True where close > MA (uptrend), False otherwise
    
    Notes
    -----
    - The moving average is computed causally (no look-ahead bias)
    - MA at time t uses closes up to and including t
    - For daily MA: we use last close of each day, then forward-fill to 4H
    - This is a standard approach for trend regime detection
    
    Examples
    --------
    >>> bars = pd.read_csv("results/BTCUSD_4h_bars.csv", parse_dates=["timestamp"])
    >>> bars = bars.set_index("timestamp")
    >>> trend_up = compute_trend_filter_ma(bars, ma_length=200, use_daily=True)
    >>> print(f"Uptrend bars: {trend_up.sum()} / {len(trend_up)} ({trend_up.mean()*100:.1f}%)")
    """
    
    if "close" not in bars_4h.columns:
        raise ValueError("bars_4h must contain 'close' column")
    
    if not isinstance(bars_4h.index, pd.DatetimeIndex):
        raise ValueError("bars_4h must have DatetimeIndex")
    
    close = bars_4h["close"].copy()
    
    if use_daily:
        # Approach 1: Daily MA200 (smoother, recommended)
        # Resample to daily, taking last close of each day
        daily_close = close.resample("D").last()
        
        # Compute rolling mean over ma_length daily closes
        # This is causal: MA at day t uses closes from day t-199 to day t
        daily_ma = daily_close.rolling(window=ma_length, min_periods=ma_length).mean()
        
        # Forward-fill daily MA back to 4H index
        # This ensures each 4H bar uses the MA from its corresponding day
        ma_4h = daily_ma.reindex(close.index, method="ffill")
        
    else:
        # Approach 2: 4H MA200 (more responsive, but noisier)
        # Compute rolling mean over ma_length 4H bars directly
        # For 4H bars, 200 bars = 800 hours = 33.3 days
        ma_4h = close.rolling(window=ma_length, min_periods=ma_length).mean()
    
    # Compute trend regime: uptrend when close > MA
    trend_up = close > ma_4h
    
    # Handle NaN values (first ma_length bars will have NaN MA)
    # Conservative approach: treat NaN as False (no trend filter active)
    trend_up = trend_up.fillna(False)
    
    return trend_up


def apply_trend_filter(
    signal_exec: pd.Series,
    trend_up: pd.Series
) -> pd.Series:
    """
    Apply trend filter to entry signals.
    
    Suppresses entry signals when trend regime is not uptrend.
    Exit logic remains unchanged (positions are managed by exit rules only).
    
    Parameters
    ----------
    signal_exec : pd.Series
        Original execution signals (0 or 1)
        1 means: enter long at this bar if no position is open
    trend_up : pd.Series
        Boolean trend regime series
        True = uptrend (allow entries), False = downtrend (suppress entries)
    
    Returns
    -------
    signal_exec_filtered : pd.Series
        Filtered execution signals
        signal_exec_filtered[t] = signal_exec[t] if trend_up[t] is True
                                   0 otherwise
    
    Notes
    -----
    - This is a hard filter on ENTRIES only
    - If there is already an open position and trend_up flips to False,
      we keep managing the position by exit rule only (SL/TP/Trail/max_bars)
    - We do NOT force exit when trend breaks (can be tested separately)
    
    Examples
    --------
    >>> signal_exec = pd.Series([0, 1, 0, 1, 0], index=pd.date_range("2020-01-01", periods=5, freq="4H"))
    >>> trend_up = pd.Series([True, True, False, False, True], index=signal_exec.index)
    >>> signal_filtered = apply_trend_filter(signal_exec, trend_up)
    >>> print(signal_filtered.values)  # [0, 1, 0, 0, 0]
    """
    
    if not signal_exec.index.equals(trend_up.index):
        raise ValueError("signal_exec and trend_up must have the same index")
    
    # Suppress signals when trend is not up
    signal_exec_filtered = signal_exec.copy()
    signal_exec_filtered[~trend_up] = 0
    
    return signal_exec_filtered


def compute_trend_filter_stats(
    signal_exec: pd.Series,
    signal_exec_filtered: pd.Series,
    trend_up: pd.Series
) -> dict:
    """
    Compute statistics about trend filter impact on signals.
    
    Parameters
    ----------
    signal_exec : pd.Series
        Original signals
    signal_exec_filtered : pd.Series
        Filtered signals
    trend_up : pd.Series
        Trend regime
    
    Returns
    -------
    stats : dict
        Statistics including:
        - total_signals_original: number of original signals
        - total_signals_filtered: number of filtered signals
        - signals_suppressed: number of signals suppressed by filter
        - suppression_rate: percentage of signals suppressed
        - uptrend_bars: number of bars in uptrend
        - uptrend_pct: percentage of bars in uptrend
    """
    
    total_original = signal_exec.sum()
    total_filtered = signal_exec_filtered.sum()
    suppressed = total_original - total_filtered
    
    uptrend_bars = trend_up.sum()
    total_bars = len(trend_up)
    
    stats = {
        "total_signals_original": int(total_original),
        "total_signals_filtered": int(total_filtered),
        "signals_suppressed": int(suppressed),
        "suppression_rate": suppressed / total_original if total_original > 0 else 0.0,
        "uptrend_bars": int(uptrend_bars),
        "total_bars": int(total_bars),
        "uptrend_pct": uptrend_bars / total_bars if total_bars > 0 else 0.0,
    }
    
    return stats

