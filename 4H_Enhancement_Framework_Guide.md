# 4H Enhancement Framework - Implementation Guide

## Overview

This framework implements and tests multi-timeframe confluence and signal clustering filters for the 4h asymmetric manipulation strategy.

## Module Structure

### 1. Core Modules (New)

#### `src/features/multitimeframe_alignment.py`
Aligns lower timeframe bars (4h) with higher timeframe bars (daily).

**Key Functions**:
```python
align_4h_with_daily(bars_4h, bars_1d) -> pd.DataFrame
    # Attaches daily regime state to each 4h bar
    # NO LOOK-AHEAD: uses previous completed daily bar
    
verify_no_lookahead(bars_4h_aligned, sample_size=10)
    # Verifies alignment has no look-ahead bias
    
get_alignment_stats(bars_4h_aligned) -> dict
    # Returns alignment statistics
```

#### `src/strategies/daily_regime.py`
Computes daily-level trend and ManipScore features.

**Key Functions**:
```python
compute_daily_trend_features(bars_1d, L_past=5, vol_window=20) -> pd.DataFrame
    # Computes: R_past, sigma, TS, abs_R_past, abs_TS
    
define_daily_extreme_regimes(bars_1d, q_extreme_trend=0.9, q_manip=0.9) -> dict
    # Returns thresholds for extreme regimes
    
identify_daily_extreme_regimes(bars_1d, thresholds) -> pd.DataFrame
    # Adds: extreme_up, extreme_down, extreme_any flags
    
get_daily_regime_stats(bars_1d) -> dict
    # Returns regime statistics
```

#### `src/strategies/clustering_features.py`
Detects clusters of high ManipScore bars.

**Key Functions**:
```python
compute_4h_clustering_features(bars_4h, q_high_manip=0.9, W=6) -> pd.DataFrame
    # Adds: high_flag, count_high, density_high
    
classify_events(bars_4h, min_count_clustered=3, max_count_isolated=1) -> pd.DataFrame
    # Adds: is_isolated, is_clustered, is_intermediate
    
get_clustering_stats(bars_4h) -> dict
    # Returns clustering statistics
    
analyze_clustering_vs_performance(bars_4h, signal_col, return_col) -> pd.DataFrame
    # Compares isolated vs clustered event performance
```

#### `src/strategies/extreme_reversal_4h_enhanced.py`
Enhanced 4h strategy with filters.

**Key Functions**:
```python
generate_asymmetric_signals(bars, config) -> pd.DataFrame
    # Generates asymmetric strategy signals
    # UP + high manip → LONG
    # DOWN + high manip → LONG
    
generate_4h_signals_with_filters(bars_4h, bars_1d, config, strategy_type='asymmetric') -> pd.DataFrame
    # Main function: generates signals with optional filters
    # strategy_type: 'asymmetric' or 'reversal'
    
apply_daily_confluence_filter(bars_4h, bars_1d, config) -> pd.DataFrame
    # Filters signals by daily regime confluence
    
apply_clustering_filter(bars_4h, config) -> pd.DataFrame
    # Filters signals by clustering
```

### 2. Extended Configuration

#### `src/strategies/extreme_reversal.py` (Extended)

**New Config Fields**:
```python
@dataclass
class ExtremeReversalConfig:
    # ... existing fields ...
    
    # Multi-timeframe filters (NEW)
    use_daily_confluence: bool = False
    daily_q_extreme_trend: float = 0.9
    daily_q_high_manip: float = 0.9
    daily_min_abs_R_past: Optional[float] = None
    
    # Clustering filters (NEW)
    use_clustering_filter: bool = False
    clustering_q_high_manip: float = 0.9
    clustering_window_W: int = 6
    clustering_min_count: int = 3
```

### 3. Experiment Scripts

#### `experiments/4h_daily_clustering_study.py`
Main experiment comparing 4 strategy variants.

**Variants**:
- A) Baseline (no filters)
- B) + Daily confluence
- C) + Clustering
- D) + Both filters

**Output**: `results/4h_filter_comparison_stats.csv`

#### `experiments/4h_parameter_sensitivity.py`
Parameter sensitivity analysis.

**Tests**:
- Clustering: 9 parameter combinations (W, min_count, q_manip)
- Daily: 6 parameter combinations (q_extreme_trend, q_high_manip)

**Output**: 
- `results/4h_clustering_sensitivity.csv`
- `results/4h_daily_sensitivity.csv`

#### `visualize_4h_enhancement_study.py`
Creates comparison plots.

**Output**:
- `results/4h_enhancement_main_comparison.png`
- `results/4h_clustering_sensitivity.png`

## Usage Examples

### Example 1: Run Main Experiment

```python
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.extreme_reversal_4h_enhanced import generate_4h_signals_with_filters
from src.strategies.backtest_reversal import run_extreme_reversal_backtest

# Load data
bars_4h = pd.read_csv('results/bars_4h_with_manipscore_full.csv', index_col=0, parse_dates=True)
bars_1d = pd.read_csv('results/bars_1d_with_manipscore_full.csv', index_col=0, parse_dates=True)

# Create config
config = ExtremeReversalConfig(
    bar_size='4h',
    L_past=5,
    vol_window=20,
    q_extreme_trend=0.9,
    q_manip=0.9,
    holding_horizon=5,
    atr_window=10,
    sl_atr_mult=0.5,
    tp_atr_mult=0.8,
    # Enable filters
    use_daily_confluence=True,
    use_clustering_filter=True,
    clustering_window_W=8,
    clustering_min_count=4,
)

# Generate signals
bars_with_signals = generate_4h_signals_with_filters(
    bars_4h,
    bars_1d,
    config,
    strategy_type='asymmetric'
)

# Run backtest
result = run_extreme_reversal_backtest(
    bars_with_signals,
    bars_with_signals['exec_signal'],
    config,
    initial_capital=10000.0
)

print(f"Sharpe: {result.stats['sharpe_ratio']:.2f}")
print(f"Total Return: {result.stats['total_return']*100:.2f}%")
```

### Example 2: Test Clustering Only

```python
config = ExtremeReversalConfig(
    bar_size='4h',
    use_clustering_filter=True,
    clustering_window_W=8,
    clustering_min_count=4,
    clustering_q_high_manip=0.90,
)

bars_with_signals = generate_4h_signals_with_filters(
    bars_4h,
    None,  # No daily bars needed
    config,
    strategy_type='asymmetric'
)
```

### Example 3: Baseline (No Filters)

```python
config = ExtremeReversalConfig(
    bar_size='4h',
    use_daily_confluence=False,
    use_clustering_filter=False,
)

bars_with_signals = generate_4h_signals_with_filters(
    bars_4h,
    None,
    config,
    strategy_type='asymmetric'
)
```

## Key Results Summary

| Strategy | Signals | Sharpe | Total Return | Win Rate |
|----------|---------|--------|--------------|----------|
| **Baseline** | **358** | **4.03** 🥇 | **13.09%** 🥇 | 43.6% |
| Optimal Clustering | 37 | 3.96 | 7.00% | 54.1% 🥇 |
| Standard Clustering | 67 | 1.58 | 3.59% | 44.8% |
| Daily Confluence | 7 | - | - | - |

**Recommendation**: Use **Baseline** (no filters) for best overall performance.

## Files Generated

### Code Modules
- `src/features/multitimeframe_alignment.py`
- `src/strategies/daily_regime.py`
- `src/strategies/clustering_features.py`
- `src/strategies/extreme_reversal_4h_enhanced.py`

### Experiment Scripts
- `experiments/4h_daily_clustering_study.py`
- `experiments/4h_parameter_sensitivity.py`
- `visualize_4h_enhancement_study.py`

### Results
- `results/4h_filter_comparison_stats.csv`
- `results/4h_clustering_sensitivity.csv`
- `results/4h_daily_sensitivity.csv`
- `results/4h_enhancement_main_comparison.png`
- `results/4h_clustering_sensitivity.png`

### Documentation
- `4H增强策略分析报告.md` (Chinese detailed report)
- `4H_Enhancement_Study_Summary.md` (English executive summary)
- `4H_Enhancement_Framework_Guide.md` (This file)

