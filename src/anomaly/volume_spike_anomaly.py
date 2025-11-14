"""
Volume spike anomaly detection module.

Detects unusual volume spikes relative to historical patterns,
accounting for time-of-day seasonality.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def compute_volume_baseline(
    bars: pd.DataFrame,
    lookback_days: int = 30,
    group_by_time: bool = True
) -> pd.DataFrame:
    """
    Compute volume baseline statistics from historical data.
    
    Args:
        bars: DataFrame with volume data and datetime index.
        lookback_days: Number of days to use for baseline calculation.
        group_by_time: If True, compute separate baselines for each time-of-day.
        
    Returns:
        pd.DataFrame: Baseline statistics (mean, std) by time bucket.
        
    Examples:
        >>> baseline = compute_volume_baseline(bars, lookback_days=30)
    """
    df = bars.copy()
    
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("bars must have a DatetimeIndex")
    
    # Use only recent data
    cutoff_date = df.index.max() - pd.Timedelta(days=lookback_days)
    df_recent = df[df.index >= cutoff_date]
    
    if group_by_time:
        # Group by hour and minute
        df_recent['hour'] = df_recent.index.hour
        df_recent['minute'] = df_recent.index.minute
        
        # Compute mean and std for each time bucket
        baseline = df_recent.groupby(['hour', 'minute'])['volume'].agg(['mean', 'std'])
        baseline['std'] = baseline['std'].fillna(baseline['mean'] * 0.1)  # Fallback for single samples
        
        logger.info(f"Computed volume baseline for {len(baseline)} time buckets")
    else:
        # Global baseline
        baseline = pd.DataFrame({
            'mean': [df_recent['volume'].mean()],
            'std': [df_recent['volume'].std()]
        })
        
        logger.info(f"Computed global volume baseline: mean={baseline['mean'].iloc[0]:.2f}")
    
    return baseline


def compute_volume_spike_score(
    bars: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.Series:
    """
    Compute volume spike anomaly scores.
    
    Args:
        bars: DataFrame with volume data and datetime index.
        config: Configuration dict with parameters.
        
    Returns:
        pd.Series: Volume spike scores (z-scores).
        
    Configuration:
        - lookback_days: Days of history for baseline (default: 30)
        - z_threshold: Z-score threshold for flagging (default: 3.0)
        - group_by_time: Whether to account for time-of-day (default: True)
        
    Interpretation:
        - z > 3.0: Significant volume spike
        - z > 5.0: Extreme volume spike (potential manipulation)
        
    Examples:
        >>> scores = compute_volume_spike_score(bars, config)
        >>> spikes = scores[scores > 3.0]
    """
    if config is None:
        config = {}
    
    lookback_days = config.get('lookback_days', 30)
    group_by_time = config.get('group_by_time', True)
    
    logger.info(f"Computing volume spike scores (lookback={lookback_days} days)")
    
    # Compute baseline
    baseline = compute_volume_baseline(bars, lookback_days, group_by_time)
    
    # Prepare data
    df = bars.copy()
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # Compute z-scores
    z_scores = pd.Series(np.nan, index=df.index, name='volume_spike_score')
    
    if group_by_time:
        for idx, row in df.iterrows():
            hour, minute = row['hour'], row['minute']
            
            if (hour, minute) in baseline.index:
                mean = baseline.loc[(hour, minute), 'mean']
                std = baseline.loc[(hour, minute), 'std']
                
                z = (row['volume'] - mean) / (std + 1e-8)
                z_scores.loc[idx] = z
            else:
                # No baseline for this time bucket (use global mean)
                z_scores.loc[idx] = 0.0
    else:
        mean = baseline['mean'].iloc[0]
        std = baseline['std'].iloc[0]
        z_scores = (df['volume'] - mean) / (std + 1e-8)
    
    logger.info(f"Computed volume spike scores. Mean: {z_scores.mean():.3f}, Max: {z_scores.max():.3f}")
    logger.info(f"Spikes (z > 3.0): {(z_scores > 3.0).sum()} / {len(z_scores)}")
    
    return z_scores


def normalize_to_score(z_scores: pd.Series, method: str = 'sigmoid') -> pd.Series:
    """
    Normalize z-scores to [0, 1] range.
    
    Args:
        z_scores: Series of z-scores.
        method: Normalization method ('sigmoid', 'minmax', 'clip').
        
    Returns:
        pd.Series: Normalized scores in [0, 1].
        
    Examples:
        >>> normalized = normalize_to_score(z_scores, method='sigmoid')
    """
    if method == 'sigmoid':
        # Sigmoid function: 1 / (1 + exp(-z))
        scores = 1 / (1 + np.exp(-z_scores))
    elif method == 'minmax':
        # Min-max normalization
        scores = (z_scores - z_scores.min()) / (z_scores.max() - z_scores.min() + 1e-8)
    elif method == 'clip':
        # Clip to [0, 5] then scale to [0, 1]
        scores = np.clip(z_scores, 0, 5) / 5.0
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return scores


if __name__ == "__main__":
    # Demo with synthetic data
    print("=== Volume Spike Anomaly Detection Demo ===\n")
    
    # Create synthetic bar data with time-of-day pattern
    n_days = 60
    bars_per_day = 390  # 6.5 hours * 60 minutes
    n_bars = n_days * bars_per_day
    
    np.random.seed(42)
    
    # Create datetime index (trading hours: 9:30 - 16:00)
    dates = pd.date_range('2024-01-01 09:30', periods=n_bars, freq='1min')
    dates = dates[dates.hour < 16]  # Filter to market hours
    
    # Base volume with time-of-day pattern
    hours = dates.hour.values
    base_volume = 500 + 200 * np.sin((hours - 9.5) * np.pi / 6.5)  # Higher at open/close
    
    # Add noise
    volume = base_volume + np.random.randn(len(dates)) * 50
    volume = np.maximum(volume, 10)  # Ensure positive
    
    bars = pd.DataFrame({'volume': volume}, index=dates)
    
    # Inject volume spikes
    spike_indices = [1000, 2000, 3000, 4000]
    for idx in spike_indices:
        if idx < len(bars):
            bars.iloc[idx, 0] *= 5  # 5x normal volume
    
    print(f"Created {len(bars)} bars with {len(spike_indices)} injected spikes\n")
    
    # Compute volume spike scores
    config = {
        'lookback_days': 30,
        'group_by_time': True,
        'z_threshold': 3.0
    }
    
    scores = compute_volume_spike_score(bars, config)
    
    print("\nTop 10 volume spikes:")
    top_spikes = scores.nlargest(10)
    print(top_spikes)
    
    print(f"\nDetected {(scores > 3.0).sum()} spikes with z > 3.0")
    
    # Normalize to [0, 1]
    normalized = normalize_to_score(scores, method='sigmoid')
    print(f"\nNormalized scores range: [{normalized.min():.3f}, {normalized.max():.3f}]")

