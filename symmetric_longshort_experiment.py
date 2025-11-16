"""
对称多空反转策略实验

Symmetric Long/Short Reversal Strategy Experiment

目标：
1. 实现严格对称的多空反转信号
2. 对比三种策略：
   - Strategy A: Long-only (仅做多)
   - Strategy B: Symmetric Long/Short (对称多空)
   - Strategy C: Short-only (仅做空)
3. 在4小时数据上测试BTC, ETH, XAUUSD
4. 扩展到所有时间周期

理论基础：
- 极端上涨 + 高ManipScore → 价格被推高 → 预期反转向下 → 做空
- 极端下跌 + 高ManipScore → 价格被打压 → 预期反转向上 → 做多
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
import sys

# Add src to path
sys.path.append('market-manimpulation-analysis')

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import (
    compute_trend_strength,
    compute_extreme_trend_thresholds
)


def generate_symmetric_reversal_signals(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig,
    return_col: str = 'returns'
) -> pd.DataFrame:
    """
    生成严格对称的多空反转信号。
    
    Generate strictly symmetric long/short reversal signals.
    
    信号逻辑 (Signal Logic):
    
    1. 极端上涨 (Extreme UP):
       - TS > T_trend (趋势强度超过阈值)
       - ret > 0 (当前bar上涨)
       - ManipScore > M_thresh (异常分数高)
       → signal = -1 (做空，预期反转向下)
    
    2. 极端下跌 (Extreme DOWN):
       - TS < -T_trend (趋势强度低于负阈值)
       - ret < 0 (当前bar下跌)
       - ManipScore > M_thresh (异常分数高)
       → signal = +1 (做多，预期反转向上)
    
    3. 其他情况:
       → signal = 0 (不交易)
    
    Args:
        bars: DataFrame with OHLC, returns, ManipScore
        config: ExtremeReversalConfig
        return_col: Name of return column
    
    Returns:
        DataFrame with columns:
        - signal_raw: Raw signal (-1, 0, +1)
        - signal_exec: Execution signal (shifted by 1 bar)
        - extreme_up: Boolean flag for extreme up regime
        - extreme_down: Boolean flag for extreme down regime
        - high_manip: Boolean flag for high ManipScore
    """
    bars = bars.copy()
    
    # 1. Compute trend strength if not present
    if 'TS' not in bars.columns:
        bars = compute_trend_strength(bars, config.L_past, config.vol_window)
    
    # 2. Compute extreme trend thresholds
    thresholds = compute_extreme_trend_thresholds(bars, quantile=config.q_extreme_trend)
    T_trend = thresholds['threshold']
    
    print(f"  Extreme trend threshold: {T_trend:.4f}")
    
    # 3. Compute ManipScore threshold
    M_thresh = bars['ManipScore'].quantile(config.q_manip)
    print(f"  ManipScore threshold (q={config.q_manip}): {M_thresh:.4f}")
    
    # 4. Identify regimes
    # Extreme UP: TS > T_trend AND ret > 0 AND ManipScore > M_thresh
    extreme_up = (
        (bars['TS'] > T_trend) &
        (bars[return_col] > 0) &
        (bars['ManipScore'] > M_thresh)
    )
    
    # Extreme DOWN: TS < -T_trend AND ret < 0 AND ManipScore > M_thresh
    extreme_down = (
        (bars['TS'] < -T_trend) &
        (bars[return_col] < 0) &
        (bars['ManipScore'] > M_thresh)
    )
    
    high_manip = bars['ManipScore'] > M_thresh
    
    # 5. Generate signals
    signal_raw = pd.Series(0, index=bars.index)
    signal_raw[extreme_up] = -1  # Short on extreme up
    signal_raw[extreme_down] = +1  # Long on extreme down
    
    # 6. Shift signal for execution (trade at next bar's open)
    signal_exec = signal_raw.shift(1).fillna(0)
    
    # 7. Create result DataFrame
    result = pd.DataFrame({
        'signal_raw': signal_raw,
        'signal_exec': signal_exec,
        'extreme_up': extreme_up,
        'extreme_down': extreme_down,
        'high_manip': high_manip
    }, index=bars.index)
    
    # Print signal statistics
    n_extreme_up = extreme_up.sum()
    n_extreme_down = extreme_down.sum()
    n_signals = (signal_exec != 0).sum()
    n_long = (signal_exec == 1).sum()
    n_short = (signal_exec == -1).sum()
    
    print(f"  Extreme UP bars: {n_extreme_up} ({n_extreme_up/len(bars)*100:.2f}%)")
    print(f"  Extreme DOWN bars: {n_extreme_down} ({n_extreme_down/len(bars)*100:.2f}%)")
    print(f"  Total signals: {n_signals} (Long: {n_long}, Short: {n_short})")
    
    return result


def load_bars_for_symbol_timeframe(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    加载指定symbol和timeframe的bar数据。

    Load bar data for given symbol and timeframe.

    Supports: BTC, ETH, XAUUSD, EURUSD, USDCHF
    """
    # File naming convention
    symbol_upper = symbol.upper()

    if symbol_upper == 'XAUUSD':
        filename = f'bars_{timeframe}_with_manipscore_full.csv'
    elif symbol_upper in ['EURUSD', 'USDCHF']:
        # Forex pairs: bars_{timeframe}_{symbol_lower}_full_with_manipscore.csv
        filename = f'bars_{timeframe}_{symbol.lower()}_full_with_manipscore.csv'
    else:
        # Crypto: BTC, ETH
        symbol_lower = symbol.lower().replace('usd', '')
        filename = f'bars_{timeframe}_{symbol_lower}_full_with_manipscore.csv'

    filepath = Path('market-manimpulation-analysis/results') / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp')

    return df


def run_strategy_comparison(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig,
    symbol: str,
    timeframe: str
) -> Dict:
    """
    运行三种策略的对比测试。

    Run comparison of three strategies:
    - Strategy A: Long-only
    - Strategy B: Symmetric Long/Short
    - Strategy C: Short-only

    Returns:
        Dictionary with results for each strategy
    """
    print(f"\n{'='*80}")
    print(f"Testing {symbol} {timeframe}")
    print(f"{'='*80}")
    print(f"Data range: {bars.index[0]} to {bars.index[-1]}")
    print(f"Total bars: {len(bars)}")

    # Generate symmetric signals
    print("\nGenerating symmetric signals...")
    signals_df = generate_symmetric_reversal_signals(bars, config)

    # Strategy A: Long-only
    print("\n" + "-"*80)
    print("Strategy A: LONG-ONLY")
    print("-"*80)
    signals_long = signals_df['signal_exec'].copy()
    signals_long[signals_long == -1] = 0  # Remove short signals
    print(f"Long signals: {(signals_long == 1).sum()}")

    result_long = run_extreme_reversal_backtest(
        bars=bars,
        exec_signals=signals_long,
        config=config,
        initial_capital=10000.0
    )

    # Strategy B: Symmetric Long/Short
    print("\n" + "-"*80)
    print("Strategy B: SYMMETRIC LONG/SHORT")
    print("-"*80)
    signals_symmetric = signals_df['signal_exec'].copy()
    print(f"Long signals: {(signals_symmetric == 1).sum()}")
    print(f"Short signals: {(signals_symmetric == -1).sum()}")

    result_symmetric = run_extreme_reversal_backtest(
        bars=bars,
        exec_signals=signals_symmetric,
        config=config,
        initial_capital=10000.0
    )

    # Strategy C: Short-only
    print("\n" + "-"*80)
    print("Strategy C: SHORT-ONLY")
    print("-"*80)
    signals_short = signals_df['signal_exec'].copy()
    signals_short[signals_short == 1] = 0  # Remove long signals
    print(f"Short signals: {(signals_short == -1).sum()}")

    result_short = run_extreme_reversal_backtest(
        bars=bars,
        exec_signals=signals_short,
        config=config,
        initial_capital=10000.0
    )

    # Compile results
    results = {
        'symbol': symbol,
        'timeframe': timeframe,
        'bars_count': len(bars),
        'date_start': bars.index[0],
        'date_end': bars.index[-1],
        'strategy_A_long_only': {
            'stats': result_long.stats,
            'n_trades': len(result_long.trades),
            'result': result_long
        },
        'strategy_B_symmetric': {
            'stats': result_symmetric.stats,
            'n_trades': len(result_symmetric.trades),
            'result': result_symmetric
        },
        'strategy_C_short_only': {
            'stats': result_short.stats,
            'n_trades': len(result_short.trades),
            'result': result_short
        }
    }

    # Print comparison
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)

    print(f"\n{'Metric':<30} {'Long-Only':>15} {'Symmetric':>15} {'Short-Only':>15}")
    print("-"*80)

    metrics = [
        ('Total Return (%)', 'total_return'),
        ('Ann. Return (%)', 'annualized_return'),
        ('Ann. Volatility (%)', 'annualized_volatility'),
        ('Sharpe Ratio', 'sharpe_ratio'),
        ('Max Drawdown (%)', 'max_drawdown'),
        ('Number of Trades', 'n_trades'),
        ('Win Rate (%)', 'win_rate'),
        ('Avg PnL (%)', 'avg_pnl_pct')
    ]

    for metric_name, metric_key in metrics:
        if metric_key == 'n_trades':
            val_long = results['strategy_A_long_only']['n_trades']
            val_sym = results['strategy_B_symmetric']['n_trades']
            val_short = results['strategy_C_short_only']['n_trades']
            print(f"{metric_name:<30} {val_long:>15.0f} {val_sym:>15.0f} {val_short:>15.0f}")
        else:
            val_long = results['strategy_A_long_only']['stats'].get(metric_key, 0)
            val_sym = results['strategy_B_symmetric']['stats'].get(metric_key, 0)
            val_short = results['strategy_C_short_only']['stats'].get(metric_key, 0)

            if 'rate' in metric_key.lower() or 'pnl' in metric_key.lower():
                val_long *= 100
                val_sym *= 100
                val_short *= 100

            print(f"{metric_name:<30} {val_long:>15.2f} {val_sym:>15.2f} {val_short:>15.2f}")

    return results


def save_comparison_results(all_results: list, output_file: str):
    """
    保存所有对比结果到CSV文件。

    Save all comparison results to CSV file.
    """
    rows = []

    for res in all_results:
        for strategy_name in ['strategy_A_long_only', 'strategy_B_symmetric', 'strategy_C_short_only']:
            strategy_data = res[strategy_name]
            stats = strategy_data['stats']

            row = {
                'symbol': res['symbol'],
                'timeframe': res['timeframe'],
                'strategy': strategy_name.replace('strategy_', '').replace('_', ' ').title(),
                'bars_count': res['bars_count'],
                'date_start': res['date_start'],
                'date_end': res['date_end'],
                'n_trades': strategy_data['n_trades'],
                'total_return': stats.get('total_return', 0),
                'ann_return': stats.get('annualized_return', 0),
                'ann_volatility': stats.get('annualized_volatility', 0),
                'sharpe_ratio': stats.get('sharpe_ratio', 0),
                'max_drawdown': stats.get('max_drawdown', 0),
                'win_rate': stats.get('win_rate', 0),
                'avg_pnl_pct': stats.get('avg_pnl_pct', 0),
                'profit_factor': stats.get('profit_factor', 0)
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    return df


def main():
    """
    主函数：运行对称多空策略实验。

    Main function: Run symmetric long/short strategy experiment.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Symmetric Long/Short Reversal Strategy Experiment')
    parser.add_argument('--symbols', nargs='+', default=['btc', 'eth', 'xauusd'],
                       help='Symbols to test (default: btc eth xauusd)')
    parser.add_argument('--timeframes', nargs='+', default=['4h'],
                       help='Timeframes to test (default: 4h)')
    parser.add_argument('--cost', type=float, default=0.0007,
                       help='Transaction cost per trade (default: 0.0007 = 7bp)')
    parser.add_argument('--output', type=str, default='market-manimpulation-analysis/results/symmetric_longshort_comparison.csv',
                       help='Output CSV file path')

    args = parser.parse_args()

    # Configuration
    config = ExtremeReversalConfig(
        bar_size='4h',  # Will be updated for each timeframe
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5,
        tp_atr_mult=0.8,
        cost_per_trade=args.cost
    )

    print("="*80)
    print("SYMMETRIC LONG/SHORT REVERSAL STRATEGY EXPERIMENT")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Symbols: {args.symbols}")
    print(f"  Timeframes: {args.timeframes}")
    print(f"  Transaction cost: {args.cost*100:.2f}bp")
    print(f"  L_past: {config.L_past}")
    print(f"  Vol window: {config.vol_window}")
    print(f"  Extreme trend quantile: {config.q_extreme_trend}")
    print(f"  ManipScore quantile: {config.q_manip}")
    print(f"  Holding horizon: {config.holding_horizon} bars")
    print(f"  SL/TP: {config.sl_atr_mult}x / {config.tp_atr_mult}x ATR")

    # Run experiments
    all_results = []

    for timeframe in args.timeframes:
        for symbol in args.symbols:
            try:
                # Update config for this timeframe
                config.bar_size = timeframe

                # Load data
                print(f"\nLoading data for {symbol.upper()} {timeframe}...")
                bars = load_bars_for_symbol_timeframe(symbol, timeframe)

                # Run comparison
                results = run_strategy_comparison(bars, config, symbol.upper(), timeframe)
                all_results.append(results)

            except FileNotFoundError as e:
                print(f"\nSkipping {symbol} {timeframe}: {e}")
                continue
            except Exception as e:
                print(f"\nError processing {symbol} {timeframe}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # Save results
    if all_results:
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        df_results = save_comparison_results(all_results, args.output)

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY BY STRATEGY")
        print("="*80)

        summary = df_results.groupby('strategy').agg({
            'n_trades': 'sum',
            'total_return': 'mean',
            'sharpe_ratio': 'mean',
            'win_rate': 'mean',
            'max_drawdown': 'mean'
        })

        print(summary)

        print("\n" + "="*80)
        print("EXPERIMENT COMPLETE!")
        print("="*80)
    else:
        print("\nNo results to save.")


if __name__ == '__main__':
    main()



