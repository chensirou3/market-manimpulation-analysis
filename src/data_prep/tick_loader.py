"""
Tick data loading module.

Provides functions to load tick-level market data from various formats (CSV, Parquet).
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, List
from datetime import datetime

from ..utils.paths import get_data_dir
from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def load_tick_data(
    symbol: str = None,
    start_date: Optional[Union[str, datetime]] = None,
    end_date: Optional[Union[str, datetime]] = None,
    data_dir: Optional[Path] = None,
    file_format: str = 'parquet',
    file_pattern: str = None
) -> pd.DataFrame:
    """
    Load tick data for a given symbol and date range.

    Supports two modes:
    1. Single file mode: Load from {symbol}_ticks.{format}
    2. Multi-file mode: Load from date-partitioned files (dt=YYYY-MM-DD_part-*.parquet)

    Args:
        symbol: Symbol/instrument name (optional for multi-file mode).
        start_date: Start date for filtering (inclusive). If None, load all.
        end_date: End date for filtering (inclusive). If None, load all.
        data_dir: Directory containing tick data. If None, use config default.
        file_format: File format ('csv' or 'parquet').
        file_pattern: Custom file pattern (e.g., 'dt={date}_part-*.parquet').

    Returns:
        pd.DataFrame: Tick data with columns [timestamp, price, volume, bid, ask, spread].

    Expected File Formats:

        Mode 1 - Single file:
            {symbol}_ticks.csv or {symbol}_ticks.parquet

        Mode 2 - Date-partitioned (auto-detected):
            YYYY/MM/tick/dt=YYYY-MM-DD_part-000.parquet

        Columns (auto-adapted):
            - ts_utc (int64) → timestamp (datetime)
            - bid, ask (float64) → price (mid-price)
            - bid_size, ask_size (float64) → volume (total)
            - spread, source, symbol, etc. (preserved)

    Examples:
        >>> # Load from date-partitioned files
        >>> ticks = load_tick_data(start_date='2024-01-01', end_date='2024-01-31')
        >>> print(ticks.head())
                           timestamp    price  volume    bid    ask  spread
        0 2024-01-01 09:30:00.011  1.21032   2.00  1.21024  1.21041  0.00017

        >>> # Load single file
        >>> ticks = load_tick_data(symbol='EURUSD', file_format='csv')
    """
    # Get data directory
    if data_dir is None:
        data_dir = get_data_dir()

    # Determine loading mode
    if file_pattern or (start_date and not symbol):
        # Multi-file mode: load from date-partitioned files
        df = _load_partitioned_data(data_dir, start_date, end_date, file_pattern)
    else:
        # Single file mode
        if not symbol:
            raise ValueError("Either 'symbol' or 'start_date' must be provided")

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

    # Adapt columns to standard format
    df = _adapt_columns(df)

    # Filter by date range
    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        # Make timezone-aware if timestamp is timezone-aware
        if df['timestamp'].dt.tz is not None:
            start_date = start_date.tz_localize('UTC')
        df = df[df['timestamp'] >= start_date]

    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        # Include the entire end date
        end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        # Make timezone-aware if timestamp is timezone-aware
        if df['timestamp'].dt.tz is not None:
            end_date = end_date.tz_localize('UTC')
        df = df[df['timestamp'] <= end_date]

    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)

    if len(df) > 0:
        logger.info(f"Loaded {len(df):,} ticks from {df['timestamp'].min()} to {df['timestamp'].max()}")
    else:
        logger.warning("No data loaded!")

    return df


def _load_partitioned_data(
    data_dir: Path,
    start_date: Optional[Union[str, datetime]],
    end_date: Optional[Union[str, datetime]],
    file_pattern: Optional[str] = None
) -> pd.DataFrame:
    """
    Load data from date-partitioned parquet files.

    Expected structure:
        data/YYYY/MM/tick/dt=YYYY-MM-DD_part-*.parquet
    """
    if start_date is None:
        raise ValueError("start_date is required for partitioned data loading")

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date) if end_date else start_date

    # Generate date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    dfs = []
    files_loaded = 0

    for date in date_range:
        # Construct path: data/YYYY/MM/tick/
        year = date.strftime('%Y')
        month = date.strftime('%m')
        tick_dir = data_dir / year / month / 'tick'

        if not tick_dir.exists():
            logger.debug(f"Directory not found: {tick_dir}")
            continue

        # Find files for this date
        date_str = date.strftime('%Y-%m-%d')
        pattern = file_pattern or f"dt={date_str}_part-*.parquet"
        files = list(tick_dir.glob(pattern))

        if not files:
            logger.debug(f"No files found for {date_str} in {tick_dir}")
            continue

        # Load all parts for this date
        for file_path in files:
            try:
                df_part = pd.read_parquet(file_path)
                dfs.append(df_part)
                files_loaded += 1
                logger.debug(f"Loaded {file_path.name}: {len(df_part):,} rows")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

    if not dfs:
        logger.warning(f"No data files found for date range {start_date.date()} to {end_date.date()}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['timestamp', 'price', 'volume', 'bid', 'ask', 'spread'])

    # Concatenate all dataframes
    df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {files_loaded} files, total {len(df):,} rows")

    return df


def _adapt_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adapt various column formats to standard format.

    Handles:
        - ts_utc (milliseconds) → timestamp (datetime)
        - bid, ask → price (mid-price)
        - bid_size, ask_size → volume (total)
    """
    df = df.copy()

    # 1. Handle timestamp
    if 'timestamp' not in df.columns:
        if 'ts_utc' in df.columns:
            # Convert milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['ts_utc'], unit='ms', utc=True)
        elif 'time' in df.columns:
            df['timestamp'] = pd.to_datetime(df['time'])
        elif 'datetime' in df.columns:
            df['timestamp'] = pd.to_datetime(df['datetime'])
        else:
            raise ValueError(
                f"No timestamp column found. Available columns: {df.columns.tolist()}"
            )
    else:
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 2. Handle price
    if 'price' not in df.columns:
        if 'bid' in df.columns and 'ask' in df.columns:
            # Calculate mid-price
            df['price'] = (df['bid'] + df['ask']) / 2
            logger.debug("Calculated price as mid-price from bid/ask")
        else:
            raise ValueError(
                f"No price column found and cannot calculate from bid/ask. "
                f"Available columns: {df.columns.tolist()}"
            )

    # 3. Handle volume
    if 'volume' not in df.columns:
        if 'bid_size' in df.columns and 'ask_size' in df.columns:
            # Sum bid and ask sizes
            df['volume'] = df['bid_size'] + df['ask_size']
            logger.debug("Calculated volume as sum of bid_size + ask_size")
        elif 'bid_size' in df.columns:
            df['volume'] = df['bid_size']
            logger.debug("Using bid_size as volume")
        elif 'ask_size' in df.columns:
            df['volume'] = df['ask_size']
            logger.debug("Using ask_size as volume")
        else:
            # Set default volume if not available
            df['volume'] = 1.0
            logger.warning("No volume information found, using default value 1.0")

    # 4. Preserve useful columns
    preserve_cols = ['bid', 'ask', 'spread', 'bid_size', 'ask_size',
                     'source', 'symbol', 'side', 'offsession', 'is_spike']

    # Select columns to keep
    standard_cols = ['timestamp', 'price', 'volume']
    extra_cols = [col for col in preserve_cols if col in df.columns]

    final_cols = standard_cols + extra_cols
    df = df[final_cols]

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

