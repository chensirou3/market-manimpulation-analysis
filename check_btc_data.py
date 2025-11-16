"""
Check BTC data availability and format
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def check_btc_data():
    """Check BTC data structure and availability"""
    
    data_dir = Path('data/symbol=BTCUSD')
    
    if not data_dir.exists():
        print("❌ BTC data directory not found!")
        return False
    
    # Get all date directories
    date_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])
    
    print(f"📁 BTC Data Directory: {data_dir}")
    print(f"📅 Date Range: {date_dirs[0].name} to {date_dirs[-1].name}")
    print(f"📊 Total Days: {len(date_dirs)}")
    print()
    
    # Try to load a sample file
    sample_dir = date_dirs[0]
    parquet_files = list(sample_dir.glob('*.parquet'))
    
    if not parquet_files:
        print("❌ No parquet files found!")
        return False
    
    print(f"📄 Sample file: {parquet_files[0]}")
    
    # Load sample data
    try:
        df_sample = pd.read_parquet(parquet_files[0])
        print(f"✅ Successfully loaded sample data")
        print(f"   Rows: {len(df_sample)}")
        print(f"   Columns: {list(df_sample.columns)}")
        print()
        print("Sample data:")
        print(df_sample.head())
        print()
        print("Data types:")
        print(df_sample.dtypes)
        print()
        
        # Check if it's 5-minute data
        if 'timestamp' in df_sample.columns:
            df_sample['timestamp'] = pd.to_datetime(df_sample['timestamp'])
            time_diffs = df_sample['timestamp'].diff().dropna()
            median_diff = time_diffs.median()
            print(f"⏱️  Median time difference: {median_diff}")
            
            if median_diff == pd.Timedelta('5 minutes'):
                print("✅ Confirmed: 5-minute bars")
            else:
                print(f"⚠️  Not 5-minute bars, median diff is {median_diff}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def estimate_total_bars():
    """Estimate total number of bars in BTC dataset"""
    
    data_dir = Path('data/symbol=BTCUSD')
    date_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])
    
    # Sample 10 random days
    sample_size = min(10, len(date_dirs))
    sample_dirs = np.random.choice(date_dirs, sample_size, replace=False)
    
    total_bars = 0
    for d in sample_dirs:
        parquet_files = list(d.glob('*.parquet'))
        for f in parquet_files:
            df = pd.read_parquet(f)
            total_bars += len(df)
    
    avg_bars_per_day = total_bars / sample_size
    estimated_total = avg_bars_per_day * len(date_dirs)
    
    print(f"📊 Estimated total bars: {estimated_total:,.0f}")
    print(f"   (Based on {sample_size} sample days)")
    print(f"   Average bars per day: {avg_bars_per_day:.0f}")
    
    # Estimate years
    bars_per_year = 365 * avg_bars_per_day
    years = estimated_total / bars_per_year
    print(f"   Estimated years of data: {years:.1f}")
    
    return estimated_total

if __name__ == '__main__':
    print("=" * 60)
    print("BTC Data Check")
    print("=" * 60)
    print()
    
    success = check_btc_data()
    
    if success:
        print()
        print("=" * 60)
        print("Estimating dataset size...")
        print("=" * 60)
        print()
        estimate_total_bars()
        print()
        print("✅ BTC data is ready for analysis!")
    else:
        print()
        print("❌ BTC data check failed!")

