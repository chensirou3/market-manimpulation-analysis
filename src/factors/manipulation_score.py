"""
Manipulation score factor construction module.

Aggregates multiple anomaly detection signals into a single manipulation score.
This score can be used for:
- Risk filtering in trading strategies
- Position sizing adjustments
- Post-trade analysis
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict

from ..utils.logging_utils import get_logger
from ..anomaly.price_volume_anomaly import compute_price_volume_anomaly
from ..anomaly.volume_spike_anomaly import compute_volume_spike_score, normalize_to_score
from ..anomaly.structure_anomaly import compute_structure_anomaly

logger = get_logger(__name__)


def normalize_anomaly_scores(
    scores: pd.Series,
    method: str = 'minmax',
    clip_range: Optional[tuple] = None
) -> pd.Series:
    """
    Normalize anomaly scores to [0, 1] range.
    
    Args:
        scores: Series of anomaly scores.
        method: Normalization method ('minmax', 'zscore', 'sigmoid').
        clip_range: Optional (min, max) to clip before normalization.
        
    Returns:
        pd.Series: Normalized scores in [0, 1].
        
    Examples:
        >>> normalized = normalize_anomaly_scores(scores, method='minmax')
    """
    if clip_range is not None:
        scores = scores.clip(clip_range[0], clip_range[1])
    
    if method == 'minmax':
        min_val = scores.min()
        max_val = scores.max()
        if max_val - min_val < 1e-8:
            return pd.Series(0.5, index=scores.index)
        normalized = (scores - min_val) / (max_val - min_val)
        
    elif method == 'zscore':
        # Z-score then sigmoid
        z = (scores - scores.mean()) / (scores.std() + 1e-8)
        normalized = 1 / (1 + np.exp(-z))
        
    elif method == 'sigmoid':
        # Direct sigmoid (assumes scores are already z-scores)
        normalized = 1 / (1 + np.exp(-scores))
        
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized


def compute_manipulation_score(
    bars: pd.DataFrame,
    config: Optional[Dict] = None,
    ticks: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Compute the manipulation score factor.
    
    This function aggregates multiple anomaly detection signals into a single
    manipulation score using weighted averaging.
    
    Args:
        bars: DataFrame with OHLCV and features.
        config: Configuration dict with weights and parameters.
        ticks: Optional tick data for volume-based features.
        
    Returns:
        pd.DataFrame: Input bars with added 'manip_score' column.
        
    Configuration:
        weights:
            price_volume: Weight for price-volume anomaly (default: 0.25)
            volume_spike: Weight for volume spike anomaly (default: 0.25)
            structure: Weight for structural anomaly (default: 0.25)
            wash_trade: Weight for wash trading (default: 0.25)
        normalize: Whether to normalize final score (default: True)
        normalization_method: Method for normalization (default: 'minmax')
        smooth: Whether to smooth the score (default: True)
        smoothing_window: Window for smoothing (default: 5)
        
    Output:
        The 'manip_score' column contains values in [0, 1]:
            - 0: No anomaly detected (normal market behavior)
            - 1: Maximum anomaly (highly suspicious)
            - Typical threshold: 0.6-0.8 for filtering
            
    Important:
        This is a STATISTICAL measure, NOT legal evidence of manipulation.
        Use for risk management and strategy filtering only.
        
    Examples:
        >>> bars_with_score = compute_manipulation_score(bars, config)
        >>> high_risk = bars_with_score[bars_with_score['manip_score'] > 0.7]
    """
    if config is None:
        config = {}
    
    logger.info("Computing manipulation score")
    
    # Get weights from config
    weights = config.get('weights', {})
    w_pv = weights.get('price_volume', 0.25)
    w_vs = weights.get('volume_spike', 0.25)
    w_st = weights.get('structure', 0.25)
    w_wt = weights.get('wash_trade', 0.25)
    
    # Normalize weights to sum to 1
    total_weight = w_pv + w_vs + w_st + w_wt
    w_pv /= total_weight
    w_vs /= total_weight
    w_st /= total_weight
    w_wt /= total_weight
    
    logger.info(f"Weights: PV={w_pv:.2f}, VS={w_vs:.2f}, ST={w_st:.2f}, WT={w_wt:.2f}")
    
    df = bars.copy()
    
    # Compute individual anomaly scores
    # 1. Price-Volume Anomaly
    try:
        pv_scores = compute_price_volume_anomaly(df, config=config.get('anomaly', {}).get('price_volume'))
        pv_scores_norm = normalize_anomaly_scores(pv_scores.abs(), method='minmax')
    except Exception as e:
        logger.warning(f"Failed to compute price-volume anomaly: {e}")
        pv_scores_norm = pd.Series(0.0, index=df.index)
    
    # 2. Volume Spike Anomaly
    try:
        vs_scores = compute_volume_spike_score(df, config=config.get('anomaly', {}).get('volume_spike'))
        vs_scores_norm = normalize_to_score(vs_scores, method='sigmoid')
    except Exception as e:
        logger.warning(f"Failed to compute volume spike anomaly: {e}")
        vs_scores_norm = pd.Series(0.0, index=df.index)
    
    # 3. Structural Anomaly (includes wash trading)
    try:
        st_scores = compute_structure_anomaly(df, config=config.get('anomaly', {}).get('structure'))
        st_scores_norm = st_scores  # Already normalized in compute_structure_anomaly
    except Exception as e:
        logger.warning(f"Failed to compute structural anomaly: {e}")
        st_scores_norm = pd.Series(0.0, index=df.index)
    
    # For now, wash_trade is part of structural anomaly
    # In the future, this could be a separate detector
    wt_scores_norm = st_scores_norm
    
    # Aggregate scores
    manip_score = (
        w_pv * pv_scores_norm +
        w_vs * vs_scores_norm +
        w_st * st_scores_norm +
        w_wt * wt_scores_norm
    )
    
    # Normalize final score if requested
    if config.get('normalize', True):
        method = config.get('normalization_method', 'minmax')
        manip_score = normalize_anomaly_scores(manip_score, method=method)
    
    # Smooth if requested
    if config.get('smooth', True):
        window = config.get('smoothing_window', 5)
        manip_score = manip_score.rolling(window=window, min_periods=1).mean()
    
    # Add to dataframe
    df['manip_score'] = manip_score
    
    # Also add individual components for analysis
    df['manip_pv'] = pv_scores_norm
    df['manip_vs'] = vs_scores_norm
    df['manip_st'] = st_scores_norm
    
    logger.info(f"Manipulation score computed. Mean: {manip_score.mean():.3f}, Max: {manip_score.max():.3f}")
    logger.info(f"High risk bars (score > 0.7): {(manip_score > 0.7).sum()} / {len(manip_score)}")
    
    return df


if __name__ == "__main__":
    # Demo with synthetic data
    print("=== Manipulation Score Demo ===\n")
    
    from ..data_prep.bar_aggregator import ticks_to_bars
    from ..data_prep.features_orderbook_proxy import add_orderbook_proxy_features
    
    # Create synthetic tick data
    n_ticks = 10000
    np.random.seed(42)
    
    ticks = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01 09:30', periods=n_ticks, freq='1s'),
        'price': np.random.randn(n_ticks).cumsum() + 1850,
        'volume': np.random.randint(1, 100, n_ticks),
        'side': np.random.choice(['buy', 'sell'], n_ticks)
    })
    
    # Aggregate to bars
    bars = ticks_to_bars(ticks, timeframe='1min', compute_features=True)
    
    # Add orderbook proxy features
    bars = add_orderbook_proxy_features(bars, ticks, window=20)
    
    print(f"Created {len(bars)} bars with features\n")
    
    # Compute manipulation score
    config = {
        'weights': {
            'price_volume': 0.25,
            'volume_spike': 0.25,
            'structure': 0.25,
            'wash_trade': 0.25
        },
        'normalize': True,
        'normalization_method': 'minmax',
        'smooth': True,
        'smoothing_window': 5,
        'anomaly': {
            'price_volume': {'window': 100},
            'volume_spike': {'lookback_days': 30, 'group_by_time': True},
            'structure': {'wash_trade_window': 20, 'wick_ratio_threshold': 3.0}
        }
    }
    
    bars_with_score = compute_manipulation_score(bars, config, ticks)
    
    print("Manipulation score statistics:")
    print(bars_with_score['manip_score'].describe())
    print()
    
    print("Top 10 highest manipulation scores:")
    print(bars_with_score.nlargest(10, 'manip_score')[['manip_score', 'manip_pv', 'manip_vs', 'manip_st']])

