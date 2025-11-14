"""
Time-related utility functions for the manipulation detection toolkit.

Provides functions for time parsing, timezone handling, and time-based features.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Union, Optional


def parse_timestamp(
    timestamp: Union[str, pd.Timestamp, datetime],
    format: Optional[str] = None
) -> pd.Timestamp:
    """
    Parse various timestamp formats to pandas Timestamp.
    
    Args:
        timestamp: Timestamp in various formats.
        format: Optional format string for parsing (e.g., '%Y-%m-%d %H:%M:%S').
        
    Returns:
        pd.Timestamp: Parsed timestamp.
        
    Examples:
        >>> ts = parse_timestamp('2024-01-01 09:30:00')
        >>> print(ts)
        2024-01-01 09:30:00
    """
    if isinstance(timestamp, pd.Timestamp):
        return timestamp
    
    if isinstance(timestamp, datetime):
        return pd.Timestamp(timestamp)
    
    if format:
        return pd.to_datetime(timestamp, format=format)
    
    return pd.to_datetime(timestamp)


def get_time_of_day_features(timestamps: pd.Series) -> pd.DataFrame:
    """
    Extract time-of-day features from timestamps.
    
    Args:
        timestamps: Series of timestamps.
        
    Returns:
        pd.DataFrame: DataFrame with time-of-day features.
        
    Features:
        - hour: Hour of day (0-23)
        - minute: Minute of hour (0-59)
        - day_of_week: Day of week (0=Monday, 6=Sunday)
        - is_market_open: Boolean indicating typical market hours
        
    Examples:
        >>> timestamps = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1h'))
        >>> features = get_time_of_day_features(timestamps)
        >>> print(features.columns)
        Index(['hour', 'minute', 'day_of_week', 'is_market_open'], dtype='object')
    """
    df = pd.DataFrame(index=timestamps.index)
    
    df['hour'] = timestamps.dt.hour
    df['minute'] = timestamps.dt.minute
    df['day_of_week'] = timestamps.dt.dayofweek
    
    # Typical market hours (9:30 - 16:00, Monday-Friday)
    # Adjust based on your market
    df['is_market_open'] = (
        (df['day_of_week'] < 5) &  # Monday-Friday
        (df['hour'] >= 9) & (df['hour'] < 16)
    )
    
    return df


def resample_to_timeframe(
    df: pd.DataFrame,
    timeframe: str,
    timestamp_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Resample DataFrame to a specific timeframe.
    
    Args:
        df: DataFrame with timestamp index or column.
        timeframe: Target timeframe (e.g., '1min', '5min', '1h', '1D').
        timestamp_col: If provided, use this column as timestamp (otherwise use index).
        
    Returns:
        pd.DataFrame: Resampled DataFrame.
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'timestamp': pd.date_range('2024-01-01', periods=100, freq='1s'),
        ...     'value': np.random.randn(100)
        ... })
        >>> resampled = resample_to_timeframe(df, '1min', timestamp_col='timestamp')
    """
    if timestamp_col:
        df = df.set_index(timestamp_col)
    
    # Map common timeframe strings to pandas offset aliases
    timeframe_map = {
        '1min': '1T',
        '5min': '5T',
        '15min': '15T',
        '30min': '30T',
        '1h': '1H',
        '1d': '1D',
        '1D': '1D',
    }
    
    pandas_freq = timeframe_map.get(timeframe, timeframe)
    
    return df.resample(pandas_freq).last()


def get_trading_session(timestamp: pd.Timestamp, market: str = 'US') -> str:
    """
    Determine the trading session for a given timestamp.
    
    Args:
        timestamp: Timestamp to check.
        market: Market identifier ('US', 'EU', 'ASIA').
        
    Returns:
        str: Trading session ('pre_market', 'regular', 'after_hours', 'closed').
        
    Examples:
        >>> ts = pd.Timestamp('2024-01-01 10:00:00')
        >>> session = get_trading_session(ts, market='US')
        >>> print(session)
        regular
    """
    hour = timestamp.hour
    day_of_week = timestamp.dayofweek
    
    # Weekend
    if day_of_week >= 5:
        return 'closed'
    
    if market == 'US':
        if hour < 9 or (hour == 9 and timestamp.minute < 30):
            return 'pre_market'
        elif hour < 16:
            return 'regular'
        elif hour < 20:
            return 'after_hours'
        else:
            return 'closed'
    
    # TODO: Add other markets
    return 'unknown'


def calculate_time_delta_seconds(timestamps: pd.Series) -> pd.Series:
    """
    Calculate time delta in seconds between consecutive timestamps.
    
    Args:
        timestamps: Series of timestamps.
        
    Returns:
        pd.Series: Time deltas in seconds.
        
    Examples:
        >>> timestamps = pd.Series(pd.date_range('2024-01-01', periods=5, freq='1s'))
        >>> deltas = calculate_time_delta_seconds(timestamps)
        >>> print(deltas)
        0    NaN
        1    1.0
        2    1.0
        3    1.0
        4    1.0
        dtype: float64
    """
    return timestamps.diff().dt.total_seconds()


if __name__ == "__main__":
    # Demo usage
    print("=== Time Utils Demo ===\n")
    
    # Parse timestamp
    ts = parse_timestamp('2024-01-01 09:30:00')
    print(f"Parsed timestamp: {ts}\n")
    
    # Time of day features
    timestamps = pd.Series(pd.date_range('2024-01-01 09:00', periods=10, freq='1h'))
    features = get_time_of_day_features(timestamps)
    print("Time of day features:")
    print(features.head())
    print()
    
    # Trading session
    session = get_trading_session(pd.Timestamp('2024-01-01 10:00:00'))
    print(f"Trading session at 10:00: {session}\n")
    
    # Time deltas
    deltas = calculate_time_delta_seconds(timestamps)
    print("Time deltas (seconds):")
    print(deltas.head())

