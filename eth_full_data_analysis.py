"""
ETH Complete Analysis - Process Full Dataset (2017-2025) in Yearly Batches

This script processes ETH data year by year to avoid memory issues,
then combines the results for final analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.data.bar_builder import build_bars, resample_bars_from_lower_tf
from src.features.manipscore_model import fit_manipscore_model, apply_manipscore

print("=" * 80)
print("ETH Full Dataset Analysis (2017-2025) - Yearly Batch Processing")
print("=" * 80)

# Process each year separately
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
all_bars_5min = []

for year in years:
    print(f"\n{'=' * 80}")
    print(f"Processing Year: {year}")
    print("=" * 80)
    
    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    
    print(f"Date range: {start_date} to {end_date}")
    print("Loading tick data...")
    
    # Load tick data for this year
    data_dir = Path('data/symbol=ETHUSD')
    date_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    dfs = []
    count = 0
    for date_dir in date_dirs:
        date_str = date_dir.name.replace('date=', '')
        try:
            date_dt = pd.to_datetime(date_str)
        except:
            continue
        
        if start_dt <= date_dt <= end_dt:
            parquet_files = list(date_dir.glob('*.parquet'))
            for f in parquet_files:
                df = pd.read_parquet(f)
                dfs.append(df)
                count += 1
                if count % 50 == 0:
                    print(f"  Loaded {count} files...")
    
    if len(dfs) == 0:
        print(f"  No data found for {year}, skipping...")
        continue
    
    print(f"Concatenating {len(dfs)} dataframes...")
    ticks = pd.concat(dfs, ignore_index=True)
    del dfs  # Free memory
    
    print(f"Total ticks: {len(ticks):,}")
    
    # Ensure timestamp column exists and set as index
    if 'ts' in ticks.columns:
        ticks['timestamp'] = pd.to_datetime(ticks['ts'])
        ticks = ticks.set_index('timestamp').sort_index()
    elif 'timestamp' in ticks.columns:
        ticks['timestamp'] = pd.to_datetime(ticks['timestamp'])
        ticks = ticks.set_index('timestamp').sort_index()
    
    # Build 5-minute bars
    print("Building 5-minute bars...")
    bars_5min = build_bars(ticks, bar_size='5min', source_type='ticks')
    del ticks  # Free memory
    
    print(f"5-minute bars: {len(bars_5min):,}")
    
    # Store for later combination
    all_bars_5min.append(bars_5min)
    
    print(f"Year {year} complete!")

# Combine all years
print("\n" + "=" * 80)
print("Combining All Years")
print("=" * 80)

bars_5min_full = pd.concat(all_bars_5min, ignore_index=False)
bars_5min_full = bars_5min_full.sort_index()
del all_bars_5min  # Free memory

print(f"Total 5-minute bars: {len(bars_5min_full):,}")
print(f"Date range: {bars_5min_full.index[0]} to {bars_5min_full.index[-1]}")

# Fit ManipScore model for 5min
print("\nFitting ManipScore model for 5min...")
model_5min = fit_manipscore_model(bars_5min_full, bar_size='5min')
bars_5min_full = apply_manipscore(bars_5min_full, model_5min)
print(f"  Residual std: {model_5min.residual_std:.6f}")

# Save 5min bars
output_path = 'results/bars_5min_eth_full_with_manipscore.csv'
bars_5min_full.to_csv(output_path)
print(f"Saved: {output_path}")

# Process higher timeframes
timeframes = {
    '15min': '15min',
    '30min': '30min',
    '60min': '1H',
    '4h': '4H',
    '1d': '1D'
}

for tf_name, tf_code in timeframes.items():
    print(f"\n{'=' * 80}")
    print(f"Processing {tf_name} timeframe")
    print("=" * 80)
    
    # Resample from 5min
    print(f"Resampling from 5min to {tf_name}...")
    bars = resample_bars_from_lower_tf(bars_5min_full, target_bar_size=tf_code)
    print(f"  {tf_name} bars: {len(bars):,}")
    
    # Fit ManipScore model
    print(f"Fitting ManipScore model for {tf_name}...")
    min_samples = 100 if tf_name == '1d' else 1000
    model = fit_manipscore_model(bars, bar_size=tf_name, min_samples=min_samples)
    bars = apply_manipscore(bars, model)
    print(f"  Residual std: {model.residual_std:.6f}")
    
    # Save
    output_path = f'results/bars_{tf_name}_eth_full_with_manipscore.csv'
    bars.to_csv(output_path)
    print(f"Saved: {output_path}")

print("\n" + "=" * 80)
print("ETH Full Dataset Processing Complete!")
print("=" * 80)
print("\nGenerated files:")
print("  - results/bars_5min_eth_full_with_manipscore.csv")
print("  - results/bars_15min_eth_full_with_manipscore.csv")
print("  - results/bars_30min_eth_full_with_manipscore.csv")
print("  - results/bars_60min_eth_full_with_manipscore.csv")
print("  - results/bars_4h_eth_full_with_manipscore.csv")
print("  - results/bars_1d_eth_full_with_manipscore.csv")

