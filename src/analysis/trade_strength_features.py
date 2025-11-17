# -*- coding: utf-8 -*-
"""
Trade Strength Features Module

Compute signal strength labels (strong/medium/weak) for each trade based on
entry-time features (TS and ManipScore).

This is Layer 3 of the exit design: connecting entry strength to exit behavior.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def compute_trade_entry_features(
    trade_paths: pd.DataFrame,
    bars_4h: pd.DataFrame
) -> pd.DataFrame:
    """
    For each trade_id in trade_paths, find the entry bar and attach entry-time features.
    
    Parameters:
        trade_paths: DataFrame with per-step data
                    Columns: ['trade_id','step','direction','pnl','pnl_atr','timestamp',...]
        bars_4h: DataFrame indexed by timestamp, with columns ['TS','ManipScore',...]
    
    Returns:
        DataFrame with one row per trade_id:
            ['trade_id','entry_time','entry_TS','entry_ManipScore']
    
    Assumptions:
        - For each trade_id, the first row (step == 1) corresponds to the first bar after entry.
        - The entry bar is the bar BEFORE step 1, so we use the timestamp from step 1 and look back.
        - Alternatively, if step == 0 exists, that's the entry bar.
        
    Convention used here:
        - We take the timestamp from step == 1 (first step in the trade).
        - Entry time is this timestamp (the bar where we entered).
        - We join with bars_4h to get TS and ManipScore at entry.
    """
    # Get first step for each trade (entry point)
    entry_rows = trade_paths[trade_paths['step'] == 1].copy()
    
    if len(entry_rows) == 0:
        # Try step == 0 if step 1 doesn't exist
        entry_rows = trade_paths.groupby('trade_id').first().reset_index()
    
    # Extract entry time
    entry_rows = entry_rows[['trade_id', 'timestamp']].rename(columns={'timestamp': 'entry_time'})
    
    # Ensure bars_4h has timestamp as index
    if 'timestamp' in bars_4h.columns:
        bars_4h = bars_4h.set_index('timestamp')
    
    # Join with bars to get TS and ManipScore at entry
    # We need to handle potential missing timestamps
    entry_features = []
    
    for _, row in entry_rows.iterrows():
        trade_id = row['trade_id']
        entry_time = row['entry_time']
        
        # Find the bar at entry_time
        if entry_time in bars_4h.index:
            bar = bars_4h.loc[entry_time]
            entry_ts = bar.get('TS', np.nan)
            entry_manipscore = bar.get('ManipScore', np.nan)
        else:
            # If exact match not found, use nearest previous bar
            valid_times = bars_4h.index[bars_4h.index <= entry_time]
            if len(valid_times) > 0:
                nearest_time = valid_times[-1]
                bar = bars_4h.loc[nearest_time]
                entry_ts = bar.get('TS', np.nan)
                entry_manipscore = bar.get('ManipScore', np.nan)
            else:
                entry_ts = np.nan
                entry_manipscore = np.nan
        
        entry_features.append({
            'trade_id': trade_id,
            'entry_time': entry_time,
            'entry_TS': entry_ts,
            'entry_ManipScore': entry_manipscore
        })
    
    return pd.DataFrame(entry_features)


def label_signal_strength(
    trade_entry_df: pd.DataFrame,
    ts_quantiles: Tuple[float, float] = (0.30, 0.70),
    ms_quantiles: Tuple[float, float] = (0.30, 0.70)
) -> pd.DataFrame:
    """
    Label each trade as 'strong', 'medium', or 'weak' based on entry TS and ManipScore.
    
    Parameters:
        trade_entry_df: DataFrame with ['trade_id','entry_TS','entry_ManipScore']
        ts_quantiles: (lower, upper) quantiles for |TS| (default: 30%, 70%)
        ms_quantiles: (lower, upper) quantiles for ManipScore (default: 30%, 70%)
    
    Returns:
        Same DataFrame with additional column 'signal_strength' in {'strong','medium','weak'}
    
    Logic:
        - Compute quantiles of |entry_TS| and entry_ManipScore
        - strong: |entry_TS| >= q_TS_70 AND entry_ManipScore >= q_MS_70
        - weak: |entry_TS| <= q_TS_30 AND entry_ManipScore <= q_MS_30
        - medium: otherwise
    """
    df = trade_entry_df.copy()
    
    # Remove NaN values for quantile calculation
    valid_mask = df['entry_TS'].notna() & df['entry_ManipScore'].notna()
    
    if valid_mask.sum() == 0:
        # No valid data, label all as medium
        df['signal_strength'] = 'medium'
        return df
    
    # Compute absolute TS
    df['abs_entry_TS'] = df['entry_TS'].abs()
    
    # Compute quantiles on valid data only
    valid_data = df[valid_mask]
    
    q_ts_low, q_ts_high = ts_quantiles
    q_ms_low, q_ms_high = ms_quantiles
    
    ts_q30 = valid_data['abs_entry_TS'].quantile(q_ts_low)
    ts_q70 = valid_data['abs_entry_TS'].quantile(q_ts_high)
    ms_q30 = valid_data['entry_ManipScore'].quantile(q_ms_low)
    ms_q70 = valid_data['entry_ManipScore'].quantile(q_ms_high)
    
    # Label signal strength
    def classify_strength(row):
        if pd.isna(row['entry_TS']) or pd.isna(row['entry_ManipScore']):
            return 'medium'  # Default for missing data
        
        abs_ts = abs(row['entry_TS'])
        ms = row['entry_ManipScore']
        
        # Strong: both high
        if abs_ts >= ts_q70 and ms >= ms_q70:
            return 'strong'
        # Weak: both low
        elif abs_ts <= ts_q30 and ms <= ms_q30:
            return 'weak'
        # Medium: everything else
        else:
            return 'medium'
    
    df['signal_strength'] = df.apply(classify_strength, axis=1)
    
    # Drop temporary column
    df = df.drop(columns=['abs_entry_TS'])
    
    return df


def attach_strength_to_trade_paths(
    trade_paths: pd.DataFrame,
    trade_entry_features: pd.DataFrame
) -> pd.DataFrame:
    """
    Attach signal_strength to each row in trade_paths by merging on trade_id.
    
    Parameters:
        trade_paths: DataFrame with per-step data
        trade_entry_features: DataFrame with ['trade_id','signal_strength',...]
    
    Returns:
        trade_paths with additional 'signal_strength' column
    """
    # Merge on trade_id
    strength_map = trade_entry_features[['trade_id', 'signal_strength']].drop_duplicates()
    
    result = trade_paths.merge(strength_map, on='trade_id', how='left')
    
    # Fill missing with 'medium' as default
    result['signal_strength'] = result['signal_strength'].fillna('medium')
    
    return result

