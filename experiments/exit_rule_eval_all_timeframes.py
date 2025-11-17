# -*- coding: utf-8 -*-
"""
Per-Trade Exit Rule Evaluation - ALL TIMEFRAMES

Compares different exit rules (static and semi-dynamic) across all timeframes.
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
    """Load trade path steps data"""
    path = f"results/{symbol.lower()}_{timeframe}_trade_path_steps.csv"
    
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    df = pd.read_csv(path)
    df = df.sort_values(['trade_id', 'step']).reset_index(drop=True)
    
    return df


def get_exit_rules_for_timeframe(timeframe: str) -> list:
    """
    Get appropriate exit rules for each timeframe.
    
    Shorter timeframes need tighter parameters, longer timeframes need wider parameters.
    """
    rules = []
    
    # Timeframe-specific parameters
    if timeframe in ['5min', '15min']:
        # Short timeframes: tight parameters
        max_bars_options = [10, 15, 20]
        sl_options = [2.0, 2.5, 3.0]
        tp_options = [1.5, 2.0, 3.0, np.inf]
        trail_configs = [
            (1.5, 0.8, 2.5, 20),  # (trigger, lock, sl, max_bars)
            (2.0, 1.0, 3.0, 20),
        ]
        
    elif timeframe in ['30min', '60min']:
        # Medium timeframes: moderate parameters
        max_bars_options = [15, 20, 26]
        sl_options = [2.5, 3.0, 4.0]
        tp_options = [2.0, 3.0, 5.0, np.inf]
        trail_configs = [
            (2.0, 1.0, 3.0, 26),
            (3.0, 1.5, 4.0, 26),
        ]
        
    elif timeframe == '4h':
        # 4H: wider parameters
        max_bars_options = [20, 26, 30]
        sl_options = [3.0, 4.0, 5.0]
        tp_options = [3.0, 5.0, np.inf]
        trail_configs = [
            (2.0, 1.0, 3.0, 30),
            (3.0, 1.5, 4.0, 30),
        ]
        
    else:  # 1d
        # Daily: very wide parameters
        max_bars_options = [15, 20, 26]
        sl_options = [3.0, 4.0, 5.0]
        tp_options = [5.0, np.inf]
        trail_configs = [
            (3.0, 1.5, 4.0, 26),
            (4.0, 2.0, 5.0, 26),
        ]
    
    # Static rules: best SL + best TP + best max_bars
    rules.append(ExitRuleConfig(
        name=f"Static_SL{sl_options[-1]}_NoTP_max{max_bars_options[-1]}",
        sl_atr=sl_options[-1],
        tp_atr=np.inf,
        max_bars=max_bars_options[-1]
    ))
    
    rules.append(ExitRuleConfig(
        name=f"Static_SL{sl_options[0]}_TP{tp_options[0]}_max{max_bars_options[0]}",
        sl_atr=sl_options[0],
        tp_atr=tp_options[0],
        max_bars=max_bars_options[0]
    ))
    
    rules.append(ExitRuleConfig(
        name=f"Static_SL{sl_options[1]}_TP{tp_options[1]}_max{max_bars_options[1]}",
        sl_atr=sl_options[1],
        tp_atr=tp_options[1],
        max_bars=max_bars_options[1]
    ))
    
    # Trailing rules
    for trigger, lock, sl, max_bars in trail_configs:
        rules.append(ExitRuleConfig(
            name=f"Trail_T{trigger}_L{lock}_SL{sl}",
            sl_atr=sl,
            tp_atr=np.inf,
            max_bars=max_bars,
            trail_trigger_atr=trigger,
            trail_lock_atr=lock
        ))
    
    return rules


def main():
    """Main execution"""
    print("=" * 100)
    print("PER-TRADE EXIT RULE EVALUATION - ALL TIMEFRAMES")
    print("=" * 100)
    print()
    
    # Define all combinations to test
    test_configs = []
    
    # XAUUSD
    for tf in ['4h', '1d']:
        test_configs.append(('XAUUSD', tf))
    
    # BTCUSD
    for tf in ['5min', '15min', '30min', '60min', '4h', '1d']:
        test_configs.append(('BTCUSD', tf))
    
    # ETHUSD
    for tf in ['5min', '15min', '30min', '60min', '4h', '1d']:
        test_configs.append(('ETHUSD', tf))
    
    all_rows = []
    
    for symbol, timeframe in test_configs:
        print(f"\n{'=' * 100}")
        print(f"Processing: {symbol} {timeframe}")
        print(f"{'=' * 100}\n")
        
        try:
            # Load trade path data
            trade_paths = load_trade_paths(symbol, timeframe)
            num_trades = trade_paths['trade_id'].nunique()
            print(f"  ✓ Loaded {len(trade_paths)} steps for {num_trades} trades")
            
            # Get exit rules for this timeframe
            rules = get_exit_rules_for_timeframe(timeframe)
            print(f"  ✓ Testing {len(rules)} exit rules")
            
            # Apply each exit rule
            for i, cfg in enumerate(rules, 1):
                print(f"    [{i}/{len(rules)}] {cfg.name}...", end=" ")
                
                # Simulate exits
                trades_df = apply_exit_rule_to_all_trades(trade_paths, cfg)
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
                
                print(f"PnL={stats['mean_pnl']:.4f}, WR={stats['win_rate']:.1%}")
        
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            continue
    
    # Save results
    results_df = pd.DataFrame(all_rows)
    output_path = "results/exit_rule_all_timeframes_summary.csv"
    results_df.to_csv(output_path, index=False)
    
    print(f"\n{'=' * 100}")
    print(f"✅ Results saved to: {output_path}")
    print(f"{'=' * 100}\n")
    
    # Display summary
    print("\nTOP RULE PER SYMBOL-TIMEFRAME (by mean PnL):\n")
    for symbol in ['XAUUSD', 'BTCUSD', 'ETHUSD']:
        symbol_df = results_df[results_df['symbol'] == symbol]
        if len(symbol_df) == 0:
            continue
        
        print(f"\n{symbol}:")
        print("-" * 100)
        
        for tf in symbol_df['timeframe'].unique():
            tf_df = symbol_df[symbol_df['timeframe'] == tf]
            best = tf_df.nlargest(1, 'mean_pnl').iloc[0]
            print(f"  {tf:6s}: {best['rule_name']:40s} | PnL={best['mean_pnl']:+.4f} | WR={best['win_rate']:.1%} | Trades={int(best['num_trades'])}")
    
    print("\n" + "=" * 100)
    print("EVALUATION COMPLETE!")
    print("=" * 100)


if __name__ == "__main__":
    main()

