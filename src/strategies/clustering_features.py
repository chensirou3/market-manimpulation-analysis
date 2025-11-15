"""
Clustering Features for 4H Bars

Detect clusters of high ManipScore bars to distinguish between:
- Isolated high ManipScore events (single spike)
- Clustered high ManipScore events (sustained manipulation over multiple bars)

Hypothesis: Clustered events have stronger reversal quality than isolated events.
"""

import pandas as pd
import numpy as np
from typing import Dict


def compute_4h_clustering_features(
    bars_4h: pd.DataFrame,
    q_high_manip: float = 0.9,
    W: int = 6,
    manip_col: str = 'ManipScore'
) -> pd.DataFrame:
    """
    Compute clustering features for 4h bars.
    
    Features:
    - high_flag: 1 if ManipScore >= threshold, 0 otherwise
    - count_high: rolling count of high_flag over window W
    - density_high: count_high / W (density of high ManipScore bars)
    
    Args:
        bars_4h: 4h bars with ManipScore
        q_high_manip: Quantile for high ManipScore threshold (default: 0.9)
        W: Rolling window size in bars (default: 6 bars ≈ 24 hours)
        manip_col: Name of ManipScore column (default: 'ManipScore')
        
    Returns:
        4h bars with clustering features
    """
    bars_4h = bars_4h.copy()
    
    # Compute high ManipScore threshold
    T_high_manip = bars_4h[manip_col].quantile(q_high_manip)
    
    # High flag: 1 if ManipScore >= threshold
    bars_4h['high_flag'] = (bars_4h[manip_col] >= T_high_manip).astype(int)
    
    # Rolling count of high flags over window W
    # Use min_periods=1 to handle initial bars
    bars_4h['count_high'] = bars_4h['high_flag'].rolling(W, min_periods=1).sum()
    
    # Density: count / window size
    bars_4h['density_high'] = bars_4h['count_high'] / W
    
    # Store threshold for reference
    bars_4h['_T_high_manip'] = T_high_manip
    
    return bars_4h


def classify_events(
    bars_4h: pd.DataFrame,
    min_count_clustered: int = 3,
    max_count_isolated: int = 1
) -> pd.DataFrame:
    """
    Classify events as isolated vs clustered based on count_high.
    
    Classification:
    - isolated: count_high <= max_count_isolated (e.g., 1)
    - clustered: count_high >= min_count_clustered (e.g., 3)
    - intermediate: between isolated and clustered
    
    Adds columns:
    - is_isolated: True if isolated event
    - is_clustered: True if clustered event
    - is_intermediate: True if intermediate
    
    Args:
        bars_4h: 4h bars with count_high
        min_count_clustered: Minimum count for clustered (default: 3)
        max_count_isolated: Maximum count for isolated (default: 1)
        
    Returns:
        4h bars with event classification
    """
    bars_4h = bars_4h.copy()
    
    bars_4h['is_isolated'] = bars_4h['count_high'] <= max_count_isolated
    bars_4h['is_clustered'] = bars_4h['count_high'] >= min_count_clustered
    bars_4h['is_intermediate'] = ~(bars_4h['is_isolated'] | bars_4h['is_clustered'])
    
    return bars_4h


def get_clustering_stats(bars_4h: pd.DataFrame) -> Dict:
    """
    Get statistics about clustering.
    
    Returns:
        dict with:
        - n_bars: total 4h bars
        - n_high_flag: number of high ManipScore bars
        - pct_high: percentage of high ManipScore bars
        - mean_count_high: mean count_high
        - median_count_high: median count_high
        - n_isolated: number of isolated events (if classified)
        - n_clustered: number of clustered events (if classified)
        - n_intermediate: number of intermediate events (if classified)
    """
    n_bars = len(bars_4h)
    n_high_flag = bars_4h['high_flag'].sum() if 'high_flag' in bars_4h.columns else 0
    pct_high = n_high_flag / n_bars * 100 if n_bars > 0 else 0
    
    mean_count = bars_4h['count_high'].mean() if 'count_high' in bars_4h.columns else 0
    median_count = bars_4h['count_high'].median() if 'count_high' in bars_4h.columns else 0
    
    n_isolated = bars_4h['is_isolated'].sum() if 'is_isolated' in bars_4h.columns else 0
    n_clustered = bars_4h['is_clustered'].sum() if 'is_clustered' in bars_4h.columns else 0
    n_intermediate = bars_4h['is_intermediate'].sum() if 'is_intermediate' in bars_4h.columns else 0
    
    return {
        'n_bars': n_bars,
        'n_high_flag': n_high_flag,
        'pct_high': pct_high,
        'mean_count_high': mean_count,
        'median_count_high': median_count,
        'n_isolated': n_isolated,
        'n_clustered': n_clustered,
        'n_intermediate': n_intermediate,
    }


def analyze_clustering_vs_performance(
    bars_4h: pd.DataFrame,
    signal_col: str = 'exec_signal',
    return_col: str = 'forward_return',
    holding_horizon: int = 5
) -> pd.DataFrame:
    """
    Analyze performance of isolated vs clustered events.
    
    Computes:
    - Mean return for isolated events
    - Mean return for clustered events
    - Win rate for isolated events
    - Win rate for clustered events
    
    Args:
        bars_4h: 4h bars with clustering classification and signals
        signal_col: Name of signal column
        return_col: Name of forward return column
        holding_horizon: Holding period in bars
        
    Returns:
        DataFrame with performance comparison
    """
    # Compute forward returns if not already present
    if return_col not in bars_4h.columns:
        bars_4h = bars_4h.copy()
        bars_4h[return_col] = bars_4h['returns'].shift(-1).rolling(holding_horizon).sum().shift(-holding_horizon+1)
    
    # Filter to trades only
    trades = bars_4h[bars_4h[signal_col] != 0].copy()
    
    if len(trades) == 0:
        return pd.DataFrame()
    
    # Compute strategy returns
    trades['strategy_return'] = trades[signal_col] * trades[return_col]
    
    # Analyze by clustering type
    results = []
    
    for event_type in ['isolated', 'clustered', 'intermediate']:
        col_name = f'is_{event_type}'
        if col_name not in trades.columns:
            continue
        
        subset = trades[trades[col_name]]
        
        if len(subset) == 0:
            continue
        
        n_trades = len(subset)
        mean_ret = subset['strategy_return'].mean()
        std_ret = subset['strategy_return'].std()
        win_rate = (subset['strategy_return'] > 0).sum() / n_trades
        
        results.append({
            'event_type': event_type,
            'n_trades': n_trades,
            'mean_return': mean_ret,
            'std_return': std_ret,
            'win_rate': win_rate,
            'sharpe': (mean_ret / std_ret) * np.sqrt(n_trades) if std_ret > 0 else 0,
        })
    
    return pd.DataFrame(results)

