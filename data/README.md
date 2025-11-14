# Data Directory

This directory is for storing tick data and intermediate results.

**IMPORTANT**: This directory is excluded from Git (see `.gitignore`). Data files will NOT be committed to the repository.

## Expected Data Format

### Tick Data

Place your tick data files here with the naming convention:
```
{symbol}_ticks.csv
```
or
```
{symbol}_ticks.parquet
```

**CSV Format Example**:
```csv
timestamp,price,volume,side
2024-01-01 09:30:00.123,1850.25,100,buy
2024-01-01 09:30:00.456,1850.30,50,sell
2024-01-01 09:30:01.789,1850.28,75,buy
```

**Required Columns**:
- `timestamp`: datetime or parseable string
- `price`: float
- `volume`: float

**Optional Columns**:
- `side`: str ('buy' or 'sell')
- `bid`: float (best bid price)
- `ask`: float (best ask price)

## Subdirectories

You can organize your data into subdirectories:

```
data/
├── raw/              # Raw tick data
├── processed/        # Processed bar data
├── results/          # Backtest results
└── cache/            # Cached intermediate results
```

## Usage

Load tick data in your code:

```python
from src.data_prep.tick_loader import load_tick_data

# Load data
ticks = load_tick_data('XAUUSD', start_date='2024-01-01', end_date='2024-01-31')
```

## Notes

- Keep data files organized by symbol and date
- Use Parquet format for better performance with large datasets
- This directory is local to each machine - not synced via Git
- Make sure to back up your data separately

