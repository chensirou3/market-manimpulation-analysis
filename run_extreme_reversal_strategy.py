"""
Extreme Reversal Strategy - Main Execution Script

This script demonstrates the complete workflow:
1. Load bar-level data with ManipScore
2. Generate extreme reversal signals
3. Run backtest
4. Display results and plots
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Import strategy modules
from src.strategies import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals,
    run_extreme_reversal_backtest,
    print_backtest_summary
)

from src.visualization import (
    plot_equity_curve,
    plot_conditional_returns,
    plot_signal_diagnostics,
    plot_comprehensive_analysis
)


def load_bars_for_symbol(
    symbol: str = "XAUUSD",
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31"
) -> pd.DataFrame:
    """
    加载K线数据（带ManipScore）。
    
    Load bar-level data with ManipScore from processed results.
    
    Args:
        symbol: Trading symbol (default: XAUUSD)
        start_date: Start date
        end_date: End date
    
    Returns:
        DataFrame with OHLC, returns, and manip_score
    """
    results_dir = Path('results')
    
    # Find all result files in date range
    all_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))
    
    # Filter by date range
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    dfs = []
    for file in all_files:
        # Extract date from filename: bars_with_manipscore_2024-01-01_2024-03-31.csv
        import re
        match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})', file.name)

        if match:
            file_start = match.group(1)
            file_end = match.group(2)

            file_start_dt = pd.to_datetime(file_start)
            file_end_dt = pd.to_datetime(file_end)

            # Check if file overlaps with requested range
            if file_start_dt <= end_dt and file_end_dt >= start_dt:
                df = pd.read_csv(file, index_col=0, parse_dates=True)
                dfs.append(df)
    
    if not dfs:
        raise ValueError(f"No data found for {symbol} between {start_date} and {end_date}")
    
    # Combine all data
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()

    # Make sure index is timezone-aware if needed
    if bars.index.tz is not None:
        start_dt = start_dt.tz_localize(bars.index.tz)
        end_dt = end_dt.tz_localize(bars.index.tz)

    # Filter to exact date range
    bars = bars.loc[start_dt:end_dt]
    
    # Ensure required columns exist
    if 'returns' not in bars.columns and 'close' in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    # Rename columns to match expected format
    column_mapping = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'manip_score': 'manip_score',
        'returns': 'returns'
    }
    
    # Check for missing columns
    missing_cols = []
    for expected_col in ['open', 'high', 'low', 'close', 'manip_score']:
        if expected_col not in bars.columns:
            missing_cols.append(expected_col)
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    print(f"✅ Loaded {len(bars):,} bars from {bars.index[0]} to {bars.index[-1]}")
    print(f"   Columns: {bars.columns.tolist()}")
    
    return bars


def main():
    """主函数 / Main function."""
    
    print("=" * 80)
    print("极端操纵反转策略 / Extreme Manipulation Reversal Strategy")
    print("=" * 80)
    print()
    
    # Step 1: Load data
    print("【步骤 1】加载数据 / Loading Data")
    print("-" * 80)
    
    bars = load_bars_for_symbol(
        symbol="XAUUSD",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    print()
    
    # Step 2: Configure strategy
    print("【步骤 2】配置策略 / Configuring Strategy")
    print("-" * 80)
    
    config = ExtremeReversalConfig(
        # Trend parameters
        L_past=5,                    # 5-bar lookback for trend
        vol_window=20,               # 20-bar volatility window
        q_extreme_trend=0.90,        # 90th percentile for extreme trend
        use_normalized_trend=True,   # Use volatility-normalized TS
        min_abs_R_past=0.005,        # Minimum 0.5% absolute move
        
        # ManipScore parameters
        q_manip=0.90,                # 90th percentile for high ManipScore
        min_manip_score=0.7,         # Minimum ManipScore of 0.7
        
        # Execution parameters
        holding_horizon=5,           # Hold for 5 bars max
        atr_window=10,               # 10-bar ATR
        sl_atr_mult=0.5,             # SL at 0.5 * ATR
        tp_atr_mult=0.8,             # TP at 0.8 * ATR
        cost_per_trade=0.0001        # 1 bp transaction cost
    )
    
    print(f"  L_past: {config.L_past}")
    print(f"  q_extreme_trend: {config.q_extreme_trend}")
    print(f"  q_manip: {config.q_manip}")
    print(f"  holding_horizon: {config.holding_horizon}")
    print()
    
    # Step 3: Generate signals
    print("【步骤 3】生成信号 / Generating Signals")
    print("-" * 80)
    
    bars_with_signals = generate_extreme_reversal_signals(bars, config)
    
    n_signals = (bars_with_signals['exec_signal'] != 0).sum()
    n_long = (bars_with_signals['exec_signal'] == 1).sum()
    n_short = (bars_with_signals['exec_signal'] == -1).sum()
    
    print(f"  总信号数: {n_signals}")
    print(f"  做多信号: {n_long}")
    print(f"  做空信号: {n_short}")
    print(f"  信号率: {n_signals / len(bars_with_signals) * 100:.2f}%")
    print()
    
    # Step 4: Run backtest
    print("【步骤 4】运行回测 / Running Backtest")
    print("-" * 80)
    
    result = run_extreme_reversal_backtest(
        bars_with_signals,
        bars_with_signals['exec_signal'],
        config,
        initial_capital=10000.0
    )
    
    print()
    
    # Step 5: Display results
    print_backtest_summary(result)
    
    # Step 6: Generate plots
    print("\n【步骤 5】生成图表 / Generating Plots")
    print("-" * 80)
    
    # Equity curve
    fig1 = plot_equity_curve(result.equity_curve, show_drawdown=True)
    plt.savefig('results/extreme_reversal_equity_curve.png', dpi=150, bbox_inches='tight')
    print("  ✅ 权益曲线已保存: results/extreme_reversal_equity_curve.png")
    
    # Conditional returns
    fig2 = plot_conditional_returns(bars_with_signals, holding_horizon=config.holding_horizon)
    plt.savefig('results/extreme_reversal_conditional_returns.png', dpi=150, bbox_inches='tight')
    print("  ✅ 条件收益分布已保存: results/extreme_reversal_conditional_returns.png")
    
    # Signal diagnostics
    fig3 = plot_signal_diagnostics(bars_with_signals)
    plt.savefig('results/extreme_reversal_signal_diagnostics.png', dpi=150, bbox_inches='tight')
    print("  ✅ 信号诊断图已保存: results/extreme_reversal_signal_diagnostics.png")
    
    # Comprehensive analysis
    fig4 = plot_comprehensive_analysis(bars_with_signals, result.equity_curve, result.trades)
    plt.savefig('results/extreme_reversal_comprehensive.png', dpi=150, bbox_inches='tight')
    print("  ✅ 综合分析图已保存: results/extreme_reversal_comprehensive.png")
    
    print()
    print("=" * 80)
    print("🎉 策略回测完成！/ Strategy Backtest Complete!")
    print("=" * 80)
    
    # Show plots
    plt.show()


if __name__ == "__main__":
    main()

