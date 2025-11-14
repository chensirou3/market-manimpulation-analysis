"""
Structural anomaly detection module.

Detects anomalies in market microstructure:
- Wash trading (high gross volume, low net volume)
- Extreme candlestick patterns (long wicks, small body)
- Mirror trades (placeholder for future tick-level analysis)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def detect_wash_trading(
    bars: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.Series:
    """
    Detect potential wash trading using wash index.
    
    Args:
        bars: DataFrame with 'gross_volume' and 'net_volume' columns.
        config: Configuration dict.
        
    Returns:
        pd.Series: Wash trading scores (0-1, higher = more suspicious).
        
    Wash Index:
        wash_index = gross_volume / (|net_volume| + ε)
        
        High wash_index suggests:
        - Lots of trading activity (gross volume)
        - But little net position change (net volume ≈ 0)
        - Potential self-dealing or coordinated wash trading
        
    Configuration:
        - window: Rolling window for smoothing (default: 20)
        - threshold: Wash index threshold (default: 5.0)
        
    Examples:
        >>> wash_scores = detect_wash_trading(bars, config)
    """
    if config is None:
        config = {}
    
    window = config.get('wash_trade_window', 20)
    threshold = config.get('wash_index_threshold', 5.0)
    
    logger.info(f"Detecting wash trading (window={window}, threshold={threshold})")
    
    # Check required columns
    if 'wash_index' not in bars.columns:
        if 'gross_volume' in bars.columns and 'net_volume' in bars.columns:
            # Compute wash index
            epsilon = 1e-8
            wash_index = bars['gross_volume'] / (np.abs(bars['net_volume']) + epsilon)
        else:
            logger.warning("Missing 'wash_index' or 'gross_volume'/'net_volume' columns")
            return pd.Series(0.0, index=bars.index, name='wash_trading_score')
    else:
        wash_index = bars['wash_index']
    
    # Smooth with rolling mean
    wash_index_smooth = wash_index.rolling(window=window, min_periods=1).mean()
    
    # Convert to score (0-1)
    # Score = 0 if wash_index < threshold, increases above threshold
    scores = np.clip((wash_index_smooth - threshold) / threshold, 0, 1)
    
    logger.info(f"Wash trading detection: {(scores > 0.5).sum()} / {len(scores)} bars flagged")
    
    return pd.Series(scores, index=bars.index, name='wash_trading_score')


def detect_extreme_candlesticks(
    bars: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.Series:
    """
    Detect extreme candlestick patterns.
    
    Args:
        bars: DataFrame with candlestick features ('wick_ratio', 'body', 'volume').
        config: Configuration dict.
        
    Returns:
        pd.Series: Extreme candlestick scores (0-1).
        
    Criteria for extreme patterns:
        - High wick_ratio (long wicks relative to body)
        - High volume (top percentile)
        - Small body (price closes near open)
        
    These patterns may indicate:
        - Stop-loss hunting
        - Spoofing (fake orders to move price)
        - Pump-and-dump (spike then reversal)
        
    Configuration:
        - wick_ratio_threshold: Minimum wick ratio (default: 3.0)
        - volume_percentile_threshold: Volume percentile (default: 0.95)
        
    Examples:
        >>> extreme_scores = detect_extreme_candlesticks(bars, config)
    """
    if config is None:
        config = {}
    
    wick_threshold = config.get('wick_ratio_threshold', 3.0)
    vol_percentile = config.get('volume_percentile_threshold', 0.95)
    
    logger.info(f"Detecting extreme candlesticks (wick_ratio>{wick_threshold}, vol>{vol_percentile})")
    
    # Check required columns
    required = ['wick_ratio', 'body', 'volume']
    missing = [col for col in required if col not in bars.columns]
    
    if missing:
        logger.warning(f"Missing columns for candlestick detection: {missing}")
        return pd.Series(0.0, index=bars.index, name='extreme_candlestick_score')
    
    df = bars.copy()
    
    # Compute volume threshold
    volume_threshold = df['volume'].quantile(vol_percentile)
    
    # Criteria
    high_wick = df['wick_ratio'] > wick_threshold
    high_volume = df['volume'] > volume_threshold
    small_body = df['body'] < df['body'].median()
    
    # Score: combination of criteria
    scores = pd.Series(0.0, index=df.index)
    
    # Partial scores
    scores += high_wick.astype(float) * 0.4
    scores += high_volume.astype(float) * 0.4
    scores += small_body.astype(float) * 0.2
    
    logger.info(f"Extreme candlesticks: {(scores > 0.7).sum()} / {len(scores)} bars flagged")
    
    return pd.Series(scores, index=bars.index, name='extreme_candlestick_score')


def compute_structure_anomaly(
    bars: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.Series:
    """
    Compute overall structural anomaly score.
    
    Combines multiple structural anomaly detectors:
        - Wash trading
        - Extreme candlesticks
        - (Future: mirror trades, layering, etc.)
        
    Args:
        bars: DataFrame with required features.
        config: Configuration dict.
        
    Returns:
        pd.Series: Combined structural anomaly score (0-1).
        
    Examples:
        >>> structure_scores = compute_structure_anomaly(bars, config)
    """
    if config is None:
        config = {}
    
    logger.info("Computing structural anomaly scores")
    
    # Detect wash trading
    wash_scores = detect_wash_trading(bars, config)
    
    # Detect extreme candlesticks
    extreme_scores = detect_extreme_candlesticks(bars, config)
    
    # Combine scores (equal weight for now)
    # TODO: Make weights configurable
    combined = (wash_scores + extreme_scores) / 2.0
    
    logger.info(f"Structural anomaly: mean={combined.mean():.3f}, max={combined.max():.3f}")
    
    return pd.Series(combined, index=bars.index, name='structure_anomaly')


if __name__ == "__main__":
    # Demo with synthetic data
    print("=== Structural Anomaly Detection Demo ===\n")
    
    # Create synthetic bar data
    n_bars = 1000
    np.random.seed(42)
    
    bars = pd.DataFrame({
        'open': np.random.randn(n_bars).cumsum() + 100,
        'high': np.random.randn(n_bars).cumsum() + 102,
        'low': np.random.randn(n_bars).cumsum() + 98,
        'close': np.random.randn(n_bars).cumsum() + 100,
        'volume': np.random.randint(100, 1000, n_bars),
        'gross_volume': np.random.randint(200, 2000, n_bars),
        'net_volume': np.random.randint(-100, 100, n_bars)
    }, index=pd.date_range('2024-01-01', periods=n_bars, freq='1min'))
    
    # Ensure OHLC consistency
    bars['high'] = bars[['open', 'close', 'high']].max(axis=1)
    bars['low'] = bars[['open', 'close', 'low']].min(axis=1)
    
    # Compute candlestick features
    bars['body'] = np.abs(bars['close'] - bars['open'])
    bars['upper_wick'] = bars['high'] - np.maximum(bars['open'], bars['close'])
    bars['lower_wick'] = np.minimum(bars['open'], bars['close']) - bars['low']
    bars['wick_ratio'] = (bars['upper_wick'] + bars['lower_wick']) / (bars['body'] + 1e-8)
    
    # Inject anomalies
    # Wash trading
    bars.loc[bars.index[100:110], 'gross_volume'] = 5000
    bars.loc[bars.index[100:110], 'net_volume'] = 10
    
    # Extreme candlesticks
    bars.loc[bars.index[500], 'wick_ratio'] = 10.0
    bars.loc[bars.index[500], 'volume'] = 5000
    
    print(f"Created {len(bars)} bars with injected anomalies\n")
    
    # Detect wash trading
    config = {
        'wash_trade_window': 20,
        'wash_index_threshold': 5.0,
        'wick_ratio_threshold': 3.0,
        'volume_percentile_threshold': 0.95
    }
    
    wash_scores = detect_wash_trading(bars, config)
    print("Top 5 wash trading scores:")
    print(wash_scores.nlargest(5))
    print()
    
    # Detect extreme candlesticks
    extreme_scores = detect_extreme_candlesticks(bars, config)
    print("Top 5 extreme candlestick scores:")
    print(extreme_scores.nlargest(5))
    print()
    
    # Combined structural anomaly
    structure_scores = compute_structure_anomaly(bars, config)
    print("Top 5 structural anomaly scores:")
    print(structure_scores.nlargest(5))

