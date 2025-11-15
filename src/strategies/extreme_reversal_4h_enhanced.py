"""
Enhanced 4H Extreme Reversal Strategy with Multi-Timeframe and Clustering Filters

This module extends the baseline 4h extreme reversal strategy with:
1. Daily regime confluence filter
2. 4h signal clustering filter

Goal: Increase signal quality by filtering for:
- Multi-day stretched conditions (daily confluence)
- Sustained manipulation patterns (clustering)
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple

from .extreme_reversal import ExtremeReversalConfig, generate_extreme_reversal_signals
from .trend_features import compute_trend_strength, compute_extreme_trend_thresholds
from .daily_regime import (
    compute_daily_trend_features,
    define_daily_extreme_regimes,
    identify_daily_extreme_regimes
)
from .clustering_features import (
    compute_4h_clustering_features,
    classify_events
)
from ..features.multitimeframe_alignment import align_4h_with_daily


def generate_asymmetric_signals(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig,
    return_col: str = 'returns',
    manip_col: str = 'ManipScore'
) -> pd.DataFrame:
    """
    Generate asymmetric strategy signals.

    Logic:
    - Extreme UP + high manip → LONG (+1, follow trend)
    - Extreme DOWN + high manip → LONG (+1, reversal/bounce)

    Both directions go LONG, exploiting different market dynamics.

    Args:
        bars: DataFrame with returns and ManipScore
        config: ExtremeReversalConfig
        return_col: Name of return column
        manip_col: Name of ManipScore column

    Returns:
        DataFrame with signals
    """
    bars = bars.copy()

    # Compute trend features
    bars = compute_trend_strength(
        bars,
        L_past=config.L_past,
        vol_window=config.vol_window,
        return_col=return_col
    )

    # Compute extreme trend thresholds
    trend_thresholds = compute_extreme_trend_thresholds(
        bars,
        quantile=config.q_extreme_trend,
        use_normalized=config.use_normalized_trend,
        min_abs_R_past=config.min_abs_R_past
    )

    # Identify extreme trends
    # Use absolute value threshold for both UP and DOWN
    threshold = trend_thresholds['threshold']

    if config.use_normalized_trend:
        # Extreme UP: TS > threshold (positive strong trend)
        # Extreme DOWN: TS < -threshold (negative strong trend)
        extreme_up = (bars['TS'] >= threshold)
        extreme_down = (bars['TS'] <= -threshold)
    else:
        # Extreme UP: R_past > threshold
        # Extreme DOWN: R_past < -threshold
        extreme_up = (bars['R_past'] >= threshold)
        extreme_down = (bars['R_past'] <= -threshold)

    # Apply minimum R_past filter if specified
    if config.min_abs_R_past is not None:
        extreme_up = extreme_up & (bars['abs_R_past'] >= config.min_abs_R_past)
        extreme_down = extreme_down & (bars['abs_R_past'] >= config.min_abs_R_past)

    # Identify high ManipScore
    manip_threshold = bars[manip_col].quantile(config.q_manip)
    if config.min_manip_score is not None:
        manip_threshold = max(manip_threshold, config.min_manip_score)

    high_manip = bars[manip_col] >= manip_threshold

    # Generate signals - ASYMMETRIC
    bars['raw_signal'] = 0
    bars['extreme_trend'] = False
    bars['high_manip'] = high_manip

    # Both UP and DOWN → LONG
    signal_condition = (extreme_up | extreme_down) & high_manip
    bars.loc[signal_condition, 'raw_signal'] = 1
    bars.loc[signal_condition, 'extreme_trend'] = True

    # Shift signal to avoid look-ahead bias
    bars['exec_signal'] = bars['raw_signal'].shift(1).fillna(0).astype(int)

    # Store thresholds
    bars.attrs['trend_threshold'] = trend_thresholds
    bars.attrs['manip_threshold'] = manip_threshold
    bars.attrs['config'] = config

    return bars


def generate_4h_signals_with_filters(
    bars_4h: pd.DataFrame,
    bars_1d: Optional[pd.DataFrame],
    config: ExtremeReversalConfig,
    strategy_type: str = 'asymmetric',
    return_col: str = 'returns',
    manip_col: str = 'ManipScore'
) -> pd.DataFrame:
    """
    Generate 4h signals with optional daily and clustering filters.

    Workflow:
    1. Generate baseline 4h signals (extreme trend + high ManipScore)
    2. If use_daily_confluence: filter by daily regime
    3. If use_clustering_filter: filter by clustering
    4. Return filtered signals

    Args:
        bars_4h: 4h bars with ManipScore
        bars_1d: Daily bars with ManipScore (required if use_daily_confluence=True)
        config: ExtremeReversalConfig with filter flags
        strategy_type: 'reversal' or 'asymmetric' (default: 'asymmetric')
        return_col: Name of return column
        manip_col: Name of ManipScore column

    Returns:
        4h bars with signals and filter flags
    """
    bars_4h = bars_4h.copy()

    # Step 1: Generate baseline 4h signals
    print(f"  Generating baseline 4h {strategy_type} signals...")

    if strategy_type == 'asymmetric':
        bars_4h = generate_asymmetric_signals(
            bars_4h,
            config,
            return_col=return_col,
            manip_col=manip_col
        )
    else:
        bars_4h = generate_extreme_reversal_signals(
            bars_4h,
            config,
            return_col=return_col,
            manip_col=manip_col
        )

    n_baseline = (bars_4h['raw_signal'] != 0).sum()
    print(f"    Baseline signals: {n_baseline}")
    
    # Step 2: Apply daily confluence filter if enabled
    if config.use_daily_confluence:
        if bars_1d is None:
            raise ValueError("bars_1d required when use_daily_confluence=True")
        
        print("  Applying daily confluence filter...")
        bars_4h = apply_daily_confluence_filter(
            bars_4h,
            bars_1d,
            config
        )
        
        n_after_daily = (bars_4h['raw_signal'] != 0).sum()
        print(f"    After daily filter: {n_after_daily} ({n_after_daily/n_baseline*100:.1f}% retained)")
    
    # Step 3: Apply clustering filter if enabled
    if config.use_clustering_filter:
        print("  Applying clustering filter...")
        bars_4h = apply_clustering_filter(
            bars_4h,
            config
        )
        
        n_after_clustering = (bars_4h['raw_signal'] != 0).sum()
        print(f"    After clustering filter: {n_after_clustering} ({n_after_clustering/n_baseline*100:.1f}% retained)")
    
    # Step 4: Re-shift signal to avoid look-ahead
    bars_4h['exec_signal'] = bars_4h['raw_signal'].shift(1).fillna(0).astype(int)
    
    return bars_4h


def apply_daily_confluence_filter(
    bars_4h: pd.DataFrame,
    bars_1d: pd.DataFrame,
    config: ExtremeReversalConfig
) -> pd.DataFrame:
    """
    Filter 4h signals by daily regime confluence.
    
    Logic:
    - Only keep 4h signals when daily regime is also extreme in the SAME direction
    - For 4h SHORT (R_past > 0): require daily extreme UP
    - For 4h LONG (R_past < 0): require daily extreme DOWN
    
    Args:
        bars_4h: 4h bars with baseline signals
        bars_1d: Daily bars
        config: Config with daily filter parameters
        
    Returns:
        4h bars with filtered signals
    """
    bars_4h = bars_4h.copy()
    bars_1d = bars_1d.copy()
    
    # Compute daily trend features
    bars_1d = compute_daily_trend_features(
        bars_1d,
        L_past=config.L_past,  # Use same L_past as 4h
        vol_window=config.vol_window
    )
    
    # Define daily extreme regimes
    daily_thresholds = define_daily_extreme_regimes(
        bars_1d,
        q_extreme_trend=config.daily_q_extreme_trend,
        q_manip=config.daily_q_high_manip,
        min_abs_R_past=config.daily_min_abs_R_past
    )
    
    bars_1d = identify_daily_extreme_regimes(bars_1d, daily_thresholds)
    
    # Align 4h with daily
    bars_4h = align_4h_with_daily(bars_4h, bars_1d)
    
    # Add daily extreme flags from aligned data
    # Need to map daily extreme_up/down to 4h bars
    # Create lookup: daily_date → extreme_up/down
    daily_lookup = bars_1d[['extreme_up', 'extreme_down']].copy()
    daily_lookup['_date'] = daily_lookup.index.date
    daily_lookup = daily_lookup.set_index('_date')
    
    # Map to 4h bars
    daily_extreme_up_list = []
    daily_extreme_down_list = []
    
    for idx, row in bars_4h.iterrows():
        daily_date = row.get('daily_date')
        if daily_date is None or pd.isna(daily_date):
            daily_extreme_up_list.append(False)
            daily_extreme_down_list.append(False)
        else:
            if daily_date in daily_lookup.index:
                daily_extreme_up_list.append(daily_lookup.loc[daily_date, 'extreme_up'])
                daily_extreme_down_list.append(daily_lookup.loc[daily_date, 'extreme_down'])
            else:
                daily_extreme_up_list.append(False)
                daily_extreme_down_list.append(False)
    
    bars_4h['daily_extreme_up'] = daily_extreme_up_list
    bars_4h['daily_extreme_down'] = daily_extreme_down_list
    
    # Filter signals: only keep if daily regime matches
    # For SHORT signals (raw_signal = -1, R_past > 0): require daily_extreme_up
    # For LONG signals (raw_signal = +1, R_past < 0): require daily_extreme_down
    
    short_signals = bars_4h['raw_signal'] == -1
    long_signals = bars_4h['raw_signal'] == 1
    
    # Zero out signals that don't have daily confluence
    bars_4h.loc[short_signals & ~bars_4h['daily_extreme_up'], 'raw_signal'] = 0
    bars_4h.loc[long_signals & ~bars_4h['daily_extreme_down'], 'raw_signal'] = 0

    return bars_4h


def apply_clustering_filter(
    bars_4h: pd.DataFrame,
    config: ExtremeReversalConfig,
    manip_col: str = 'ManipScore'
) -> pd.DataFrame:
    """
    Filter 4h signals by clustering.

    Logic:
    - Only keep signals that are part of a cluster (count_high >= min_count)
    - Isolated spikes are filtered out

    Args:
        bars_4h: 4h bars with baseline signals
        config: Config with clustering parameters
        manip_col: Name of ManipScore column

    Returns:
        4h bars with filtered signals
    """
    bars_4h = bars_4h.copy()

    # Compute clustering features
    bars_4h = compute_4h_clustering_features(
        bars_4h,
        q_high_manip=config.clustering_q_high_manip,
        W=config.clustering_window_W,
        manip_col=manip_col
    )

    # Classify events
    bars_4h = classify_events(
        bars_4h,
        min_count_clustered=config.clustering_min_count,
        max_count_isolated=1
    )

    # Filter: only keep clustered events
    # Zero out signals that are not clustered
    non_clustered = ~bars_4h['is_clustered']
    bars_4h.loc[non_clustered, 'raw_signal'] = 0

    return bars_4h

