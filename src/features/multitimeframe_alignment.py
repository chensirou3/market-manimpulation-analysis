"""
Multi-Timeframe Alignment Module

Aligns lower timeframe bars (e.g., 4h) with higher timeframe bars (e.g., daily)
to enable multi-timeframe confluence filtering.

Key principle: NO LOOK-AHEAD BIAS
- For a 4h bar ending at time t, only use daily information available at or before t.
- Conservative approach: use the PREVIOUS COMPLETED daily bar as the regime reference.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def align_4h_with_daily(
    bars_4h: pd.DataFrame,
    bars_1d: pd.DataFrame
) -> pd.DataFrame:
    """
    For each 4h bar, attach the corresponding daily regime state.
    
    ALIGNMENT LOGIC (NO LOOK-AHEAD):
    - For a 4h bar ending at time t, we use the PREVIOUS COMPLETED daily bar.
    - This ensures we only use information that would have been known at time t.
    
    Example:
    - 4h bar ending at 2024-01-02 04:00 → uses daily bar from 2024-01-01
    - 4h bar ending at 2024-01-02 20:00 → uses daily bar from 2024-01-01
    - 4h bar ending at 2024-01-03 04:00 → uses daily bar from 2024-01-02
    
    Args:
        bars_4h: 4h bars with DatetimeIndex
        bars_1d: Daily bars with DatetimeIndex
        
    Returns:
        4h bars with additional daily-level columns:
        - daily_ret: daily return
        - daily_ManipScore: daily ManipScore
        - daily_R_past: daily trend strength (if exists)
        - daily_TS: daily normalized trend strength (if exists)
        - daily_date: date of the daily bar used (for debugging)
    """
    # Ensure both have DatetimeIndex
    if not isinstance(bars_4h.index, pd.DatetimeIndex):
        raise ValueError("bars_4h must have DatetimeIndex")
    if not isinstance(bars_1d.index, pd.DatetimeIndex):
        raise ValueError("bars_1d must have DatetimeIndex")
    
    # Create a copy to avoid modifying original
    bars_4h = bars_4h.copy()
    
    # Extract date from 4h timestamps
    bars_4h['_date'] = bars_4h.index.date
    
    # Create daily lookup: date → daily bar data
    # Use the daily bar's date as key
    bars_1d_lookup = bars_1d.copy()
    bars_1d_lookup['_date'] = bars_1d_lookup.index.date
    bars_1d_lookup = bars_1d_lookup.set_index('_date')
    
    # For each 4h bar, find the PREVIOUS completed daily bar
    # Strategy: for date D, use daily bar from date D-1
    daily_ret_list = []
    daily_manip_list = []
    daily_R_past_list = []
    daily_TS_list = []
    daily_date_list = []
    
    for idx, row in bars_4h.iterrows():
        current_date = row['_date']
        
        # Find previous daily bar
        # Get all daily bars before current date
        prev_daily_bars = bars_1d_lookup[bars_1d_lookup.index < current_date]
        
        if len(prev_daily_bars) == 0:
            # No previous daily bar available
            daily_ret_list.append(np.nan)
            daily_manip_list.append(np.nan)
            daily_R_past_list.append(np.nan)
            daily_TS_list.append(np.nan)
            daily_date_list.append(None)
        else:
            # Use the most recent previous daily bar
            prev_daily = prev_daily_bars.iloc[-1]
            
            daily_ret_list.append(prev_daily.get('returns', np.nan))
            daily_manip_list.append(prev_daily.get('ManipScore', np.nan))
            daily_R_past_list.append(prev_daily.get('R_past', np.nan))
            daily_TS_list.append(prev_daily.get('TS', np.nan))
            daily_date_list.append(prev_daily.name)
    
    # Add to 4h bars
    bars_4h['daily_ret'] = daily_ret_list
    bars_4h['daily_ManipScore'] = daily_manip_list
    bars_4h['daily_R_past'] = daily_R_past_list
    bars_4h['daily_TS'] = daily_TS_list
    bars_4h['daily_date'] = daily_date_list
    
    # Drop temporary column
    bars_4h = bars_4h.drop(columns=['_date'])
    
    return bars_4h


def verify_no_lookahead(
    bars_4h_aligned: pd.DataFrame,
    sample_size: int = 10
) -> None:
    """
    Verify that alignment has no look-ahead bias.
    
    Prints sample rows showing:
    - 4h timestamp
    - daily_date (should be before 4h timestamp)
    - daily_ret, daily_ManipScore
    
    Args:
        bars_4h_aligned: Aligned 4h bars
        sample_size: Number of samples to print
    """
    print("="*80)
    print("ALIGNMENT VERIFICATION (No Look-Ahead Check)")
    print("="*80)
    print()
    print("Sample rows:")
    print(f"{'4h Timestamp':<25} {'Daily Date':<15} {'Daily Ret':<12} {'Daily ManipScore':<15}")
    print("-"*80)
    
    # Sample evenly across the dataset
    sample_indices = np.linspace(0, len(bars_4h_aligned)-1, sample_size, dtype=int)
    
    for idx in sample_indices:
        row = bars_4h_aligned.iloc[idx]
        ts_4h = row.name
        daily_date = row.get('daily_date', None)
        daily_ret = row.get('daily_ret', np.nan)
        daily_manip = row.get('daily_ManipScore', np.nan)
        
        # Check: daily_date should be before ts_4h
        if daily_date is not None:
            daily_dt = pd.Timestamp(daily_date)
            if daily_dt.date() >= ts_4h.date():
                print(f"⚠️ WARNING: Look-ahead detected at {ts_4h}")
        
        print(f"{str(ts_4h):<25} {str(daily_date):<15} {daily_ret:>10.6f}  {daily_manip:>12.4f}")
    
    print()
    print("✅ Verification complete. Check for any warnings above.")
    print("="*80)


def get_alignment_stats(bars_4h_aligned: pd.DataFrame) -> dict:
    """
    Get statistics about the alignment.
    
    Returns:
        dict with:
        - n_4h_bars: total 4h bars
        - n_aligned: number of 4h bars with daily data
        - pct_aligned: percentage aligned
        - first_aligned_date: first 4h bar with daily data
        - last_aligned_date: last 4h bar with daily data
    """
    n_4h_bars = len(bars_4h_aligned)
    n_aligned = bars_4h_aligned['daily_ManipScore'].notna().sum()
    pct_aligned = n_aligned / n_4h_bars * 100 if n_4h_bars > 0 else 0
    
    aligned_bars = bars_4h_aligned[bars_4h_aligned['daily_ManipScore'].notna()]
    first_aligned = aligned_bars.index[0] if len(aligned_bars) > 0 else None
    last_aligned = aligned_bars.index[-1] if len(aligned_bars) > 0 else None
    
    return {
        'n_4h_bars': n_4h_bars,
        'n_aligned': n_aligned,
        'pct_aligned': pct_aligned,
        'first_aligned_date': first_aligned,
        'last_aligned_date': last_aligned,
    }

