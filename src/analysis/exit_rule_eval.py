# -*- coding: utf-8 -*-
"""
Exit Rule Evaluation Module

Per-trade exit rule comparison using trade path analysis data.
Simulates different exit designs (static and semi-dynamic) on each trade independently.

NO portfolio logic, NO capital constraints - each trade is treated independently.
"""

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
import numpy as np


@dataclass
class ExitRuleConfig:
    """Configuration for an exit rule"""
    name: str
    sl_atr: float                    # static stop loss threshold in ATR units (e.g., 2.0, 3.0)
    tp_atr: float                    # static take profit threshold in ATR units; use np.inf for "no TP"
    max_bars: int                    # maximum holding bars; use large number (e.g., 999) for "no limit"
    # Optional parameters for semi-dynamic rules:
    trail_trigger_atr: float = np.inf   # when pnl_atr >= trigger, start trailing; np.inf = no trailing
    trail_lock_atr: float = 0.0         # how much profit (ATR) to lock when trailing


def simulate_exit_on_single_trade(
    trade_path: pd.DataFrame,
    cfg: ExitRuleConfig
) -> Dict:
    """
    Simulate exit logic for a single trade given its path (pnl_atr over time).
    
    Parameters:
        trade_path: DataFrame containing all rows for a single trade_id, sorted by 'step'.
                   Must have columns ['trade_id','step','direction','pnl','pnl_atr'].
        cfg: ExitRuleConfig specifying static and (optional) trailing parameters.
    
    Returns:
        Dict with:
            - 'trade_id'
            - 'direction'
            - 'holding_bars'
            - 'pnl_final'
            - 'mfe'        (max of pnl over the path)
            - 'mae'        (min of pnl over the path)
            - 'mfe_atr'    (max of pnl_atr)
            - 'mae_atr'    (min of pnl_atr)
            - 'capture_ratio' = pnl_final / max(mfe, small_eps)
            - 'exit_reason' in {'SL','TP','TRAIL','TIME_MAX','RAW_END'}
    
    Exit logic:
        - Initialize: current_sl_atr = -cfg.sl_atr (negative)
        - For each step t:
            1. Check if pnl_atr >= trail_trigger_atr → activate trailing
            2. If trailing active, update SL: current_sl_atr = max(current_sl_atr, pnl_atr - trail_lock_atr)
            3. Check exits (priority order):
               a) SL: if pnl_atr <= current_sl_atr → exit (reason: 'TRAIL' if trailing else 'SL')
               b) TP: if pnl_atr >= tp_atr → exit (reason: 'TP')
               c) TIME_MAX: if step >= max_bars → exit (reason: 'TIME_MAX')
            4. If no exit, continue to next step
        - If reach end without exit → exit_reason = 'RAW_END'
    """
    # Ensure sorted by step
    trade_path = trade_path.sort_values('step').reset_index(drop=True)
    
    trade_id = trade_path['trade_id'].iloc[0]
    direction = trade_path['direction'].iloc[0]
    
    # Compute path-based metrics
    mfe = trade_path['pnl'].max()
    mae = trade_path['pnl'].min()
    mfe_atr = trade_path['pnl_atr'].max()
    mae_atr = trade_path['pnl_atr'].min()
    
    # Initialize exit logic
    current_sl_atr = -cfg.sl_atr  # Negative (e.g., -2.0 means stop at -2 ATR)
    tp_atr = cfg.tp_atr
    trailing_active = False
    
    exit_triggered = False
    exit_reason = None
    pnl_final = None
    holding_bars = None
    
    # Loop through each step
    for idx, row in trade_path.iterrows():
        step = row['step']
        pnl_atr_t = row['pnl_atr']
        pnl_t = row['pnl']
        
        # Check if we should activate trailing
        if not trailing_active and pnl_atr_t >= cfg.trail_trigger_atr:
            trailing_active = True
            # Lock in profit: set SL to current profit minus lock amount
            current_sl_atr = pnl_atr_t - cfg.trail_lock_atr
        
        # If trailing is active, tighten SL as profit increases
        if trailing_active:
            current_sl_atr = max(current_sl_atr, pnl_atr_t - cfg.trail_lock_atr)
        
        # Check exit conditions (priority order)
        # Priority 1: Stop Loss (or Trailing Stop)
        if pnl_atr_t <= current_sl_atr:
            exit_reason = 'TRAIL' if trailing_active else 'SL'
            pnl_final = pnl_t
            holding_bars = step
            exit_triggered = True
            break
        
        # Priority 2: Take Profit
        if pnl_atr_t >= tp_atr:
            exit_reason = 'TP'
            pnl_final = pnl_t
            holding_bars = step
            exit_triggered = True
            break
        
        # Priority 3: Max Holding Time
        if step >= cfg.max_bars:
            exit_reason = 'TIME_MAX'
            pnl_final = pnl_t
            holding_bars = step
            exit_triggered = True
            break
    
    # If no exit triggered, use final step
    if not exit_triggered:
        exit_reason = 'RAW_END'
        pnl_final = trade_path['pnl'].iloc[-1]
        holding_bars = trade_path['step'].iloc[-1]
    
    # Compute capture ratio
    eps = 1e-8
    capture_ratio = pnl_final / max(mfe, eps) if mfe > 0 else 0.0
    
    return {
        'trade_id': trade_id,
        'direction': direction,
        'holding_bars': holding_bars,
        'pnl_final': pnl_final,
        'mfe': mfe,
        'mae': mae,
        'mfe_atr': mfe_atr,
        'mae_atr': mae_atr,
        'capture_ratio': capture_ratio,
        'exit_reason': exit_reason
    }


def apply_exit_rule_to_all_trades(
    trade_paths: pd.DataFrame,
    cfg: ExitRuleConfig
) -> pd.DataFrame:
    """
    Apply an exit rule to all trades in the dataset.

    Parameters:
        trade_paths: DataFrame with path data for many trades.
                    Must have columns: ['trade_id','step','pnl','pnl_atr','direction']
        cfg: ExitRuleConfig

    Returns:
        DataFrame with one row per trade, containing exit simulation results.
    """
    results = []

    # Group by trade_id and process each trade
    for trade_id, group in trade_paths.groupby('trade_id'):
        result = simulate_exit_on_single_trade(group, cfg)
        results.append(result)

    return pd.DataFrame(results)


def summarize_exit_rule_results(trades_df: pd.DataFrame) -> Dict:
    """
    Compute summary statistics for a given exit rule.

    Parameters:
        trades_df: DataFrame with one row per trade (output of apply_exit_rule_to_all_trades)

    Returns:
        Dict with summary statistics:
            - num_trades
            - win_rate
            - mean_pnl, median_pnl, std_pnl
            - mean_mfe, mean_mae
            - mean_capture_ratio, median_capture_ratio
            - frac_cap_gt_0_3, frac_cap_gt_0_5, frac_cap_gt_0_7
            - mean_holding_bars, median_holding_bars
            - exit_reason_counts (dict)
            - tail_loss_rate (fraction with pnl_final < -2 ATR using mae_atr as proxy)
    """
    num_trades = len(trades_df)

    if num_trades == 0:
        return {
            'num_trades': 0,
            'win_rate': 0.0,
            'mean_pnl': 0.0,
            'median_pnl': 0.0,
            'std_pnl': 0.0,
            'mean_mfe': 0.0,
            'mean_mae': 0.0,
            'mean_capture_ratio': 0.0,
            'median_capture_ratio': 0.0,
            'frac_cap_gt_0_3': 0.0,
            'frac_cap_gt_0_5': 0.0,
            'frac_cap_gt_0_7': 0.0,
            'mean_holding_bars': 0.0,
            'median_holding_bars': 0.0,
            'tail_loss_rate': 0.0,
        }

    # Basic PnL statistics
    win_rate = (trades_df['pnl_final'] > 0).mean()
    mean_pnl = trades_df['pnl_final'].mean()
    median_pnl = trades_df['pnl_final'].median()
    std_pnl = trades_df['pnl_final'].std()

    # MFE/MAE statistics
    mean_mfe = trades_df['mfe'].mean()
    mean_mae = trades_df['mae'].mean()

    # Capture ratio statistics
    mean_capture_ratio = trades_df['capture_ratio'].mean()
    median_capture_ratio = trades_df['capture_ratio'].median()
    frac_cap_gt_0_3 = (trades_df['capture_ratio'] > 0.3).mean()
    frac_cap_gt_0_5 = (trades_df['capture_ratio'] > 0.5).mean()
    frac_cap_gt_0_7 = (trades_df['capture_ratio'] > 0.7).mean()

    # Holding time statistics
    mean_holding_bars = trades_df['holding_bars'].mean()
    median_holding_bars = trades_df['holding_bars'].median()

    # Exit reason breakdown
    exit_reason_counts = trades_df['exit_reason'].value_counts().to_dict()

    # Tail loss rate (using mae_atr as proxy for extreme losses)
    # Approximate: trades where final PnL is very negative
    # Use mae_atr < -2.0 as proxy for tail losses
    tail_loss_rate = (trades_df['mae_atr'] < -2.0).mean()

    return {
        'num_trades': num_trades,
        'win_rate': win_rate,
        'mean_pnl': mean_pnl,
        'median_pnl': median_pnl,
        'std_pnl': std_pnl,
        'mean_mfe': mean_mfe,
        'mean_mae': mean_mae,
        'mean_capture_ratio': mean_capture_ratio,
        'median_capture_ratio': median_capture_ratio,
        'frac_cap_gt_0_3': frac_cap_gt_0_3,
        'frac_cap_gt_0_5': frac_cap_gt_0_5,
        'frac_cap_gt_0_7': frac_cap_gt_0_7,
        'mean_holding_bars': mean_holding_bars,
        'median_holding_bars': median_holding_bars,
        'tail_loss_rate': tail_loss_rate,
        # Exit reason counts as separate fields
        'exit_SL': exit_reason_counts.get('SL', 0),
        'exit_TP': exit_reason_counts.get('TP', 0),
        'exit_TRAIL': exit_reason_counts.get('TRAIL', 0),
        'exit_TIME_MAX': exit_reason_counts.get('TIME_MAX', 0),
        'exit_RAW_END': exit_reason_counts.get('RAW_END', 0),
    }

