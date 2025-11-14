"""
Bar aggregation module.

Converts tick-level data to OHLCV bars with additional features.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union

from ..utils.logging_utils import get_logger
from ..utils.paths import load_config

logger = get_logger(__name__)


def ticks_to_bars(
    df_ticks: pd.DataFrame,
    timeframe: str = '1min',
    compute_features: bool = True
) -> pd.DataFrame:
    """
    Aggregate tick data to OHLCV bars.
    
    Args:
        df_ticks: DataFrame with tick data (must have 'timestamp', 'price', 'volume').
        timeframe: Bar timeframe (e.g., '1min', '5min', '1h').
        compute_features: If True, compute additional features (VWAP, rolling stats).
        
    Returns:
        pd.DataFrame: Bar data with OHLCV and optional features.
        
    Output Columns:
        - open, high, low, close: OHLC prices
        - volume: Total volume
        - n_trades: Number of ticks in the bar
        - vwap: Volume-weighted average price (if compute_features=True)
        - rolling_vol: Rolling volatility (if compute_features=True)
        - rolling_volume: Rolling average volume (if compute_features=True)
        
    Examples:
        >>> ticks = pd.DataFrame({
        ...     'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1s'),
        ...     'price': np.random.randn(1000).cumsum() + 100,
        ...     'volume': np.random.randint(1, 100, 1000)
        ... })
        >>> bars = ticks_to_bars(ticks, timeframe='1min')
        >>> print(bars.head())
    """
    # Validate input
    required_cols = ['timestamp', 'price', 'volume']
    missing_cols = [col for col in required_cols if col not in df_ticks.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Set timestamp as index
    df = df_ticks.copy()
    df = df.set_index('timestamp')
    
    # Map timeframe to pandas frequency
    timeframe_map = {
        '1min': '1T',
        '5min': '5T',
        '15min': '15T',
        '30min': '30T',
        '1h': '1H',
        '1d': '1D',
        '1D': '1D',
    }
    
    freq = timeframe_map.get(timeframe, timeframe)
    
    logger.info(f"Aggregating {len(df):,} ticks to {timeframe} bars")
    
    # Aggregate to OHLCV
    bars = pd.DataFrame()
    
    bars['open'] = df['price'].resample(freq).first()
    bars['high'] = df['price'].resample(freq).max()
    bars['low'] = df['price'].resample(freq).min()
    bars['close'] = df['price'].resample(freq).last()
    bars['volume'] = df['volume'].resample(freq).sum()
    bars['n_trades'] = df['price'].resample(freq).count()
    
    # Drop bars with no trades
    bars = bars.dropna(subset=['close'])
    
    # Compute VWAP
    if compute_features:
        # VWAP: volume-weighted average price
        df['value'] = df['price'] * df['volume']
        bars['vwap'] = df['value'].resample(freq).sum() / bars['volume']
        
        # Load config for rolling window parameters
        config = load_config()
        vol_window = config.get('bars', {}).get('rolling_volatility_window', 20)
        volume_window = config.get('bars', {}).get('rolling_volume_window', 20)
        
        # Compute returns
        bars['returns'] = bars['close'].pct_change()
        
        # Rolling volatility (annualized, assuming 252 trading days)
        bars['rolling_vol'] = bars['returns'].rolling(window=vol_window).std()
        
        # Rolling average volume
        bars['rolling_volume'] = bars['volume'].rolling(window=volume_window).mean()
        
        # Fill NaN in rolling features with forward fill
        bars['rolling_vol'] = bars['rolling_vol'].fillna(method='bfill')
        bars['rolling_volume'] = bars['rolling_volume'].fillna(method='bfill')
    
    logger.info(f"Created {len(bars):,} bars from {bars.index.min()} to {bars.index.max()}")
    
    return bars


def add_technical_indicators(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Add common technical indicators to bar data.
    
    Args:
        bars: DataFrame with OHLCV data.
        
    Returns:
        pd.DataFrame: Bars with additional technical indicators.
        
    Added Indicators:
        - sma_20: 20-period simple moving average
        - ema_12: 12-period exponential moving average
        - rsi_14: 14-period relative strength index
        
    TODO: Expand with more indicators as needed.
    
    Examples:
        >>> bars_with_indicators = add_technical_indicators(bars)
    """
    df = bars.copy()
    
    # Simple Moving Average
    df['sma_20'] = df['close'].rolling(window=20).mean()
    
    # Exponential Moving Average
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    return df


if __name__ == "__main__":
    # Demo usage with synthetic data
    print("=== Bar Aggregator Demo ===\n")
    
    # Create synthetic tick data
    n_ticks = 10000
    ticks = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01 09:30', periods=n_ticks, freq='1s'),
        'price': np.random.randn(n_ticks).cumsum() + 1850,
        'volume': np.random.randint(1, 100, n_ticks)
    })
    
    print(f"Generated {len(ticks):,} synthetic ticks")
    print(f"Time range: {ticks['timestamp'].min()} to {ticks['timestamp'].max()}\n")
    
    # Aggregate to 1-minute bars
    bars = ticks_to_bars(ticks, timeframe='1min', compute_features=True)
    
    print(f"Aggregated to {len(bars):,} bars")
    print("\nFirst 5 bars:")
    print(bars.head())
    
    print("\nBar columns:")
    print(bars.columns.tolist())
    
    # Add technical indicators
    bars_with_ta = add_technical_indicators(bars)
    print("\nColumns after adding technical indicators:")
    print(bars_with_ta.columns.tolist())

