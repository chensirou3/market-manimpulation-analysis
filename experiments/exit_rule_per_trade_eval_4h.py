# -*- coding: utf-8 -*-
"""
Per-Trade Exit Rule Evaluation - 4H Timeframe

Compares different exit rules (static and semi-dynamic) on XAUUSD and BTCUSD 4H data.
Uses existing trade path analysis data to simulate alternative exits.

NO portfolio logic, NO capital constraints - pure per-trade analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from src.analysis.exit_rule_eval import (
    ExitRuleConfig,
    apply_exit_rule_to_all_trades,
    summarize_exit_rule_results
)


def load_trade_paths(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Load trade path analysis data for a given symbol and timeframe.
    
    Expected file: results/{symbol}_{timeframe}_trade_path_analysis.csv
    
    Returns:
        DataFrame with columns: trade_id, step, direction, pnl, pnl_atr, etc.
    """
    # Try different possible file names
    possible_paths = [
        f"results/{symbol.lower()}_{timeframe}_trade_path_steps.csv",
        f"results/{symbol.upper()}_{timeframe}_trade_path_steps.csv",
        f"results/{symbol.lower()}_{timeframe}_trade_path_analysis.csv",
        f"results/{symbol.upper()}_{timeframe}_trade_path_analysis.csv",
        f"results/{symbol}_{timeframe}_trade_path.csv",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            print(f"Loading: {path}")
            df = pd.read_csv(path)
            
            # Ensure required columns exist
            required_cols = ['trade_id', 'step', 'direction', 'pnl', 'pnl_atr']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
            
            # Sort by trade_id and step
            df = df.sort_values(['trade_id', 'step']).reset_index(drop=True)
            
            print(f"  Loaded {len(df)} rows, {df['trade_id'].nunique()} unique trades")
            return df
    
    raise FileNotFoundError(f"Could not find trade path file for {symbol} {timeframe}")


# Define exit rule configurations to test
def get_exit_rules() -> list:
    """
    Define a list of exit rule configurations to evaluate.
    
    Includes:
        - Static SL/TP rules
        - Semi-dynamic trailing stop rules
    """
    rules = []
    
    # ===== STATIC RULES =====
    
    # Conservative: tight SL, moderate TP
    rules.append(ExitRuleConfig(
        name="Static_SL2_TP1.5_max20",
        sl_atr=2.0,
        tp_atr=1.5,
        max_bars=20
    ))
    
    rules.append(ExitRuleConfig(
        name="Static_SL2_TP2_max20",
        sl_atr=2.0,
        tp_atr=2.0,
        max_bars=20
    ))
    
    # Moderate: wider SL, wider TP
    rules.append(ExitRuleConfig(
        name="Static_SL3_TP2_max26",
        sl_atr=3.0,
        tp_atr=2.0,
        max_bars=26
    ))
    
    rules.append(ExitRuleConfig(
        name="Static_SL3_TP3_max26",
        sl_atr=3.0,
        tp_atr=3.0,
        max_bars=26
    ))
    
    # Wide SL, no TP (let it run)
    rules.append(ExitRuleConfig(
        name="Static_SL5_NoTP_max30",
        sl_atr=5.0,
        tp_atr=np.inf,
        max_bars=30
    ))
    
    # ===== SEMI-DYNAMIC TRAILING RULES =====
    
    # Trail after reaching 2 ATR profit, lock in 1 ATR
    rules.append(ExitRuleConfig(
        name="Trail_trigger2_lock1_SL3",
        sl_atr=3.0,
        tp_atr=np.inf,
        max_bars=30,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0
    ))
    
    # Trail after reaching 1.5 ATR profit, lock in 0.8 ATR
    rules.append(ExitRuleConfig(
        name="Trail_trigger1.5_lock0.8_SL2.5",
        sl_atr=2.5,
        tp_atr=np.inf,
        max_bars=26,
        trail_trigger_atr=1.5,
        trail_lock_atr=0.8
    ))
    
    # Aggressive trailing: trigger at 1 ATR, lock 0.5 ATR
    rules.append(ExitRuleConfig(
        name="Trail_trigger1_lock0.5_SL2",
        sl_atr=2.0,
        tp_atr=np.inf,
        max_bars=26,
        trail_trigger_atr=1.0,
        trail_lock_atr=0.5
    ))
    
    # Conservative trailing: trigger at 3 ATR, lock 1.5 ATR
    rules.append(ExitRuleConfig(
        name="Trail_trigger3_lock1.5_SL4",
        sl_atr=4.0,
        tp_atr=np.inf,
        max_bars=30,
        trail_trigger_atr=3.0,
        trail_lock_atr=1.5
    ))
    
    # Hybrid: moderate TP + trailing
    rules.append(ExitRuleConfig(
        name="Hybrid_TP4_Trail2_lock1",
        sl_atr=3.0,
        tp_atr=4.0,  # Take profit at 4 ATR
        max_bars=30,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0
    ))
    
    return rules


def main():
    """
    Main execution: evaluate all exit rules on XAUUSD and BTCUSD 4H data.
    """
    print("=" * 80)
    print("PER-TRADE EXIT RULE EVALUATION - 4H TIMEFRAME")
    print("=" * 80)
    print()
    
    # Focus on these two assets first
    symbols = ["XAUUSD", "BTCUSD"]
    timeframe = "4h"
    
    # Get all exit rules to test
    rules = get_exit_rules()
    print(f"Testing {len(rules)} exit rule configurations:")
    for rule in rules:
        print(f"  - {rule.name}")
    print()
    
    all_rows = []
    
    for symbol in symbols:
        print(f"\n{'=' * 80}")
        print(f"Processing: {symbol} {timeframe}")
        print(f"{'=' * 80}\n")
        
        try:
            # Load trade path data
            trade_paths = load_trade_paths(symbol, timeframe)
            
            # Apply each exit rule
            for i, cfg in enumerate(rules, 1):
                print(f"  [{i}/{len(rules)}] Evaluating: {cfg.name}...", end=" ")
                
                # Simulate exits for all trades
                trades_df = apply_exit_rule_to_all_trades(trade_paths, cfg)
                
                # Compute summary statistics
                stats = summarize_exit_rule_results(trades_df)
                
                # Build result row
                stats_row = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "rule_name": cfg.name,
                    "sl_atr": cfg.sl_atr,
                    "tp_atr": cfg.tp_atr if cfg.tp_atr != np.inf else 999.0,
                    "max_bars": cfg.max_bars,
                    "trail_trigger_atr": cfg.trail_trigger_atr if cfg.trail_trigger_atr != np.inf else 999.0,
                    "trail_lock_atr": cfg.trail_lock_atr,
                }
                stats_row.update(stats)
                all_rows.append(stats_row)
                
                print(f"Done. (mean_pnl={stats['mean_pnl']:.4f}, cap_ratio={stats['mean_capture_ratio']:.2%})")
        
        except Exception as e:
            print(f"ERROR processing {symbol}: {e}")
            continue
    
    # Save results
    results_df = pd.DataFrame(all_rows)
    output_path = "results/exit_rule_per_trade_4h_summary.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\n{'=' * 80}")
    print(f"Results saved to: {output_path}")
    print(f"{'=' * 80}\n")
    
    # Display top results by mean_pnl for each symbol
    print("\nTOP 5 RULES BY MEAN PNL (per symbol):\n")
    for symbol in symbols:
        symbol_df = results_df[results_df['symbol'] == symbol].copy()
        if len(symbol_df) == 0:
            continue
        
        top5 = symbol_df.nlargest(5, 'mean_pnl')
        print(f"\n{symbol}:")
        print(top5[['rule_name', 'mean_pnl', 'mean_capture_ratio', 'win_rate', 'num_trades']].to_string(index=False))
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()

