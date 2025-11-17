# -*- coding: utf-8 -*-
"""
Dynamic Exit Rules Module

Define per-strength exit rule mappings for Layer 3 dynamic exit system.

Strong signals get wider SL / later trailing / looser exits.
Weak signals get tighter SL / TP / shorter holding.
"""

import numpy as np
from typing import Dict
from src.analysis.exit_rule_eval import ExitRuleConfig
from src.backtest.exit_rules_portfolio import PortfolioExitRule


# ============================================================================
# BTC 4H: Per-Strength Exit Rules
# ============================================================================

BTC_4H_RULES_BY_STRENGTH = {
    "strong": ExitRuleConfig(
        name="BTC4H_STRONG_Trail_T3_L1.5_SL4",
        sl_atr=4.0,         # Wide SL for strong signals
        tp_atr=np.inf,      # No fixed TP - let it run
        max_bars=30,        # Longer holding period
        trail_trigger_atr=3.0,  # Start trailing at +3 ATR
        trail_lock_atr=1.5      # Lock 1.5 ATR profit
    ),
    "medium": ExitRuleConfig(
        name="BTC4H_MEDIUM_Trail_T2_L1_SL3",
        sl_atr=3.0,         # Medium SL
        tp_atr=np.inf,      # No fixed TP
        max_bars=20,        # Medium holding period
        trail_trigger_atr=2.0,  # Start trailing at +2 ATR
        trail_lock_atr=1.0      # Lock 1.0 ATR profit
    ),
    "weak": ExitRuleConfig(
        name="BTC4H_WEAK_Static_SL2_TP1.5_max15",
        sl_atr=2.0,         # Tight SL for weak signals
        tp_atr=1.5,         # Take profit early at +1.5 ATR
        max_bars=15,        # Short holding period
        trail_trigger_atr=np.inf,  # No trailing
        trail_lock_atr=0.0
    )
}


# Portfolio versions (same parameters, different class)
BTC_4H_PORTFOLIO_RULES_BY_STRENGTH = {
    "strong": PortfolioExitRule(
        name="BTC4H_STRONG_Trail_T3_L1.5_SL4",
        bar_size="4h",
        sl_atr_mult=4.0,
        tp_atr_mult=np.inf,
        max_holding_bars=30,
        trail_trigger_atr=3.0,
        trail_lock_atr=1.5
    ),
    "medium": PortfolioExitRule(
        name="BTC4H_MEDIUM_Trail_T2_L1_SL3",
        bar_size="4h",
        sl_atr_mult=3.0,
        tp_atr_mult=np.inf,
        max_holding_bars=20,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0
    ),
    "weak": PortfolioExitRule(
        name="BTC4H_WEAK_Static_SL2_TP1.5_max15",
        bar_size="4h",
        sl_atr_mult=2.0,
        tp_atr_mult=1.5,
        max_holding_bars=15,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    )
}


# ============================================================================
# XAU 4H: Per-Strength Exit Rules
# ============================================================================
# XAU showed less benefit from dynamic trailing in previous tests,
# so we use simpler static rules with varying tightness

XAU_4H_RULES_BY_STRENGTH = {
    "strong": ExitRuleConfig(
        name="XAU4H_STRONG_Static_SL5_NoTP_max30",
        sl_atr=5.0,         # Wide SL for strong signals
        tp_atr=np.inf,      # No TP - let it run
        max_bars=30,        # Longer holding
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    ),
    "medium": ExitRuleConfig(
        name="XAU4H_MEDIUM_Static_SL4_TP3_max20",
        sl_atr=4.0,         # Medium SL
        tp_atr=3.0,         # Take profit at +3 ATR
        max_bars=20,        # Medium holding
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    ),
    "weak": ExitRuleConfig(
        name="XAU4H_WEAK_Static_SL2_TP1.5_max15",
        sl_atr=2.0,         # Tight SL
        tp_atr=1.5,         # Take profit early at +1.5 ATR
        max_bars=15,        # Short holding
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    )
}


# Portfolio versions
XAU_4H_PORTFOLIO_RULES_BY_STRENGTH = {
    "strong": PortfolioExitRule(
        name="XAU4H_STRONG_Static_SL5_NoTP_max30",
        bar_size="4h",
        sl_atr_mult=5.0,
        tp_atr_mult=np.inf,
        max_holding_bars=30,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    ),
    "medium": PortfolioExitRule(
        name="XAU4H_MEDIUM_Static_SL4_TP3_max20",
        bar_size="4h",
        sl_atr_mult=4.0,
        tp_atr_mult=3.0,
        max_holding_bars=20,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    ),
    "weak": PortfolioExitRule(
        name="XAU4H_WEAK_Static_SL2_TP1.5_max15",
        bar_size="4h",
        sl_atr_mult=2.0,
        tp_atr_mult=1.5,
        max_holding_bars=15,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    )
}


# ============================================================================
# ETH 4H: Per-Strength Exit Rules
# ============================================================================
# ETH is similar to BTC, use same dynamic trailing approach

ETH_4H_RULES_BY_STRENGTH = {
    "strong": ExitRuleConfig(
        name="ETH4H_STRONG_Trail_T3_L1.5_SL4",
        sl_atr=4.0,
        tp_atr=np.inf,
        max_bars=30,
        trail_trigger_atr=3.0,
        trail_lock_atr=1.5
    ),
    "medium": ExitRuleConfig(
        name="ETH4H_MEDIUM_Trail_T2_L1_SL3",
        sl_atr=3.0,
        tp_atr=np.inf,
        max_bars=20,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0
    ),
    "weak": ExitRuleConfig(
        name="ETH4H_WEAK_Static_SL2_TP1.5_max15",
        sl_atr=2.0,
        tp_atr=1.5,
        max_bars=15,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    )
}


# Portfolio versions
ETH_4H_PORTFOLIO_RULES_BY_STRENGTH = {
    "strong": PortfolioExitRule(
        name="ETH4H_STRONG_Trail_T3_L1.5_SL4",
        bar_size="4h",
        sl_atr_mult=4.0,
        tp_atr_mult=np.inf,
        max_holding_bars=30,
        trail_trigger_atr=3.0,
        trail_lock_atr=1.5
    ),
    "medium": PortfolioExitRule(
        name="ETH4H_MEDIUM_Trail_T2_L1_SL3",
        bar_size="4h",
        sl_atr_mult=3.0,
        tp_atr_mult=np.inf,
        max_holding_bars=20,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0
    ),
    "weak": PortfolioExitRule(
        name="ETH4H_WEAK_Static_SL2_TP1.5_max15",
        bar_size="4h",
        sl_atr_mult=2.0,
        tp_atr_mult=1.5,
        max_holding_bars=15,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0
    )
}


# ============================================================================
# Selector Functions
# ============================================================================

def get_exit_rule_for_trade(
    symbol: str,
    signal_strength: str
) -> ExitRuleConfig:
    """
    Get ExitRuleConfig for a trade based on symbol and signal strength.

    Used for per-trade path analysis.

    Parameters:
        symbol: "BTCUSD", "ETHUSD", or "XAUUSD"
        signal_strength: "strong", "medium", or "weak"

    Returns:
        ExitRuleConfig instance
    """
    if symbol == "BTCUSD":
        return BTC_4H_RULES_BY_STRENGTH[signal_strength]
    elif symbol == "ETHUSD":
        return ETH_4H_RULES_BY_STRENGTH[signal_strength]
    elif symbol == "XAUUSD":
        return XAU_4H_RULES_BY_STRENGTH[signal_strength]
    else:
        raise ValueError(f"Unsupported symbol: {symbol}")


def get_portfolio_exit_rule_for_strength(
    symbol: str,
    signal_strength: str
) -> PortfolioExitRule:
    """
    Get PortfolioExitRule for a trade based on symbol and signal strength.

    Used for portfolio-level backtest.

    Parameters:
        symbol: "BTCUSD", "ETHUSD", or "XAUUSD"
        signal_strength: "strong", "medium", or "weak"

    Returns:
        PortfolioExitRule instance
    """
    if symbol == "BTCUSD":
        return BTC_4H_PORTFOLIO_RULES_BY_STRENGTH[signal_strength]
    elif symbol == "ETHUSD":
        return ETH_4H_PORTFOLIO_RULES_BY_STRENGTH[signal_strength]
    elif symbol == "XAUUSD":
        return XAU_4H_PORTFOLIO_RULES_BY_STRENGTH[signal_strength]
    else:
        raise ValueError(f"Unsupported symbol: {symbol}")

