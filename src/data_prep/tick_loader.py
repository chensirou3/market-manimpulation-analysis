"""
Tick data loading module.

Provides functions to load tick-level market data from various formats (CSV, Parquet).
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, List
from datetime import datetime

from ..utils.paths import get_data_dir, load_config
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def load_tick_data(
    symbol: str,
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    data_dir: Optional[Path] = None,
    file_format: str = 'csv'
) -> pd.DataFrame:
    """
    Load tick data for a given symbol and date range.
    
    Args:
        symbol: Symbol/instrument name (e.g., 'XAUUSD', 'EURUSD').
        start_date: Start date for filtering (inclusive). If None, load all.
        end_date: End date for filtering (inclusive). If None, load all.
        data_dir: Directory containing tick data. If None, use config default.
        file_format: File format ('csv' or 'parquet').
        
    Returns:
        pd.DataFrame: Tick data with columns [timestamp, price, volume, side].
        
    Expected File Format:
        CSV/Parquet files should be named: {symbol}_ticks.csv or {symbol}_ticks.parquet
        
        Required columns:
            - timestamp: datetime or parseable string
            - price: float
            - volume: float
            
        Optional columns:
            - side: str ('buy' or 'sell')
            - bid: float
            - ask: float
            
    Examples:
        >>> ticks = load_tick_data('XAUUSD', start_date='2024-01-01', end_date='2024-01-31')
        >>> print(ticks.head())
                           timestamp    price  volume side
        0 2024-01-01 09:30:00.123  1850.25   100.0  buy
        1 2024-01-01 09:30:00.456  1850.30    50.0  sell
    """
    # Get data directory
    if data_dir is None:
        data_dir = get_data_dir()
    
    # Construct file path
    file_name = f"{symbol}_ticks.{file_format}"
    file_path = data_dir / file_name
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Tick data file not found: {file_path}\n"
            f"Expected format: {symbol}_ticks.{file_format} in {data_dir}"
        )
    
    logger.info(f"Loading tick data from {file_path}")
    
    # Load data based on format
    if file_format == 'csv':
        df = pd.read_csv(file_path)
    elif file_format == 'parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    # Get column names from config
    config = load_config()
    col_config = config.get('data', {}).get('columns', {})
    
    timestamp_col = col_config.get('timestamp', 'timestamp')
    price_col = col_config.get('price', 'price')
    volume_col = col_config.get('volume', 'volume')
    side_col = col_config.get('side', 'side')
    
    # Validate required columns
    required_cols = [timestamp_col, price_col, volume_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(
            f"Missing required columns: {missing_cols}\n"
            f"Available columns: {df.columns.tolist()}"
        )
    
    # Parse timestamp
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    # Rename columns to standard names
    rename_map = {
        timestamp_col: 'timestamp',
        price_col: 'price',
        volume_col: 'volume'
    }
    
    if side_col in df.columns:
        rename_map[side_col] = 'side'
    
    df = df.rename(columns=rename_map)
    
    # Filter by date range
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        df = df[df['timestamp'] >= start_date]
    
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        df = df[df['timestamp'] <= end_date]
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"Loaded {len(df):,} ticks from {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df


def load_multiple_symbols(
    symbols: List[str],
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    **kwargs
) -> dict:
    """
    Load tick data for multiple symbols.
    
    Args:
        symbols: List of symbol names.
        start_date: Start date for filtering.
        end_date: End date for filtering.
        **kwargs: Additional arguments passed to load_tick_data.
        
    Returns:
        dict: Dictionary mapping symbol -> DataFrame.
        
    Examples:
        >>> data = load_multiple_symbols(['XAUUSD', 'EURUSD'], start_date='2024-01-01')
        >>> print(data.keys())
        dict_keys(['XAUUSD', 'EURUSD'])
    """
    result = {}
    
    for symbol in symbols:
        try:
            result[symbol] = load_tick_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to load {symbol}: {e}")
    
    return result


if __name__ == "__main__":
    # Demo usage (will fail if no data file exists)
    print("=== Tick Loader Demo ===\n")
    print("To use this module, place tick data files in the data/ directory.")
    print("Expected format: {symbol}_ticks.csv or {symbol}_ticks.parquet\n")
    print("Example CSV format:")
    print("timestamp,price,volume,side")
    print("2024-01-01 09:30:00.123,1850.25,100,buy")
    print("2024-01-01 09:30:00.456,1850.30,50,sell")

