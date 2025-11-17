"""
Portfolio-level exit rule configurations for backtesting.

This module defines exit rule configurations that can be plugged into
the portfolio backtest engine to compare different exit strategies.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class PortfolioExitRule:
    """
    Configuration for portfolio-level exit rules.
    
    Supports both static SL/TP and dynamic trailing stop logic.
    
    Attributes:
        name: Descriptive name for the rule
        bar_size: Timeframe (e.g., "4h", "1d")
        sl_atr_mult: Stop-loss in ATR units (np.inf = no SL)
        tp_atr_mult: Take-profit in ATR units (np.inf = no TP)
        max_holding_bars: Maximum bars to hold (999 = effectively no limit)
        trail_trigger_atr: PnL threshold in ATR to activate trailing (np.inf = no trailing)
        trail_lock_atr: Profit to lock when trailing active (e.g., 1.5 ATR)
    
    Exit Logic:
        1. Static SL: exit if pnl_atr <= -sl_atr_mult
        2. Trailing SL (if activated): exit if pnl_atr <= (peak_pnl_atr - trail_lock_atr)
        3. Static TP: exit if pnl_atr >= tp_atr_mult
        4. Time limit: exit if holding_bars >= max_holding_bars
    
    Examples:
        # Pure baseline: wide SL, no TP, no time limit
        PortfolioExitRule(
            name="Pure_SL5_NoTP",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999
        )
        
        # Static with time limit
        PortfolioExitRule(
            name="Static_SL5_NoTP_max30",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=30
        )
        
        # Dynamic trailing
        PortfolioExitRule(
            name="Trail_T3_L1.5_SL4",
            sl_atr_mult=4.0,
            tp_atr_mult=np.inf,
            max_holding_bars=30,
            trail_trigger_atr=3.0,  # activate when pnl >= 3 ATR
            trail_lock_atr=1.5       # lock 1.5 ATR profit
        )
    """
    name: str
    bar_size: str = "4h"
    
    # Static SL/TP
    sl_atr_mult: float = np.inf
    tp_atr_mult: float = np.inf
    max_holding_bars: int = 999
    
    # Trailing parameters
    trail_trigger_atr: float = np.inf
    trail_lock_atr: float = 0.0


# ===== Predefined Exit Rules =====

# 1. Pure factor baseline: wide SL, no TP, no time limit
PURE_BASELINE = PortfolioExitRule(
    name="Pure_SL5_NoTP_noMaxBars",
    bar_size="4h",
    sl_atr_mult=5.0,
    tp_atr_mult=np.inf,
    max_holding_bars=999,
    trail_trigger_atr=np.inf,
    trail_lock_atr=0.0,
)

# 2. Static baseline: SL=5 ATR, no TP, max 30 bars
STATIC_SL5_NOTP_30 = PortfolioExitRule(
    name="Static_SL5_NoTP_max30",
    bar_size="4h",
    sl_atr_mult=5.0,
    tp_atr_mult=np.inf,
    max_holding_bars=30,
    trail_trigger_atr=np.inf,
    trail_lock_atr=0.0,
)

# 3. Dynamic trailing: trigger at 3 ATR, lock 1.5 ATR, base SL=4 ATR
TRAIL_T3_L1p5_SL4 = PortfolioExitRule(
    name="Trail_T3_L1.5_SL4",
    bar_size="4h",
    sl_atr_mult=4.0,
    tp_atr_mult=np.inf,
    max_holding_bars=30,
    trail_trigger_atr=3.0,
    trail_lock_atr=1.5,
)

# 4. Alternative: tighter trailing for comparison
TRAIL_T2_L1_SL3 = PortfolioExitRule(
    name="Trail_T2_L1.0_SL3",
    bar_size="4h",
    sl_atr_mult=3.0,
    tp_atr_mult=np.inf,
    max_holding_bars=30,
    trail_trigger_atr=2.0,
    trail_lock_atr=1.0,
)

# 5. Static with moderate TP for comparison
STATIC_SL4_TP5_30 = PortfolioExitRule(
    name="Static_SL4_TP5_max30",
    bar_size="4h",
    sl_atr_mult=4.0,
    tp_atr_mult=5.0,
    max_holding_bars=30,
    trail_trigger_atr=np.inf,
    trail_lock_atr=0.0,
)


def get_bars_per_year(bar_size: str) -> float:
    """
    Get number of bars per year for annualization.
    
    Args:
        bar_size: Timeframe string (e.g., "5min", "15min", "4h", "1d")
    
    Returns:
        Number of bars per year
    """
    bars_per_day = {
        "1min": 1440,
        "5min": 288,
        "15min": 96,
        "30min": 48,
        "60min": 24,
        "1h": 24,
        "4h": 6,
        "1d": 1,
    }
    
    if bar_size not in bars_per_day:
        raise ValueError(f"Unknown bar_size: {bar_size}. Supported: {list(bars_per_day.keys())}")
    
    # Assume 365 days per year
    return bars_per_day[bar_size] * 365

