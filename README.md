# XAUUSD Market Manipulation Strategy Research

A comprehensive quantitative research project for detecting and exploiting market manipulation patterns in XAUUSD (Gold) using microstructure anomalies.

## 🎯 Project Summary

**Asset**: XAUUSD (Gold)
**Data Period**: 2015-2025 (11 years)
**Data Points**: 761,279 5-minute bars
**Best Strategy**: 4H Asymmetric + SL/TP
**Performance**: Sharpe 4.03, 13.09% total return, 358 trades

## 🏆 Key Achievement

After extensive testing across **6 timeframes**, **3 strategy types**, and **multiple enhancement filters**, we identified an optimal trading strategy:

**4-Hour Asymmetric Strategy with Stop-Loss/Take-Profit**
- **Sharpe Ratio**: 4.03 (exceptional risk-adjusted return)
- **Total Return**: 13.09% over 11 years
- **Win Rate**: 43.6%
- **Max Drawdown**: -7.40%
- **Trade Frequency**: ~33 trades/year

**Key Insight**: Market manipulation patterns unfold over multi-day horizons (4H timeframe), and asymmetric signal logic (UP=continuation, DOWN=reversal) captures these dynamics better than pure reversal strategies.

## 📖 Research Overview

This project implements a complete quantitative research pipeline:

1. **ManipScore Model**: Microstructure anomaly detection using regression residuals
2. **Multi-Timeframe Analysis**: Testing 5min, 15min, 30min, 60min, 4H, daily
3. **Strategy Type Comparison**: Reversal vs Continuation vs Asymmetric
4. **Enhancement Filters**: Daily confluence and signal clustering
5. **Parameter Optimization**: Extensive sensitivity analysis

### Research Phases

- ✅ **Phase 1**: Foundation (5min baseline) - Sharpe 0.61
- ✅ **Phase 2**: Multi-timeframe (15/30/60min) - Best: 30min Sharpe 1.16
- ✅ **Phase 3**: Strategy types (asymmetric discovery) - 15min pure Sharpe 1.43
- ✅ **Phase 4**: Extended timeframes (4H/daily) - **4H Sharpe 4.03** 🏆
- ✅ **Phase 5**: Enhancement filters - Baseline remains optimal

### Key Findings

1. **Timeframe Matters**: 4H perfectly captures multi-day manipulation cycles
2. **Asymmetric > Reversal**: Different dynamics in UP vs DOWN moves
3. **Simpler is Better**: Baseline outperforms all enhanced variants
4. **SL/TP is Timeframe-Dependent**: Current params (0.5/0.8 ATR) optimal for 4H only

## 📁 Project Structure

```
market-manimpulation-analysis/
├── data/                          # Raw tick data (NOT in Git)
│   └── symbol=XAUUSD/            # XAUUSD 5-minute bars (2015-2025)
├── src/
│   ├── data/                     # Data processing
│   │   └── bar_builder.py        # Multi-timeframe bar aggregation
│   ├── features/                 # Feature engineering
│   │   ├── manipscore_model.py   # ManipScore calculation
│   │   └── multitimeframe_alignment.py  # Timeframe alignment
│   ├── strategies/               # Trading strategies
│   │   ├── trend_features.py     # Trend strength calculation
│   │   ├── extreme_reversal.py   # Core strategy logic
│   │   ├── extreme_reversal_4h_enhanced.py  # Enhanced 4H strategy
│   │   ├── daily_regime.py       # Daily regime features
│   │   ├── clustering_features.py # Signal clustering
│   │   └── backtest_reversal.py  # Backtest engine
│   ├── visualization/            # Plotting tools
│   │   └── plots_reversal.py     # Strategy visualization
│   └── utils/                    # Utilities
├── experiments/                   # Research experiments
│   ├── 4h_daily_clustering_study.py      # Enhancement filters
│   └── 4h_parameter_sensitivity.py       # Parameter optimization
├── results/                       # Backtest results & plots
│   ├── bars_*_with_manipscore_full.csv  # Processed bars
│   ├── *_results.csv             # Backtest statistics
│   └── *.png                     # Visualization plots
├── docs/                         # Documentation
│   ├── PROJECT_PROGRESS_REPORT.md        # Complete research report
│   ├── 4H_Enhancement_Study_Summary.md   # Enhancement study
│   └── 4H_Enhancement_Framework_Guide.md # Implementation guide
└── *.py                          # Main experiment scripts
```

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10+
# Required packages: pandas, numpy, matplotlib, seaborn, scipy
pip install -r requirements.txt
```

### Run Complete Research Pipeline

```bash
# 1. Test all timeframes (5min to daily)
python extended_timeframe_backtest.py

# 2. Test enhancement filters
python experiments/4h_daily_clustering_study.py

# 3. Parameter sensitivity analysis
python experiments/4h_parameter_sensitivity.py

# 4. Generate visualizations
python visualize_4h_enhancement_study.py
```

### Use the Optimal Strategy

```python
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.extreme_reversal_4h_enhanced import generate_4h_signals_with_filters
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
import pandas as pd

# Load 4H bars with ManipScore
bars_4h = pd.read_csv('results/bars_4h_with_manipscore_full.csv',
                      index_col=0, parse_dates=True)

# Configure optimal strategy
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
)

# Generate signals (asymmetric strategy)
bars_with_signals = generate_4h_signals_with_filters(
    bars_4h, None, config, strategy_type='asymmetric'
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

## 📊 Performance Summary

### All Timeframes Tested (Asymmetric Strategy + SL/TP)

| Timeframe | Sharpe | Total Return | Win Rate | Trades | Status |
|-----------|--------|--------------|----------|--------|--------|
| 5min | 0.01 | 0.10% | 50.0% | 5,979 | ❌ Poor |
| 15min | 0.31 | 5.48% | 51.6% | 2,785 | ⚠️ Mediocre |
| 30min | 0.62 | 10.80% | 51.4% | 2,785 | ✅ Good |
| 60min | 1.65 | 14.31% | 42.1% | 716 | ✅ Very Good |
| **4h** | **4.03** | **13.09%** | **43.6%** | **358** | **🏆 Optimal** |
| 1d | -2.73 | -13.23% | 31.1% | 75 | ❌ Poor |

### Enhancement Filters (4H Baseline)

| Filter | Signals | Sharpe | Return | Win Rate | Recommendation |
|--------|---------|--------|--------|----------|----------------|
| **None (Baseline)** | **358** | **4.03** | **13.09%** | **43.6%** | **✅ Use This** |
| Daily Confluence | 7 | - | - | - | ❌ Too restrictive |
| Clustering (std) | 67 | 1.58 | 3.59% | 44.8% | ❌ Degrades performance |
| Clustering (optimal) | 37 | 3.96 | 7.00% | 54.1% | ⚠️ Alternative |

## 📚 Documentation

### Main Reports
- **[PROJECT_PROGRESS_REPORT.md](PROJECT_PROGRESS_REPORT.md)** - Complete research report with all phases
- **[4H_Enhancement_Study_Summary.md](4H_Enhancement_Study_Summary.md)** - Enhancement filters analysis
- **[4H_Enhancement_Framework_Guide.md](4H_Enhancement_Framework_Guide.md)** - Implementation guide

### Chinese Reports
- **[全时间周期对比分析.md](全时间周期对比分析.md)** - All timeframes comparison
- **[非对称策略完整分析报告.md](非对称策略完整分析报告.md)** - Asymmetric strategy analysis
- **[4H增强策略分析报告.md](4H增强策略分析报告.md)** - 4H enhancement study

## 🔬 Research Methodology

### ManipScore Model

ManipScore detects microstructure anomalies using regression residuals:

```
Model: abs(ret) ~ f(N_ticks, spread_mean, RV, ...)
ManipScore = standardized_residual
```

High ManipScore indicates abnormal price movement given market microstructure.

### Strategy Logic (Asymmetric)

```python
if extreme_UP and high_ManipScore:
    signal = +1  # LONG (follow trend)

elif extreme_DOWN and high_ManipScore:
    signal = +1  # LONG (reversal/bounce)
```

**Key Insight**: UP and DOWN extremes have different dynamics. Both go LONG to exploit this asymmetry.

### Risk Management

- **Stop-Loss**: 0.5 × ATR (tight)
- **Take-Profit**: 0.8 × ATR (moderate)
- **Time Exit**: 5 bars maximum holding period

## 🛠️ Technical Details

### Data Processing Pipeline

1. Load 5-minute XAUUSD bars (2015-2025)
2. Resample to higher timeframes (15min, 30min, 60min, 4H, daily)
3. Fit ManipScore model independently for each timeframe
4. Compute trend features (R_past, sigma, TS)
5. Generate trading signals
6. Run backtest with SL/TP
7. Analyze performance

### No Look-Ahead Bias

All signals are shifted by 1 bar:
```python
bars['exec_signal'] = bars['raw_signal'].shift(1)
```

Execution happens at next bar's open based on previous bar's signal.

## ⚠️ Important Notes

### Data Security

- **DO NOT** commit `data/` directory or any data files to Git
- **DO NOT** commit `github.txt` (contains SSH information)
- All sensitive files are already in `.gitignore`

### Multi-Machine Development

To continue development on a new machine:

1. **Install Git** (if not already installed)
2. **Configure SSH key** for GitHub:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Add the public key to GitHub: Settings → SSH and GPG keys
   ```
3. **Clone the repository**:
   ```bash
   git clone git@github.com:yourusername/market.git
   ```
4. **Set up environment** (see Quick Start above)
5. **Add your data** to the `data/` directory
6. **Continue development** and push changes:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

## 📈 Results Files

All results are saved in `results/` directory:

- `bars_*_with_manipscore_full.csv` - Processed bars with ManipScore for each timeframe
- `*_results.csv` - Backtest statistics
- `*.png` - Visualization plots

## 🔄 Reproducibility

All experiments are fully reproducible:

```bash
# Reproduce all timeframe tests
python extended_timeframe_backtest.py

# Reproduce enhancement study
python experiments/4h_daily_clustering_study.py

# Reproduce parameter sensitivity
python experiments/4h_parameter_sensitivity.py
```

## 🤝 Contributing

This is a research project. When making changes:

1. Create a feature branch
2. Make your changes with proper type hints and docstrings
3. Update documentation
4. Test your changes
5. Submit a pull request

## 📄 License

This project is for research and educational purposes.

## 🔗 Key Insights

### Why 4H is Optimal

1. **Timeframe matches manipulation cycle**: 4H × 5 bars = 20 hours ≈ 2.5 trading days
2. **Perfect SL/TP fit**: 0.5/0.8 ATR parameters well-matched to 4H volatility
3. **Captures sustained patterns**: Multi-day manipulation unfolds over 4H bars
4. **Optimal trade-off**: Balance between signal quality and frequency

### Why Asymmetric Works

1. **UP moves**: Often continuation (momentum/manipulation pushing higher)
2. **DOWN moves**: Often reversal (manipulation exhaustion/bounce)
3. **Both go LONG**: Exploits gold's long bias and manipulation asymmetry
4. **Better than pure reversal**: Captures different dynamics in each direction

### Why Simpler is Better

1. **Baseline already captures core pattern**: Extreme trend + high ManipScore
2. **Additional filters over-constrain**: Daily confluence too restrictive (2% signals)
3. **Clustering paradox**: Isolated events may be strongest signals
4. **Occam's Razor**: Simplest explanation often correct

## 📞 Contact

For questions or collaboration, please open an issue on GitHub.

---

**Last Updated**: 2025-11-15
**Status**: ✅ Research Complete - Optimal Strategy Identified
- Wealth-limited trading models

---

**Disclaimer**: This toolkit is for research and educational purposes only. Manipulation scores are statistical anomaly measures and do not constitute legal evidence of market manipulation.

