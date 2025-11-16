"""
Complete BTC Analysis Pipeline
Run the same analysis as XAUUSD on BTC data
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from src.data.bar_builder import build_bars, resample_bars_from_lower_tf
from src.features.manipscore_model import fit_manipscore_model, apply_manipscore

print("=" * 80)
print("BTC Complete Analysis Pipeline")
print("=" * 80)
print()

# Step 1: Load BTC tick data
print("Step 1: Loading BTC tick data...")
print("-" * 80)

# Use a subset of data for initial testing (2024 only, ~1 year)
start_date = '2024-01-01'
end_date = '2024-12-31'

print(f"Date range: {start_date} to {end_date}")
print("Loading tick data (this may take a while)...")

# Load manually from parquet files
data_dir = Path('data/symbol=BTCUSD')
date_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])

# Filter by date range
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

print(f"Concatenating {len(dfs)} dataframes...")
ticks = pd.concat(dfs, ignore_index=True)

# Adapt columns
if 'ts' in ticks.columns:
    ticks = ticks.rename(columns={'ts': 'timestamp'})

# Compute mid price and volume
ticks['price'] = (ticks['bid'] + ticks['ask']) / 2
ticks['volume'] = ticks['bid_size'] + ticks['ask_size']
ticks['spread'] = ticks['ask'] - ticks['bid']

# Sort by timestamp
print("Sorting by timestamp...")
ticks = ticks.sort_values('timestamp').reset_index(drop=True)

print(f"OK Loaded {len(ticks):,} ticks")
print(f"   Time range: {ticks['timestamp'].min()} to {ticks['timestamp'].max()}")
print()

# Step 2: Build 5-minute bars
print("Step 2: Building 5-minute bars from ticks...")
print("-" * 80)

bars_5min = build_bars(ticks, bar_size='5min', source_type='ticks')

print(f"OK Built {len(bars_5min):,} 5-minute bars")
print(f"   Columns: {bars_5min.columns.tolist()}")
print()

# Save 5min bars
output_file = Path('results/bars_5min_btc_with_features.csv')
bars_5min.to_csv(output_file)
print(f"Saved to {output_file}")
print()

# Step 3: Fit ManipScore model on 5min bars
print("Step 3: Fitting ManipScore model...")
print("-" * 80)

model_5min = fit_manipscore_model(bars_5min, bar_size='5min')
bars_5min = apply_manipscore(bars_5min, model_5min)

print(f"OK ManipScore model fitted")
print(f"   Features: {model_5min.feature_cols}")
print(f"   Residual std: {model_5min.residual_std:.6f}")
print()

# Save 5min bars with ManipScore
output_file = Path('results/bars_5min_btc_with_manipscore_full.csv')
bars_5min.to_csv(output_file)
print(f"Saved to {output_file}")
print()

# Step 4: Build higher timeframe bars
print("Step 4: Building higher timeframe bars...")
print("-" * 80)

timeframes = {
    '15min': '15min',
    '30min': '30min',
    '60min': '60min',
    '4h': '4H',
    '1d': '1D'
}

bars_dict = {'5min': bars_5min}

for name, bar_size in timeframes.items():
    print(f"Building {name} bars...")
    bars = resample_bars_from_lower_tf(bars_5min, target_bar_size=bar_size)

    # Fit ManipScore model with lower min_samples for daily
    min_samples = 100 if name == '1d' else 1000

    try:
        model = fit_manipscore_model(bars, bar_size=name, min_samples=min_samples)
        bars = apply_manipscore(bars, model)

        bars_dict[name] = bars

        # Save
        output_file = Path(f'results/bars_{name}_btc_with_manipscore_full.csv')
        bars.to_csv(output_file)

        print(f"  OK {len(bars):,} bars, residual_std={model.residual_std:.6f}, saved to {output_file.name}")
    except ValueError as e:
        print(f"  SKIP {name}: {e}")

print()
print("OK All timeframes processed and saved!")
print()

print("=" * 80)
print("BTC data processing complete!")
print("=" * 80)
print()
print("Next step: Run backtest analysis")
print("Execute: python btc_backtest_all_timeframes.py")

