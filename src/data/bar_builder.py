"""
Bar Builder - Parameterized by timeframe

Supports building bars at different timeframes (5min, 15min, 30min, 60min)
from tick data or lower timeframe bars.
"""

import pandas as pd
import numpy as np
from typing import Optional


def build_bars(
    ticks_or_lower_bars: pd.DataFrame,
    bar_size: str,
    source_type: str = 'bars'
) -> pd.DataFrame:
    """
    Build bars at specified timeframe from tick data or lower timeframe bars.
    
    Args:
        ticks_or_lower_bars: Input data (tick data or lower timeframe bars)
        bar_size: Target bar size ('5min', '15min', '30min', '60min', etc.)
        source_type: 'ticks' or 'bars' (default: 'bars')
    
    Returns:
        DataFrame with OHLC bars and microstructure features
    """
    if source_type == 'ticks':
        return _build_bars_from_ticks(ticks_or_lower_bars, bar_size)
    else:
        return resample_bars_from_lower_tf(ticks_or_lower_bars, bar_size)


def resample_bars_from_lower_tf(
    lower_bars: pd.DataFrame,
    target_bar_size: str
) -> pd.DataFrame:
    """
    Resample lower timeframe bars to higher timeframe.

    Args:
        lower_bars: DataFrame with lower timeframe bars
                   Expected columns: open, high, low, close, volume,
                                   N_ticks, spread_mean, RV, etc.
        target_bar_size: Target bar size ('15min', '30min', '60min', '4h', '1d', etc.)

    Returns:
        Resampled bars with aggregated microstructure features
    """
    # Ensure index is datetime
    if not isinstance(lower_bars.index, pd.DatetimeIndex):
        raise ValueError("Input bars must have DatetimeIndex")
    
    # Define aggregation rules
    agg_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
    }
    
    # Add volume if exists
    if 'volume' in lower_bars.columns:
        agg_rules['volume'] = 'sum'
    
    # Add microstructure features if they exist
    if 'N_ticks' in lower_bars.columns:
        agg_rules['N_ticks'] = 'sum'  # Total ticks in the period
    
    if 'spread_mean' in lower_bars.columns:
        agg_rules['spread_mean'] = 'mean'  # Average spread
    
    if 'RV' in lower_bars.columns:
        # Realized variance: sum of squared returns
        # For aggregation, we sum the RV from lower bars
        agg_rules['RV'] = 'sum'
    
    # Resample
    resampled = lower_bars.resample(target_bar_size).agg(agg_rules)
    
    # Remove bars with no data
    resampled = resampled.dropna(subset=['open', 'close'])
    
    # Compute returns
    resampled['returns'] = resampled['close'].pct_change()
    
    # Compute mid prices if bid/ask exist
    if 'bid_close' in lower_bars.columns and 'ask_close' in lower_bars.columns:
        bid_agg = lower_bars[['bid_open', 'bid_high', 'bid_low', 'bid_close']].resample(target_bar_size).agg({
            'bid_open': 'first',
            'bid_high': 'max',
            'bid_low': 'min',
            'bid_close': 'last',
        })
        ask_agg = lower_bars[['ask_open', 'ask_high', 'ask_low', 'ask_close']].resample(target_bar_size).agg({
            'ask_open': 'first',
            'ask_high': 'max',
            'ask_low': 'min',
            'ask_close': 'last',
        })
        
        resampled['mid_open'] = (bid_agg['bid_open'] + ask_agg['ask_open']) / 2
        resampled['mid_high'] = (bid_agg['bid_high'] + ask_agg['ask_high']) / 2
        resampled['mid_low'] = (bid_agg['bid_low'] + ask_agg['ask_low']) / 2
        resampled['mid_close'] = (bid_agg['bid_close'] + ask_agg['ask_close']) / 2
    
    return resampled


def _build_bars_from_ticks(
    ticks: pd.DataFrame,
    bar_size: str
) -> pd.DataFrame:
    """
    Build bars from tick data.
    
    Args:
        ticks: Tick data with columns: timestamp, bid, ask, (volume)
        bar_size: Target bar size
    
    Returns:
        OHLC bars with microstructure features
    """
    # Ensure index is datetime
    if not isinstance(ticks.index, pd.DatetimeIndex):
        if 'timestamp' in ticks.columns:
            ticks = ticks.set_index('timestamp')
        else:
            raise ValueError("Ticks must have DatetimeIndex or 'timestamp' column")
    
    # Compute mid price
    ticks['mid'] = (ticks['bid'] + ticks['ask']) / 2
    ticks['spread'] = ticks['ask'] - ticks['bid']
    
    # Resample to bars
    agg_rules = {
        'mid': ['first', 'max', 'min', 'last'],
        'bid': ['first', 'max', 'min', 'last'],
        'ask': ['first', 'max', 'min', 'last'],
        'spread': 'mean',
    }

    if 'volume' in ticks.columns:
        agg_rules['volume'] = 'sum'

    bars = ticks.resample(bar_size).agg(agg_rules)

    # Flatten column names
    bars.columns = ['_'.join(col).strip('_') for col in bars.columns.values]

    # Rename to standard OHLC
    bars = bars.rename(columns={
        'mid_first': 'mid_open',
        'mid_max': 'mid_high',
        'mid_min': 'mid_low',
        'mid_last': 'mid_close',
        'spread_mean': 'spread_mean',
    })

    # Also keep bid/ask OHLC
    bars['bid_open'] = bars.get('bid_first', np.nan)
    bars['bid_high'] = bars.get('bid_max', np.nan)
    bars['bid_low'] = bars.get('bid_min', np.nan)
    bars['bid_close'] = bars.get('bid_last', np.nan)
    bars['ask_open'] = bars.get('ask_first', np.nan)
    bars['ask_high'] = bars.get('ask_max', np.nan)
    bars['ask_low'] = bars.get('ask_min', np.nan)
    bars['ask_close'] = bars.get('ask_last', np.nan)
    
    # Use mid as main OHLC
    bars['open'] = bars['mid_open']
    bars['high'] = bars['mid_high']
    bars['low'] = bars['mid_low']
    bars['close'] = bars['mid_close']
    
    # Compute returns
    bars['returns'] = bars['close'].pct_change()
    
    # Count ticks per bar
    bars['N_ticks'] = ticks.resample(bar_size).size()
    
    # Compute realized variance (sum of squared tick returns within bar)
    tick_returns = ticks['mid'].pct_change()
    bars['RV'] = tick_returns.resample(bar_size).apply(lambda x: (x**2).sum())
    
    # Remove bars with no data
    bars = bars.dropna(subset=['open', 'close'])
    
    return bars

