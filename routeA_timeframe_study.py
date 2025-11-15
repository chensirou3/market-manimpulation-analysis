"""
Route A: Timeframe Study

Rebuild the entire analysis and strategy for higher timeframes (15m, 30m, 1h).

For each timeframe:
1. Build bars from existing 5m data
2. Fit ManipScore model at that timeframe
3. Run empirical reversal analysis
4. Run strategy backtest
5. Generate reports

Finally, produce a consolidated comparison across all timeframes.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.data import resample_bars_from_lower_tf
from src.features import fit_manipscore_model, apply_manipscore
from src.strategies import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals,
    run_extreme_reversal_backtest
)


# ============================================================================
# Configuration
# ============================================================================

BAR_SIZES = ["5min", "15min", "30min", "60min"]

# Base configuration (will be adapted for each timeframe)
BASE_CONFIG = ExtremeReversalConfig(
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.90,
    use_normalized_trend=True,
    min_abs_R_past=0.003,
    q_manip=0.90,
    min_manip_score=0.7,
    holding_horizon=5,
    atr_window=10,
    sl_atr_mult=0.5,
    tp_atr_mult=0.8,
    cost_per_trade=0.0001
)


# ============================================================================
# Step 1: Load and prepare 5min baseline data
# ============================================================================

def load_5min_data():
    """Load all 5min bars with ManipScore"""
    print("="*80)
    print("Loading 5min baseline data")
    print("="*80)
    
    results_dir = Path('results')
    files_5min = sorted(results_dir.glob('bars_with_manipscore_*.csv'))
    
    print(f"Found {len(files_5min)} 5min data files")
    
    dfs = []
    for i, file in enumerate(files_5min, 1):
        if i % 10 == 0:
            print(f"  Loading: {i}/{len(files_5min)}")
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars_5min = pd.concat(dfs, axis=0)
    bars_5min = bars_5min.sort_index()
    
    print(f"Loaded {len(bars_5min):,} 5min bars")
    print(f"Date range: {bars_5min.index[0]} to {bars_5min.index[-1]}")
    print()
    
    return bars_5min


# ============================================================================
# Step 2: Build bars at target timeframe
# ============================================================================

def build_bars_for_timeframe(bars_5min, bar_size):
    """Resample 5min bars to target timeframe"""
    print(f"Building {bar_size} bars from 5min data...")
    
    if bar_size == "5min":
        # Already have 5min data
        return bars_5min.copy()
    
    # Resample to higher timeframe
    bars_tf = resample_bars_from_lower_tf(bars_5min, bar_size)
    
    print(f"  Created {len(bars_tf):,} {bar_size} bars")
    
    return bars_tf


# ============================================================================
# Step 3: Fit and apply ManipScore model
# ============================================================================

def compute_manipscore_for_timeframe(bars, bar_size):
    """Fit ManipScore model and apply to bars"""
    print(f"Computing ManipScore for {bar_size}...")
    
    # Fit model
    model = fit_manipscore_model(bars, bar_size)
    
    print(f"  Fitted model with features: {model.feature_cols}")
    print(f"  Residual std: {model.residual_std:.6f}")
    
    # Apply model
    bars_with_manip = apply_manipscore(bars, model)
    
    n_valid = bars_with_manip['ManipScore'].notna().sum()
    print(f"  ManipScore computed for {n_valid:,} bars")
    
    return bars_with_manip, model


# ============================================================================
# Step 4: Save bars with ManipScore
# ============================================================================

def save_bars_by_timeframe(bars, bar_size):
    """Save bars to CSV files by quarter"""
    print(f"Saving {bar_size} bars...")
    
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Group by quarter
    bars['year'] = bars.index.year
    bars['quarter'] = bars.index.quarter
    
    saved_files = []
    for (year, quarter), group in bars.groupby(['year', 'quarter']):
        # Determine quarter date range
        if quarter == 1:
            start_date = f"{year}-01-01"
            end_date = f"{year}-03-31"
        elif quarter == 2:
            start_date = f"{year}-04-01"
            end_date = f"{year}-06-30"
        elif quarter == 3:
            start_date = f"{year}-07-01"
            end_date = f"{year}-09-30"
        else:
            start_date = f"{year}-10-01"
            end_date = f"{year}-12-31"
        
        filename = f"bars_{bar_size}_with_manipscore_{start_date}_{end_date}.csv"
        filepath = results_dir / filename
        
        # Drop temporary columns
        group_save = group.drop(columns=['year', 'quarter'], errors='ignore')
        group_save.to_csv(filepath)
        saved_files.append(filename)
    
    print(f"  Saved {len(saved_files)} files")
    
    return saved_files


# ============================================================================
# Step 5: Empirical reversal analysis
# ============================================================================

def analyze_reversal_probability(bars, bar_size, horizons=[1, 3, 5]):
    """
    Analyze reversal probability after extreme trend + high ManipScore.

    Returns:
        DataFrame with reversal statistics
    """
    print(f"Analyzing reversal probability for {bar_size}...")

    from src.strategies import compute_trend_strength, compute_extreme_trend_thresholds

    # Compute trend features
    bars_analysis = compute_trend_strength(
        bars.copy(),
        L_past=5,
        vol_window=20
    )

    # Compute thresholds
    thresholds = compute_extreme_trend_thresholds(
        bars_analysis,
        quantile=0.90,
        use_normalized=True,
        min_abs_R_past=0.003
    )

    # Identify extreme trends based on TS (normalized trend strength)
    threshold_val = thresholds['threshold']
    extreme_up = (bars_analysis['R_past'] > 0) & (bars_analysis['abs_TS'] >= threshold_val)
    extreme_down = (bars_analysis['R_past'] < 0) & (bars_analysis['abs_TS'] >= threshold_val)

    # Apply minimum absolute R_past filter if specified
    if thresholds['min_abs_R_past'] is not None:
        min_R = thresholds['min_abs_R_past']
        extreme_up = extreme_up & (bars_analysis['abs_R_past'] >= min_R)
        extreme_down = extreme_down & (bars_analysis['abs_R_past'] >= min_R)

    # High ManipScore
    manip_threshold = bars_analysis['ManipScore'].quantile(0.90)
    high_manip = bars_analysis['ManipScore'] >= manip_threshold

    # Compute future returns
    results = []
    for H in horizons:
        future_ret = bars_analysis['returns'].shift(-H).rolling(H).sum()

        # Extreme UP + high manip (expect reversal DOWN)
        mask_up = extreme_up & high_manip
        if mask_up.sum() > 0:
            avg_ret_up = future_ret[mask_up].mean()
            reversal_prob_up = (future_ret[mask_up] < 0).mean()
        else:
            avg_ret_up = np.nan
            reversal_prob_up = np.nan

        # Extreme DOWN + high manip (expect reversal UP)
        mask_down = extreme_down & high_manip
        if mask_down.sum() > 0:
            avg_ret_down = future_ret[mask_down].mean()
            reversal_prob_down = (future_ret[mask_down] > 0).mean()
        else:
            avg_ret_down = np.nan
            reversal_prob_down = np.nan

        # Combined reversal probability
        mask_any = mask_up | mask_down
        if mask_any.sum() > 0:
            # For UP moves, reversal = negative return
            # For DOWN moves, reversal = positive return
            reversal_up_count = ((future_ret < 0) & mask_up).sum()
            reversal_down_count = ((future_ret > 0) & mask_down).sum()
            total_reversal = reversal_up_count + reversal_down_count
            reversal_prob_combined = total_reversal / mask_any.sum()
        else:
            reversal_prob_combined = np.nan

        results.append({
            'bar_size': bar_size,
            'horizon': H,
            'n_extreme_up_highmanip': mask_up.sum(),
            'n_extreme_down_highmanip': mask_down.sum(),
            'n_total': mask_any.sum(),
            'reversal_prob_up': reversal_prob_up,
            'reversal_prob_down': reversal_prob_down,
            'reversal_prob_combined': reversal_prob_combined,
            'avg_future_ret_up': avg_ret_up,
            'avg_future_ret_down': avg_ret_down,
        })

    df_results = pd.DataFrame(results)

    print(f"  Analyzed {horizons} bar horizons")
    print(f"  Total extreme+highmanip events: {df_results['n_total'].iloc[0]}")

    return df_results


# ============================================================================
# Step 6: Run strategy backtest
# ============================================================================

def run_strategy_backtest(bars, bar_size):
    """Run Extreme Reversal strategy backtest"""
    print(f"Running strategy backtest for {bar_size}...")

    # Create config for this timeframe
    config = ExtremeReversalConfig(
        bar_size=bar_size,
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.90,
        use_normalized_trend=True,
        min_abs_R_past=0.003,
        q_manip=0.90,
        min_manip_score=0.7,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5,
        tp_atr_mult=0.8,
        cost_per_trade=0.0001
    )

    # Generate signals (specify correct ManipScore column name)
    bars_with_signals = generate_extreme_reversal_signals(
        bars.copy(),
        config,
        manip_col='ManipScore'
    )

    n_signals = (bars_with_signals['exec_signal'] != 0).sum()
    print(f"  Generated {n_signals} signals")

    if n_signals < 10:
        print(f"  ⚠️ Too few signals, skipping backtest")
        return None, None

    # Run backtest
    result = run_extreme_reversal_backtest(
        bars_with_signals,
        bars_with_signals['exec_signal'],
        config,
        initial_capital=10000.0
    )

    print(f"  Total return: {result.stats['total_return']*100:.2f}%")
    print(f"  Sharpe: {result.stats['sharpe_ratio']:.2f}")
    print(f"  Win rate: {result.stats['win_rate']*100:.1f}%")

    return result, config


# ============================================================================
# Step 7: Generate reports
# ============================================================================

def save_timeframe_results(bar_size, reversal_stats, backtest_result):
    """Save results for this timeframe"""
    results_dir = Path('results')

    # Save reversal stats
    reversal_file = results_dir / f"routeA_reversal_stats_{bar_size}.csv"
    reversal_stats.to_csv(reversal_file, index=False)

    # Save backtest results if available
    if backtest_result is not None:
        # Yearly results
        yearly_file = results_dir / f"extreme_reversal_yearly_results_{bar_size}.csv"
        # (Would need to implement yearly breakdown - for now just save summary)

        # Summary
        summary_file = results_dir / f"extreme_reversal_summary_{bar_size}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Extreme Reversal Strategy - {bar_size}\n\n")
            f.write(f"## Performance Summary\n\n")
            for key, value in backtest_result.stats.items():
                f.write(f"- {key}: {value}\n")

    print(f"  Results saved for {bar_size}")


# ============================================================================
# Main execution
# ============================================================================

def main():
    """Main execution"""
    print("="*80)
    print("Route A: Timeframe Study")
    print("="*80)
    print()
    print(f"Timeframes to study: {BAR_SIZES}")
    print()

    # Load 5min baseline
    bars_5min = load_5min_data()

    # Process each timeframe
    all_reversal_stats = []
    all_backtest_stats = []

    for bar_size in BAR_SIZES:
        print()
        print("="*80)
        print(f"Processing {bar_size}")
        print("="*80)
        print()

        # Build bars
        bars = build_bars_for_timeframe(bars_5min, bar_size)

        # Compute ManipScore
        bars_with_manip, model = compute_manipscore_for_timeframe(bars, bar_size)

        # Save bars
        saved_files = save_bars_by_timeframe(bars_with_manip, bar_size)

        # Empirical analysis
        reversal_stats = analyze_reversal_probability(bars_with_manip, bar_size)
        all_reversal_stats.append(reversal_stats)

        # Strategy backtest
        backtest_result, config = run_strategy_backtest(bars_with_manip, bar_size)

        if backtest_result is not None:
            backtest_summary = {
                'bar_size': bar_size,
                **backtest_result.stats
            }
            all_backtest_stats.append(backtest_summary)

        # Save results
        save_timeframe_results(bar_size, reversal_stats, backtest_result)

        print()
        print(f"✅ {bar_size} processing complete")
        print()

    # Generate consolidated comparison
    print("="*80)
    print("Generating consolidated comparison")
    print("="*80)

    # Combine all results
    df_comparison = pd.DataFrame(all_backtest_stats)
    comparison_file = Path('results') / 'routeA_timeframe_comparison.csv'
    df_comparison.to_csv(comparison_file, index=False)

    print(f"Saved: {comparison_file}")

    # Generate report
    report_file = Path('results') / 'routeA_timeframe_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Route A: Timeframe Study Report\n\n")
        f.write("## Comparison Across Timeframes\n\n")
        f.write(df_comparison.to_markdown(index=False))

    print(f"Saved: {report_file}")

    print()
    print("="*80)
    print("Route A: Timeframe Study Complete!")
    print("="*80)


if __name__ == "__main__":
    main()

