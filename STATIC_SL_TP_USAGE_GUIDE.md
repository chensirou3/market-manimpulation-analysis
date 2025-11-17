# Static SL/TP Backtest System - Usage Guide

## 📚 Overview

This system implements a comprehensive static stop-loss (SL) and take-profit (TP) backtesting framework for long-only trading strategies. It allows you to:

1. Test different SL/TP parameters based on ATR multiples
2. Optimize maximum holding periods
3. Compare performance across multiple assets and timeframes
4. Generate detailed performance metrics and visualizations

---

## 🏗️ System Architecture

### Core Components

```
src/backtest/
├── static_exit_backtest.py    # Core backtest engine
│   ├── StaticExitConfig       # Configuration dataclass
│   ├── run_static_exit_backtest()  # Main backtest function
│   ├── compute_atr()          # ATR calculation
│   └── compute_backtest_stats()    # Performance metrics

experiments/
├── static_sl_tp_grid_4h.py    # 4H grid search script

examples/
├── static_exit_example.py     # Usage example

visualize_static_sl_tp_results.py  # Results visualization
```

---

## 🚀 Quick Start

### 1. Run Example (Single Configuration)

```bash
cd market-manimpulation-analysis
python examples/static_exit_example.py
```

This will:
- Load XAUUSD 4H data
- Generate long-only signals
- Run backtest with SL=2.0, TP=1.5, MaxBars=20
- Display detailed results

### 2. Run Grid Search (All Configurations)

```bash
python experiments/static_sl_tp_grid_4h.py
```

This will:
- Test XAUUSD, BTCUSD, ETHUSD on 4H timeframe
- Run 192 combinations (64 per asset)
- Save results to `results/static_sl_tp_grid_4h_summary.csv`
- Display top 20 configurations

### 3. Visualize Results

```bash
python visualize_static_sl_tp_results.py
```

This will:
- Generate comprehensive visualization
- Save to `results/static_sl_tp_grid_4h_analysis.png`
- Print detailed summary by asset

---

## 💻 Code Examples

### Example 1: Basic Usage

```python
from src.backtest.static_exit_backtest import (
    StaticExitConfig,
    run_static_exit_backtest,
    compute_atr
)
from src.strategies.extreme_reversal import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals
)

# Load data
bars = pd.read_csv("results/bars_4h_with_manipscore_full.csv",
                   parse_dates=['timestamp']).set_index('timestamp')

# Compute ATR
atr = compute_atr(bars, window=10)

# Generate signals
strategy_config = ExtremeReversalConfig(
    bar_size="4h",
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9
)

df_with_signals = generate_extreme_reversal_signals(
    bars, strategy_config, return_col='returns', manip_col='ManipScore'
)
signal_exec = (df_with_signals['exec_signal'] == 1).astype(int)

# Run backtest
config = StaticExitConfig(
    bar_size="4h",
    sl_atr_mult=2.0,
    tp_atr_mult=1.5,
    max_holding_bars=20,
    cost_per_trade=0.0007
)

result = run_static_exit_backtest(bars, signal_exec, atr, config)

# Access results
print(result['stats'])
print(result['trades'].head())
result['equity_curve'].plot()
```

### Example 2: Custom Grid Search

```python
import pandas as pd
from itertools import product

# Define custom grid
SL_MULTS = [2.0, 2.5, 3.0]
TP_MULTS = [1.0, 1.5, 2.0]
MAX_HOLDING_BARS = [15, 20, 25]

results = []

for sl, tp, max_bars in product(SL_MULTS, TP_MULTS, MAX_HOLDING_BARS):
    config = StaticExitConfig(
        bar_size="4h",
        sl_atr_mult=sl,
        tp_atr_mult=tp,
        max_holding_bars=max_bars,
        cost_per_trade=0.0007
    )
    
    result = run_static_exit_backtest(bars, signal_exec, atr, config)
    
    results.append({
        'sl_mult': sl,
        'tp_mult': tp,
        'max_holding_bars': max_bars,
        **result['stats']
    })

df_results = pd.DataFrame(results)
print(df_results.nlargest(10, 'sharpe'))
```

### Example 3: Analyze Trade Details

```python
result = run_static_exit_backtest(bars, signal_exec, atr, config)
trades_df = result['trades']

# Exit reason breakdown
print(trades_df['exit_reason'].value_counts())

# Winners vs Losers
winners = trades_df[trades_df['pnl_pct'] > 0]
losers = trades_df[trades_df['pnl_pct'] <= 0]

print(f"Winners: {len(winners)} ({len(winners)/len(trades_df)*100:.1f}%)")
print(f"Avg Winner: {winners['pnl_pct'].mean():.2%}")
print(f"Avg Loser: {losers['pnl_pct'].mean():.2%}")

# Holding period analysis
print(f"Avg Holding: {trades_df['holding_bars'].mean():.1f} bars")
print(f"Max Holding: {trades_df['holding_bars'].max()} bars")
```

---

## 📊 Output Files

### 1. Grid Search Results CSV

**File**: `results/static_sl_tp_grid_4h_summary.csv`

**Columns**:
- `symbol`: Asset name (XAUUSD, BTCUSD, ETHUSD)
- `timeframe`: Timeframe (4h)
- `sl_mult`: Stop-loss multiplier
- `tp_mult`: Take-profit multiplier
- `max_holding_bars`: Maximum holding period
- `total_return`: Total return over backtest period
- `ann_return`: Annualized return
- `ann_vol`: Annualized volatility
- `sharpe`: Sharpe ratio
- `max_drawdown`: Maximum drawdown
- `num_trades`: Number of trades
- `win_rate`: Win rate (%)
- `avg_pnl_per_trade`: Average PnL per trade
- `avg_winner`: Average winning trade
- `avg_loser`: Average losing trade
- `profit_factor`: Profit factor

### 2. Visualization

**File**: `results/static_sl_tp_grid_4h_analysis.png`

**Includes**:
- Sharpe ratio heatmaps (SL vs TP) for each asset
- Return vs Drawdown scatter plot
- Sharpe vs Max Holding Bars line chart
- Win rate distribution histogram
- SL/TP ratio vs Sharpe scatter
- Profit factor distribution
- Best configuration summary table

---

## ⚙️ Configuration Parameters

### StaticExitConfig

```python
@dataclass
class StaticExitConfig:
    bar_size: str              # Timeframe ('4h', '1d', etc.)
    sl_atr_mult: float         # Stop-loss as ATR multiple (e.g., 2.0)
    tp_atr_mult: float         # Take-profit as ATR multiple (e.g., 1.5)
    max_holding_bars: int      # Maximum bars to hold (e.g., 20)
    cost_per_trade: float = 0.0007  # Transaction cost (default 7bp)
```

### Recommended Ranges

| Parameter | Min | Max | Typical | Notes |
|-----------|-----|-----|---------|-------|
| `sl_atr_mult` | 1.0 | 5.0 | 2.0-3.0 | Wider stops for noisy assets |
| `tp_atr_mult` | 0.5 | 3.0 | 1.0-2.0 | Tighter TP for quick profits |
| `max_holding_bars` | 5 | 50 | 10-20 | Based on t_mfe analysis |
| `cost_per_trade` | 0.0001 | 0.01 | 0.0007 | 1bp-100bp range |

---

## 📈 Performance Metrics

### Key Metrics Explained

1. **Sharpe Ratio**: Risk-adjusted return (higher is better)
   - \> 1.0: Excellent
   - 0.5-1.0: Good
   - 0-0.5: Acceptable
   - < 0: Poor

2. **Max Drawdown**: Largest peak-to-trough decline
   - < 20%: Low risk
   - 20-40%: Moderate risk
   - \> 40%: High risk

3. **Win Rate**: Percentage of profitable trades
   - \> 55%: High
   - 45-55%: Medium
   - < 45%: Low

4. **Profit Factor**: Gross profit / Gross loss
   - \> 1.5: Excellent
   - 1.2-1.5: Good
   - 1.0-1.2: Acceptable
   - < 1.0: Losing

---

## 🔧 Customization

### Add New Asset

1. Prepare data file: `results/bars_4h_{symbol}_full_with_manipscore.csv`
2. Add to `SYMBOLS_4H` list in `experiments/static_sl_tp_grid_4h.py`
3. Update `symbol_map` in `load_bars()` function

### Add New Timeframe

1. Prepare data files for all assets
2. Update `get_bars_per_year()` in `static_exit_backtest.py`
3. Create new experiment script (e.g., `static_sl_tp_grid_1d.py`)

### Modify Grid Parameters

Edit in `experiments/static_sl_tp_grid_4h.py`:
```python
SL_MULTS = [1.5, 2.0, 2.5, 3.0, 3.5]  # Add 3.5
TP_MULTS = [0.8, 1.0, 1.2, 1.5, 2.0]  # Add 0.8, 1.2
MAX_HOLDING_BARS = [8, 12, 16, 20, 24]  # Custom values
```

---

## 🐛 Troubleshooting

### Issue: "FileNotFoundError: Could not find data file"

**Solution**: Check file naming pattern in `load_bars()` function. Ensure data files exist in `results/` directory.

### Issue: "No signal column found"

**Solution**: Verify signal generation returns `exec_signal` or `raw_signal` column.

### Issue: "Negative Sharpe for all configurations"

**Solution**: 
- Check signal quality (win rate, avg PnL)
- Verify transaction costs are reasonable
- Consider different strategy parameters

---

## 📚 Further Reading

- **Trade Path Analysis Report**: `XAUUSD_全时间周期交易路径分析报告.md`
- **Strategy Documentation**: `策略逻辑完整说明.md`
- **Project Progress**: `PROJECT_PROGRESS.md`

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0  
**Author**: Market Manipulation Analysis Team

