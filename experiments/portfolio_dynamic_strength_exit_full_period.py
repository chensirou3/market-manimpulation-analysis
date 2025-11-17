# -*- coding: utf-8 -*-
"""
Portfolio Dynamic Strength-Based Exit - Full Period Test

Test Layer 3 dynamic exit system on full historical data:
- BTCUSD 4H: 2017-2024 (7-8 years)
- ETHUSD 4H: 2017-2024 (7 years)
- XAUUSD 4H: 2016-2024 (9 years)

Compare:
1. Pure baseline
2. Best static/trailing rule
3. Dynamic strength-based exit
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

# Import modules
from src.analysis.trade_strength_features import (
    compute_trade_entry_features,
    label_signal_strength,
    attach_strength_to_trade_paths
)
from src.backtest.portfolio_backtest import run_portfolio_backtest_with_exit_rule
from src.backtest.portfolio_backtest_dynamic import run_portfolio_backtest_with_dynamic_exit
from src.backtest.exit_rules_portfolio import PortfolioExitRule


def load_bars(symbol: str, timeframe: str = "4h", L_past: int = 5, vol_window: int = 20) -> pd.DataFrame:
    """Load bars with ManipScore and compute TS if needed"""
    symbol_lower = symbol.lower().replace('usd', '')  # btc, xau, eth

    # Try full historical data first, then fall back to shorter versions
    possible_paths = [
        project_root / f"results/bars_{timeframe}_{symbol_lower}_full_with_manipscore.csv",  # Full historical
        project_root / f"results/{symbol}_{timeframe}_bars_with_manipscore_full.csv",
        project_root / f"results/bars_{timeframe}_{symbol_lower}_with_manipscore_full.csv",
        project_root / f"results/bars_{timeframe}_with_manipscore_full.csv",  # For XAUUSD
    ]
    
    for file_path in possible_paths:
        if file_path.exists():
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp').sort_index()
            
            # Compute TS if not present
            if 'TS' not in df.columns:
                if 'returns' in df.columns:
                    ret = df['returns']
                elif 'log_return' in df.columns:
                    ret = df['log_return']
                else:
                    ret = np.log(df['close'] / df['close'].shift(1))
                
                R_past = ret.rolling(window=L_past).sum()
                sigma = ret.rolling(window=vol_window).std()
                sigma = sigma.replace(0, np.nan)
                df['TS'] = R_past / sigma
            
            return df
    
    raise FileNotFoundError(f"Could not find bars file for {symbol} {timeframe}. Tried: {possible_paths}")


def ensure_atr(bars: pd.DataFrame, window: int = 14) -> pd.Series:
    """Compute or load ATR"""
    if 'atr' in bars.columns:
        return bars['atr']
    
    high = bars['high']
    low = bars['low']
    close = bars['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()
    
    return atr


def generate_4h_long_signals(bars: pd.DataFrame, L_past: int = 5, vol_window: int = 20) -> pd.Series:
    """Generate 4H long-only extreme reversal signals (asymmetric)"""
    if 'ManipScore' not in bars.columns:
        raise ValueError("Bars must have 'ManipScore' column")
    
    if 'returns' in bars.columns:
        ret = bars['returns']
    elif 'log_return' in bars.columns:
        ret = bars['log_return']
    else:
        ret = np.log(bars['close'] / bars['close'].shift(1))
    
    if 'TS' not in bars.columns:
        R_past = ret.rolling(window=L_past).sum()
        sigma = ret.rolling(window=vol_window).std()
        sigma = sigma.replace(0, np.nan)
        TS = R_past / sigma
    else:
        TS = bars['TS']
    
    # Compute thresholds (90th percentile)
    ts_threshold = TS.abs().quantile(0.90)
    ms_threshold = bars['ManipScore'].quantile(0.90)
    
    # Asymmetric logic
    extreme_up = (TS > ts_threshold) & (ret > 0) & (bars['ManipScore'] > ms_threshold)
    extreme_down = (TS < -ts_threshold) & (ret < 0) & (bars['ManipScore'] > ms_threshold)
    
    signal = (extreme_up | extreme_down).astype(int)
    
    return signal


def get_baseline_rules(symbol: str) -> tuple:
    """Get baseline exit rules for comparison"""
    if symbol == "BTCUSD":
        pure_rule = PortfolioExitRule(
            name="PURE_BASELINE",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
        
        best_rule = PortfolioExitRule(
            name="BEST_STATIC_Trail_T2_L1_SL3",
            bar_size="4h",
            sl_atr_mult=3.0,
            tp_atr_mult=np.inf,
            max_holding_bars=20,
            trail_trigger_atr=2.0,
            trail_lock_atr=1.0
        )
    elif symbol == "ETHUSD":
        pure_rule = PortfolioExitRule(
            name="PURE_BASELINE",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
        
        best_rule = PortfolioExitRule(
            name="BEST_STATIC_Trail_T2_L1_SL3",
            bar_size="4h",
            sl_atr_mult=3.0,
            tp_atr_mult=np.inf,
            max_holding_bars=20,
            trail_trigger_atr=2.0,
            trail_lock_atr=1.0
        )
    else:  # XAUUSD
        pure_rule = PortfolioExitRule(
            name="PURE_BASELINE",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=999,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
        
        best_rule = PortfolioExitRule(
            name="BEST_STATIC_SL5_NoTP",
            bar_size="4h",
            sl_atr_mult=5.0,
            tp_atr_mult=np.inf,
            max_holding_bars=30,
            trail_trigger_atr=np.inf,
            trail_lock_atr=0.0
        )
    
    return pure_rule, best_rule


def build_stats_row(symbol: str, variant: str, stats: dict, period: str) -> dict:
    """Build a row for summary table"""
    return {
        'symbol': symbol,
        'period': period,
        'variant': variant,
        'total_return': stats.get('total_return', 0.0),
        'ann_return': stats.get('ann_return', 0.0),
        'ann_vol': stats.get('ann_vol', 0.0),
        'sharpe': stats.get('sharpe', 0.0),
        'max_drawdown': stats.get('max_drawdown', 0.0),
        'num_trades': stats.get('num_trades', 0),
        'win_rate': stats.get('win_rate', 0.0),
        'avg_pnl_per_trade': stats.get('avg_pnl_per_trade', 0.0),
        # Strength-specific stats
        'strong_count': stats.get('strong_count', 0),
        'strong_win_rate': stats.get('strong_win_rate', 0.0),
        'strong_avg_pnl': stats.get('strong_avg_pnl', 0.0),
        'medium_count': stats.get('medium_count', 0),
        'medium_win_rate': stats.get('medium_win_rate', 0.0),
        'medium_avg_pnl': stats.get('medium_avg_pnl', 0.0),
        'weak_count': stats.get('weak_count', 0),
        'weak_win_rate': stats.get('weak_win_rate', 0.0),
        'weak_avg_pnl': stats.get('weak_avg_pnl', 0.0),
    }


def main():
    """
    Main experiment: Full period test of dynamic strength-based exit system
    """
    print("=" * 80)
    print("Portfolio Dynamic Strength-Based Exit - FULL PERIOD TEST")
    print("=" * 80)

    # Test configuration
    test_configs = [
        {
            'symbol': 'BTCUSD',
            'timeframe': '4h',
            'start_date': '2017-01-01',
            'end_date': '2024-12-31',
            'description': 'BTC 2017-2024 (7-8 years)'
        },
        {
            'symbol': 'ETHUSD',
            'timeframe': '4h',
            'start_date': '2017-01-01',
            'end_date': '2024-12-31',
            'description': 'ETH 2017-2024 (7 years)'
        },
        {
            'symbol': 'XAUUSD',
            'timeframe': '4h',
            'start_date': '2016-01-01',
            'end_date': '2024-12-31',
            'description': 'XAU 2016-2024 (9 years)'
        }
    ]

    rows = []

    for config in test_configs:
        symbol = config['symbol']
        timeframe = config['timeframe']
        start_date = config['start_date']
        end_date = config['end_date']
        description = config['description']

        print(f"\n{'='*80}")
        print(f"Processing {symbol} {timeframe}: {description}")
        print(f"{'='*80}")

        # Load data
        print(f"Loading bars for {symbol}...")
        try:
            bars = load_bars(symbol, timeframe)
        except FileNotFoundError as e:
            print(f"  ERROR: {e}")
            print(f"  Skipping {symbol}")
            continue

        # Filter date range
        bars = bars.loc[start_date:end_date]

        if len(bars) == 0:
            print(f"  ERROR: No data in date range {start_date} to {end_date}")
            continue

        print(f"  Loaded {len(bars)} bars from {bars.index[0]} to {bars.index[-1]}")

        # Compute ATR
        atr = ensure_atr(bars)

        # Generate signals
        print(f"Generating signals...")
        signal_exec = generate_4h_long_signals(bars)
        num_signals = signal_exec.sum()
        print(f"  Generated {num_signals} signals")

        if num_signals == 0:
            print(f"  WARNING: No signals generated for {symbol}")
            continue

        # Compute entry features
        print(f"Computing entry features from signals...")
        signal_times = bars.index[signal_exec == 1]

        entry_data = []
        for i, entry_time in enumerate(signal_times):
            if entry_time in bars.index:
                bar = bars.loc[entry_time]
                entry_data.append({
                    'trade_id': i + 1,
                    'entry_time': entry_time,
                    'entry_TS': bar.get('TS', np.nan),
                    'entry_ManipScore': bar.get('ManipScore', np.nan)
                })

        entry_features = pd.DataFrame(entry_data)
        entry_features = label_signal_strength(entry_features)

        # Print strength distribution
        strength_dist = entry_features['signal_strength'].value_counts()
        print(f"  Signal strength distribution:")
        for strength, count in strength_dist.items():
            pct = count / len(entry_features) * 100
            print(f"    {strength}: {count} ({pct:.1f}%)")

        # Get baseline rules
        pure_rule, best_rule = get_baseline_rules(symbol)

        # 1) Pure baseline
        print(f"\n[1/3] Running PURE baseline...")
        result_pure = run_portfolio_backtest_with_exit_rule(
            bars, signal_exec, atr, pure_rule
        )
        rows.append(build_stats_row(symbol, "pure", result_pure["stats"], description))
        print(f"  Sharpe: {result_pure['stats']['sharpe']:.2f}, "
              f"Total Return: {result_pure['stats']['total_return']*100:.2f}%")

        # 2) Best static/trailing baseline
        print(f"\n[2/3] Running BEST_STATIC baseline...")
        result_best = run_portfolio_backtest_with_exit_rule(
            bars, signal_exec, atr, best_rule
        )
        rows.append(build_stats_row(symbol, "best_static", result_best["stats"], description))
        print(f"  Sharpe: {result_best['stats']['sharpe']:.2f}, "
              f"Total Return: {result_best['stats']['total_return']*100:.2f}%")

        # 3) Dynamic strength-based exit
        print(f"\n[3/3] Running DYNAMIC_STRENGTH exit...")
        result_dyn = run_portfolio_backtest_with_dynamic_exit(
            bars, signal_exec, atr, entry_features, symbol
        )
        rows.append(build_stats_row(symbol, "dynamic_strength", result_dyn["stats"], description))
        print(f"  Sharpe: {result_dyn['stats']['sharpe']:.2f}, "
              f"Total Return: {result_dyn['stats']['total_return']*100:.2f}%")

        # Print strength breakdown
        stats = result_dyn['stats']
        print(f"\n  Strength breakdown:")
        for strength in ['strong', 'medium', 'weak']:
            count = stats.get(f'{strength}_count', 0)
            wr = stats.get(f'{strength}_win_rate', 0.0)
            avg_pnl = stats.get(f'{strength}_avg_pnl', 0.0)
            print(f"    {strength}: {count} trades, WR={wr*100:.1f}%, Avg PnL={avg_pnl*100:.2f}%")

        # Save detailed results
        result_dyn['trades'].to_csv(
            project_root / f"results/{symbol}_4h_full_dynamic_strength_trades.csv",
            index=False
        )
        result_dyn['equity_curve'].to_csv(
            project_root / f"results/{symbol}_4h_full_dynamic_strength_equity.csv"
        )

    # Save summary
    df_summary = pd.DataFrame(rows)

    output_path = project_root / "results/portfolio_dynamic_strength_exit_full_period_summary.csv"
    df_summary.to_csv(output_path, index=False)

    print(f"\n{'='*80}")
    print("SUMMARY - FULL PERIOD TEST")
    print(f"{'='*80}")
    print(df_summary[['symbol', 'period', 'variant', 'total_return', 'sharpe', 'win_rate',
                      'num_trades', 'max_drawdown']].to_string(index=False))

    print(f"\n✅ Results saved to: {output_path}")
    print(f"✅ Detailed trades and equity curves saved to results/")


if __name__ == "__main__":
    main()

