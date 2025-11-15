"""
Simple Parameter Optimization Runner
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import multiprocessing
import sys

# Set UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from parameter_optimization_simplified import (
    optimize_parameters_simplified,
    PARAM_GRID_SIMPLIFIED
)

from parameter_optimization import (
    analyze_optimization_results,
    visualize_optimization_results
)


def load_all_data():
    """Load all data"""
    print("="*80)
    print("Loading Data")
    print("="*80)
    
    results_dir = Path('results')
    all_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))
    
    print(f"Found {len(all_files)} files")
    
    dfs = []
    for i, file in enumerate(all_files, 1):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(all_files)}")
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()
    
    if 'returns' not in bars.columns and 'close' in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    print(f"Data loaded: {len(bars):,} bars")
    print(f"Date range: {bars.index[0]} to {bars.index[-1]}")
    print()
    
    return bars


def main():
    print("="*80)
    print("Simplified Parameter Optimization")
    print("="*80)
    print()
    
    # Show parameter space
    total_combinations = np.prod([len(v) for v in PARAM_GRID_SIMPLIFIED.values()])
    print(f"Total combinations: {total_combinations:,}")
    
    n_workers = max(1, multiprocessing.cpu_count() - 1)
    print(f"Parallel workers: {n_workers}")
    print(f"Estimated time: {total_combinations * 2 / n_workers / 60:.1f} minutes")
    print()
    
    # Load data
    bars = load_all_data()
    
    # Run optimization
    print("="*80)
    print("Starting Optimization")
    print("="*80)
    print()
    
    start_time = datetime.now()
    
    df_results = optimize_parameters_simplified(
        bars,
        n_workers=n_workers,
        save_interval=100
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'results/optimization_simplified_{timestamp}.csv'
    df_results.to_csv(results_file, index=False, encoding='utf-8-sig')
    
    print()
    print("="*80)
    print("Optimization Complete!")
    print("="*80)
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Speed: {len(df_results)/elapsed:.2f} tests/sec")
    print(f"Results saved: {results_file}")
    print()
    
    # Analyze
    top10_return, top10_sharpe = analyze_optimization_results(df_results)
    
    # Visualize
    visualize_optimization_results(df_results, 
                                  save_path=f'results/opt_analysis_{timestamp}.png')
    
    # Save top results
    top10_return.to_csv(f'results/top10_return_{timestamp}.csv', index=False, encoding='utf-8-sig')
    top10_sharpe.to_csv(f'results/top10_sharpe_{timestamp}.csv', index=False, encoding='utf-8-sig')
    
    # Show best
    best = df_results.loc[df_results['total_return'].idxmax()]
    
    print("="*80)
    print("Best Configuration")
    print("="*80)
    print(f"Return: {best['total_return']*100:.2f}%")
    print(f"Sharpe: {best['sharpe_ratio']:.2f}")
    print(f"Win Rate: {best['win_rate']*100:.1f}%")
    print(f"Signals: {best['n_signals']}")
    print()
    print("Parameters:")
    print(f"  q_extreme_trend = {best['q_extreme_trend']:.2f}")
    print(f"  q_manip = {best['q_manip']:.2f}")
    print(f"  holding_horizon = {int(best['holding_horizon'])}")
    print(f"  L_past = {int(best['L_past'])}")
    print(f"  min_abs_R_past = {best['min_abs_R_past']:.4f}")
    print(f"  sl_atr_mult = {best['sl_atr_mult']:.2f}")
    print(f"  tp_atr_mult = {best['tp_atr_mult']:.2f}")
    print()
    print("="*80)


if __name__ == "__main__":
    main()

