"""
BTCUSD 4H Trend Filter Comparison Experiment

Tests whether adding a simple MA200 trend filter can:
1. Reduce catastrophic drawdowns in bear markets (2018, 2022)
2. Improve Sharpe ratio and risk-adjusted returns
3. Maintain most of the upside in bull markets

Compares:
- Baseline: no trend filter
- Trend-filtered: only enter when price > MA200

Author: Market Manipulation Analysis Project
Date: 2025-01-17
Phase: 24 - Trend Filter Testing
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.extreme_reversal_4h_enhanced import generate_asymmetric_signals
from src.analysis.trend_filter import (
    compute_trend_filter_ma,
    apply_trend_filter,
    compute_trend_filter_stats
)
from src.backtest.portfolio_backtest import run_portfolio_backtest_with_exit_rule
from src.backtest.exit_rules_portfolio import PortfolioExitRule
from src.strategies.backtest_reversal import compute_atr


def load_btc_4h_bars(start_date: str = "2017-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """Load BTCUSD 4H bars with ManipScore"""
    
    # Try multiple possible file paths
    possible_paths = [
        project_root / "results/bars_4h_btc_full_with_manipscore.csv",
        project_root / "results/BTCUSD_4h_bars_with_manipscore_full.csv",
        project_root / "results/bars_4h_with_manipscore_full.csv",
    ]
    
    bars = None
    for path in possible_paths:
        if path.exists():
            print(f"Loading BTCUSD 4H bars from: {path.name}")
            bars = pd.read_csv(path, parse_dates=["timestamp"])
            bars = bars.set_index("timestamp")
            break
    
    if bars is None:
        raise FileNotFoundError(f"Could not find BTCUSD 4H bars in any of: {[p.name for p in possible_paths]}")
    
    # Filter to test period
    bars = bars.loc[start_date:end_date]
    print(f"Loaded {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")
    
    return bars


def generate_btc_4h_long_signals(bars: pd.DataFrame) -> pd.Series:
    """
    Generate long-only extreme reversal signals for BTCUSD 4H.
    
    Uses asymmetric strategy:
    - Extreme UP + high manip → LONG (continuation)
    - Extreme DOWN + high manip → LONG (reversal/bounce)
    """
    
    config = ExtremeReversalConfig(
        bar_size='4h',
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        use_normalized_trend=True,
        min_abs_R_past=0.003,
    )
    
    # Generate signals
    bars_with_signals = generate_asymmetric_signals(
        bars,
        config,
        return_col='returns',
        manip_col='ManipScore'
    )
    
    # Extract execution signal (already shifted to avoid look-ahead)
    signal_exec = bars_with_signals['exec_signal'].fillna(0).astype(int)
    
    return signal_exec


def compute_yearly_stats(trades: pd.DataFrame) -> pd.DataFrame:
    """Compute yearly performance breakdown from trades"""
    
    if len(trades) == 0:
        return pd.DataFrame()
    
    trades = trades.copy()
    trades['year'] = pd.to_datetime(trades['entry_time']).dt.year
    
    yearly = trades.groupby('year').agg({
        'pnl': ['count', 'sum', 'mean'],
    }).round(4)
    
    yearly.columns = ['num_trades', 'total_pnl', 'avg_pnl']
    yearly = yearly.reset_index()
    
    # Add win rate
    yearly['win_rate'] = trades.groupby('year').apply(
        lambda x: (x['pnl'] > 0).mean()
    ).values
    
    return yearly


def main():
    print("=" * 100)
    print("BTCUSD 4H TREND FILTER COMPARISON EXPERIMENT")
    print("=" * 100)
    
    # ===== 1. Load data =====
    print("\n[1/6] Loading BTCUSD 4H bars...")
    bars = load_btc_4h_bars(start_date="2017-01-01", end_date="2024-12-31")
    
    # ===== 2. Compute ATR =====
    print("\n[2/6] Computing ATR...")
    if "atr" not in bars.columns:
        atr = compute_atr(bars, window=10)
        bars['atr'] = atr
    else:
        atr = bars["atr"]
    print(f"ATR computed: mean={atr.mean():.2f}, median={atr.median():.2f}")
    
    # ===== 3. Generate signals =====
    print("\n[3/6] Generating long-only extreme reversal signals...")
    signal_exec = generate_btc_4h_long_signals(bars)
    print(f"Total signals: {signal_exec.sum()}")
    
    # ===== 4. Compute trend filter =====
    print("\n[4/6] Computing MA200 trend filter...")
    trend_up = compute_trend_filter_ma(bars, ma_length=200, use_daily=True)
    print(f"Uptrend bars: {trend_up.sum()} / {len(trend_up)} ({trend_up.mean()*100:.1f}%)")
    
    # Apply filter
    signal_exec_filtered = apply_trend_filter(signal_exec, trend_up)
    
    # Filter stats
    filter_stats = compute_trend_filter_stats(signal_exec, signal_exec_filtered, trend_up)
    print(f"\nTrend Filter Impact:")
    print(f"  Original signals: {filter_stats['total_signals_original']}")
    print(f"  Filtered signals: {filter_stats['total_signals_filtered']}")
    print(f"  Suppressed: {filter_stats['signals_suppressed']} ({filter_stats['suppression_rate']*100:.1f}%)")
    
    # ===== 5. Define exit rules =====
    print("\n[5/6] Defining exit rules...")
    
    # Best dynamic trailing rule from Phase 23
    TRAIL_T2_L1p0_SL3 = PortfolioExitRule(
        name="Trail_T2_L1.0_SL3",
        bar_size="4h",
        sl_atr_mult=3.0,
        tp_atr_mult=np.inf,
        max_holding_bars=20,
        trail_trigger_atr=2.0,
        trail_lock_atr=1.0,
    )
    
    # Pure baseline for comparison
    PURE_SL5_NOTP = PortfolioExitRule(
        name="Pure_SL5_NoTP_noMaxBars",
        bar_size="4h",
        sl_atr_mult=5.0,
        tp_atr_mult=np.inf,
        max_holding_bars=999,
        trail_trigger_atr=np.inf,
        trail_lock_atr=0.0,
    )
    
    rules = [TRAIL_T2_L1p0_SL3, PURE_SL5_NOTP]
    
    # ===== 6. Run backtests =====
    print("\n[6/6] Running backtests...")
    
    results = []
    
    for rule in rules:
        print(f"\n{'='*100}")
        print(f"Testing exit rule: {rule.name}")
        print(f"{'='*100}")
        
        # Baseline (no trend filter)
        print(f"\n  [A] Baseline (no trend filter)...")
        result_base = run_portfolio_backtest_with_exit_rule(
            bars=bars,
            signal_exec=signal_exec,
            atr=atr,
            rule=rule,
            cost_per_trade=0.0007,
            initial_equity=10000.0,
        )
        
        print(f"    Sharpe: {result_base['stats']['sharpe']:.2f}")
        print(f"    Total Return: {result_base['stats']['total_return']*100:.2f}%")
        print(f"    Max Drawdown: {result_base['stats']['max_drawdown']*100:.2f}%")
        print(f"    Num Trades: {result_base['stats']['num_trades']}")
        
        # Trend-filtered
        print(f"\n  [B] Trend-filtered (MA200)...")
        result_tf = run_portfolio_backtest_with_exit_rule(
            bars=bars,
            signal_exec=signal_exec_filtered,
            atr=atr,
            rule=rule,
            cost_per_trade=0.0007,
            initial_equity=10000.0,
        )
        
        print(f"    Sharpe: {result_tf['stats']['sharpe']:.2f}")
        print(f"    Total Return: {result_tf['stats']['total_return']*100:.2f}%")
        print(f"    Max Drawdown: {result_tf['stats']['max_drawdown']*100:.2f}%")
        print(f"    Num Trades: {result_tf['stats']['num_trades']}")
        
        # Store results
        results.append({
            "symbol": "BTCUSD",
            "timeframe": "4h",
            "exit_rule": rule.name,
            "variant": "no_trend_filter",
            **result_base["stats"]
        })
        
        results.append({
            "symbol": "BTCUSD",
            "timeframe": "4h",
            "exit_rule": rule.name,
            "variant": "ma200_filter",
            **result_tf["stats"]
        })
        
        # Save detailed results for Trail_T2_L1.0_SL3
        if rule.name == "Trail_T2_L1.0_SL3":
            # Save trades
            result_base['trades'].to_csv(
                project_root / "results/BTCUSD_4h_Trail_T2_L1.0_SL3_noFilter_trades.csv",
                index=False
            )
            result_tf['trades'].to_csv(
                project_root / "results/BTCUSD_4h_Trail_T2_L1.0_SL3_ma200_trades.csv",
                index=False
            )
            
            # Save equity curves
            result_base['equity_curve'].to_csv(
                project_root / "results/BTCUSD_4h_Trail_T2_L1.0_SL3_noFilter_equity.csv"
            )
            result_tf['equity_curve'].to_csv(
                project_root / "results/BTCUSD_4h_Trail_T2_L1.0_SL3_ma200_equity.csv"
            )
            
            # Compute yearly stats
            yearly_base = compute_yearly_stats(result_base['trades'])
            yearly_tf = compute_yearly_stats(result_tf['trades'])
            
            print(f"\n  Yearly Performance (Baseline):")
            print(yearly_base.to_string(index=False))
            
            print(f"\n  Yearly Performance (MA200 Filter):")
            print(yearly_tf.to_string(index=False))
    
    # ===== 7. Save summary =====
    df_summary = pd.DataFrame(results)
    output_path = project_root / "results/btc_4h_trend_filter_compare_summary.csv"
    df_summary.to_csv(output_path, index=False)
    
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")
    print(df_summary.to_string(index=False))
    
    print(f"\n✅ Results saved to: {output_path.name}")
    print(f"\n{'='*100}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()

