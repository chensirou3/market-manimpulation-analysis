# -*- coding: utf-8 -*-
"""
Trade Path Analysis for All Assets (BTC, ETH, XAUUSD) and All Timeframes

This script will:
1. Run trade path analysis for each asset and each timeframe
2. Generate detailed trade records CSV
3. Generate summary comparison table
4. Save all results
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.trade_path_analysis import (
    TradePathConfig,
    analyze_trade_paths_long_only,
    summarize_trade_paths,
    print_trade_path_summary
)
from src.strategies.extreme_reversal import generate_extreme_reversal_signals, ExtremeReversalConfig
from src.strategies.trend_features import compute_trend_strength

def main():
    """Main function: Analyze all assets across all timeframes"""

    # Define assets and timeframes
    assets = {
        'BTC': 'btc',
        'ETH': 'eth',
        'XAUUSD': 'xauusd'
    }

    timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']

    # Store all results
    all_results = []

    print("=" * 80)
    print("Starting Trade Path Analysis for All Assets and All Timeframes")
    print("=" * 80)
    print()

    # Iterate through each asset
    for asset_name, asset_code in assets.items():
        print(f"\n{'=' * 80}")
        print(f"Analyzing Asset: {asset_name}")
        print(f"{'=' * 80}\n")

        # Iterate through each timeframe
        for tf in timeframes:
            print(f"\n{'-' * 60}")
            print(f"Timeframe: {tf}")
            print(f"{'-' * 60}")
            
            # Build data file path
            data_file = f'results/bars_{tf}_{asset_code}_full_with_manipscore.csv'

            # Check if file exists
            if not Path(data_file).exists():
                print(f"WARNING: Data file not found: {data_file}")
                print(f"Skipping {asset_name} {tf}")
                continue

            try:
                # Read data
                print(f"Reading data: {data_file}")
                df = pd.read_csv(data_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp').sort_index()

                print(f"Data range: {df.index[0]} to {df.index[-1]}")
                print(f"Data rows: {len(df):,}")

                # Generate signals
                print(f"\nGenerating trading signals...")

                # Create strategy configuration
                strategy_config = ExtremeReversalConfig(
                    L_past=5,
                    vol_window=20,
                    q_extreme_trend=0.9,
                    q_manip=0.9
                )

                # Generate extreme reversal signals (use ManipScore column name)
                df = generate_extreme_reversal_signals(df, strategy_config, manip_col='ManipScore')

                # Extract execution signals (Long-Only)
                signal_exec = df['exec_signal'].copy()
                signal_exec[signal_exec == -1] = 0  # Remove short signals

                # Calculate ATR
                if 'atr' not in df.columns:
                    df['atr'] = df['close'].rolling(10).std()  # Simple ATR estimate

                # Configure analysis parameters
                config = TradePathConfig(
                    max_loss_atr=5.0,        # ATR stop loss multiplier
                    max_holding_bars=None    # No time limit
                )

                # Run analysis
                print(f"\nRunning trade path analysis...")
                trade_records = analyze_trade_paths_long_only(df, signal_exec, df['atr'], config)

                if len(trade_records) == 0:
                    print(f"WARNING: No trade records generated")
                    continue

                # Summarize statistics
                summary = summarize_trade_paths(trade_records)

                # Print summary
                print_trade_path_summary(summary, title=f"{asset_name} {tf} Trade Path Analysis")

                # Save detailed trade records
                output_file = f'results/{asset_code}_{tf}_trade_path_analysis.csv'
                trade_records.to_csv(output_file, index=False)
                print(f"\nSUCCESS: Detailed trade records saved: {output_file}")
                
                # Add to summary results
                result_row = {
                    'asset': asset_name,
                    'timeframe': tf,
                    'n_trades': summary['n_trades'],
                    'win_rate': summary['win_rate'],
                    'avg_pnl': summary['avg_pnl'],
                    'avg_mfe': summary['mfe_mean'],
                    'avg_mae': summary['mae_mean'],
                    't_mfe_median': summary['t_mfe_median'],
                    't_mfe_mean': summary['t_mfe_mean'],
                    'profit_capture_ratio': summary['profit_capture_ratio'],
                    'avg_holding_bars': summary['holding_bars_mean']
                }
                all_results.append(result_row)

            except Exception as e:
                print(f"ERROR: Analysis failed: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

    # Save summary comparison table
    if all_results:
        print(f"\n{'=' * 80}")
        print("Generating Summary Comparison Table")
        print(f"{'=' * 80}\n")

        comparison_df = pd.DataFrame(all_results)

        # Save CSV
        output_file = 'results/all_assets_trade_path_comparison.csv'
        comparison_df.to_csv(output_file, index=False)
        print(f"SUCCESS: Summary comparison table saved: {output_file}")

        # Print summary table
        print(f"\n{'=' * 80}")
        print("All Assets Trade Path Analysis Summary")
        print(f"{'=' * 80}\n")
        print(comparison_df.to_string(index=False))

    print(f"\n{'=' * 80}")
    print("SUCCESS: All analysis complete!")
    print(f"{'=' * 80}\n")

if __name__ == '__main__':
    main()

