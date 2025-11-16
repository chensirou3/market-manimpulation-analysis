"""Check XAUUSD data format"""
import pandas as pd
from pathlib import Path

xau_file = Path('data/symbol=XAUUSD/date=2015-01-01/XAUUSD_2015-01-01.parquet')
df = pd.read_parquet(xau_file)

print("XAUUSD columns:", df.columns.tolist())
print("\nSample data:")
print(df.head())
print("\nData types:")
print(df.dtypes)

