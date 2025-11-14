"""
Orderbook proxy features module.

Since we don't have Level 2 orderbook data, this module constructs proxy features
from tick data and bar data to approximate orderbook characteristics.
"""

import pandas as pd
import numpy as np
from typing import Optional

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def compute_candlestick_features(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Compute candlestick pattern features from OHLC data.
    
    Args:
        bars: DataFrame with OHLC data.
        
    Returns:
        pd.DataFrame: Bars with additional candlestick features.
        
    Added Features:
        - body: Absolute difference between open and close
        - upper_wick: Distance from high to max(open, close)
        - lower_wick: Distance from min(open, close) to low
        - wick_ratio: (upper_wick + lower_wick) / (body + epsilon)
        - body_pct: body as percentage of (high - low)
        
    Examples:
        >>> bars_with_candles = compute_candlestick_features(bars)
    """
    df = bars.copy()
    
    # Body
    df['body'] = np.abs(df['close'] - df['open'])
    
    # Upper and lower wicks
    df['upper_wick'] = df['high'] - np.maximum(df['open'], df['close'])
    df['lower_wick'] = np.minimum(df['open'], df['close']) - df['low']
    
    # Wick ratio (high ratio indicates potential manipulation)
    epsilon = 1e-8
    df['wick_ratio'] = (df['upper_wick'] + df['lower_wick']) / (df['body'] + epsilon)
    
    # Body as percentage of total range
    total_range = df['high'] - df['low']
    df['body_pct'] = df['body'] / (total_range + epsilon)
    
    # Direction (1 for bullish, -1 for bearish)
    df['direction'] = np.where(df['close'] >= df['open'], 1, -1)
    
    return df


def compute_volume_features(
    ticks: pd.DataFrame,
    bars: pd.DataFrame,
    window: int = 20
) -> pd.DataFrame:
    """
    Compute volume-based features from tick data.
    
    Args:
        ticks: DataFrame with tick data (must have 'timestamp', 'volume', optionally 'side').
        bars: DataFrame with bar data (index should be timestamp).
        window: Rolling window size for computing features.
        
    Returns:
        pd.DataFrame: Bars with additional volume features.
        
    Added Features:
        - gross_volume: Sum of absolute volumes (if side available)
        - net_volume: Sum of signed volumes (buy - sell)
        - wash_index: gross_volume / (|net_volume| + epsilon)
        - volume_imbalance: net_volume / gross_volume
        
    Note:
        If 'side' column is not available in ticks, gross_volume = net_volume = volume.
        
    Examples:
        >>> bars_with_vol = compute_volume_features(ticks, bars, window=20)
    """
    df = bars.copy()
    
    # Check if we have side information
    if 'side' in ticks.columns:
        logger.info("Computing volume features with side information")
        
        # Set timestamp as index for ticks
        ticks_indexed = ticks.set_index('timestamp')
        
        # Create signed volume
        ticks_indexed['signed_volume'] = ticks_indexed['volume'].copy()
        ticks_indexed.loc[ticks_indexed['side'] == 'sell', 'signed_volume'] *= -1
        
        # Resample to bar frequency
        bar_freq = pd.infer_freq(df.index)
        if bar_freq is None:
            # Fallback: use median time difference
            bar_freq = pd.Timedelta(df.index.to_series().diff().median())
        
        # Gross volume (sum of absolute values)
        df['gross_volume'] = ticks_indexed['volume'].resample(bar_freq).sum()
        
        # Net volume (sum of signed values)
        df['net_volume'] = ticks_indexed['signed_volume'].resample(bar_freq).sum()
        
        # Fill NaN with 0
        df['gross_volume'] = df['gross_volume'].fillna(0)
        df['net_volume'] = df['net_volume'].fillna(0)
        
    else:
        logger.warning("No 'side' column in ticks, using volume as both gross and net")
        df['gross_volume'] = df['volume']
        df['net_volume'] = df['volume']
    
    # Wash trading index (high value suggests wash trading)
    epsilon = 1e-8
    df['wash_index'] = df['gross_volume'] / (np.abs(df['net_volume']) + epsilon)
    
    # Volume imbalance (-1 to +1, positive means more buying)
    df['volume_imbalance'] = df['net_volume'] / (df['gross_volume'] + epsilon)
    
    # Rolling features
    df['rolling_wash_index'] = df['wash_index'].rolling(window=window).mean()
    df['rolling_imbalance'] = df['volume_imbalance'].rolling(window=window).mean()
    
    return df


def add_orderbook_proxy_features(
    bars: pd.DataFrame,
    ticks: Optional[pd.DataFrame] = None,
    window: int = 20
) -> pd.DataFrame:
    """
    Add all orderbook proxy features to bar data.
    
    This is a convenience function that combines candlestick and volume features.
    
    Args:
        bars: DataFrame with OHLCV data.
        ticks: Optional DataFrame with tick data for volume features.
        window: Rolling window size.
        
    Returns:
        pd.DataFrame: Bars with all proxy features.
        
    Examples:
        >>> bars_enhanced = add_orderbook_proxy_features(bars, ticks, window=20)
    """
    logger.info("Adding orderbook proxy features")
    
    # Add candlestick features
    df = compute_candlestick_features(bars)
    
    # Add volume features if ticks are provided
    if ticks is not None:
        df = compute_volume_features(ticks, df, window=window)
    else:
        logger.warning("No tick data provided, skipping tick-based volume features")
    
    logger.info(f"Added {len(df.columns) - len(bars.columns)} new features")
    
    return df


if __name__ == "__main__":
    # Demo usage with synthetic data
    print("=== Orderbook Proxy Features Demo ===\n")
    
    # Create synthetic bar data
    n_bars = 500
    bars = pd.DataFrame({
        'open': np.random.randn(n_bars).cumsum() + 1850,
        'high': np.random.randn(n_bars).cumsum() + 1852,
        'low': np.random.randn(n_bars).cumsum() + 1848,
        'close': np.random.randn(n_bars).cumsum() + 1850,
        'volume': np.random.randint(100, 1000, n_bars)
    }, index=pd.date_range('2024-01-01', periods=n_bars, freq='1min'))
    
    # Ensure high >= max(open, close) and low <= min(open, close)
    bars['high'] = bars[['open', 'close', 'high']].max(axis=1)
    bars['low'] = bars[['open', 'close', 'low']].min(axis=1)
    
    print(f"Generated {len(bars)} synthetic bars\n")
    
    # Compute candlestick features
    bars_with_candles = compute_candlestick_features(bars)
    print("Candlestick features:")
    print(bars_with_candles[['body', 'upper_wick', 'lower_wick', 'wick_ratio']].head())
    print()
    
    # Create synthetic tick data
    n_ticks = 5000
    ticks = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_ticks, freq='10s'),
        'price': np.random.randn(n_ticks).cumsum() + 1850,
        'volume': np.random.randint(1, 100, n_ticks),
        'side': np.random.choice(['buy', 'sell'], n_ticks)
    })
    
    # Compute volume features
    bars_with_vol = compute_volume_features(ticks, bars, window=20)
    print("Volume features:")
    print(bars_with_vol[['gross_volume', 'net_volume', 'wash_index', 'volume_imbalance']].head())

