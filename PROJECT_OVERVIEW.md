# Project Overview - Market Manipulation Detection Toolkit

## 📦 Complete Project Structure

```
market/
├── .gitignore                          # Git ignore rules (data, secrets, cache)
├── README.md                           # Main project documentation
├── PROJECT_OVERVIEW.md                 # This file
├── requirements.txt                    # Python dependencies
├── github.txt                          # SSH configuration (NOT in Git)
├── verify_setup.py                     # Setup verification script
│
├── data/                               # Data directory (NOT in Git)
│   └── README.md                       # Data format documentation
│
├── src/                                # Source code
│   ├── __init__.py
│   │
│   ├── config/                         # Configuration
│   │   ├── __init__.py
│   │   └── config.yaml                 # Main configuration file
│   │
│   ├── utils/                          # Utility modules
│   │   ├── __init__.py
│   │   ├── paths.py                    # Path management
│   │   ├── logging_utils.py            # Logging configuration
│   │   └── time_utils.py               # Time utilities
│   │
│   ├── data_prep/                      # Data preprocessing
│   │   ├── __init__.py
│   │   ├── tick_loader.py              # Load tick data
│   │   ├── bar_aggregator.py           # Tick → Bar aggregation
│   │   └── features_orderbook_proxy.py # Orderbook proxy features
│   │
│   ├── baseline_sim/                   # Market simulation
│   │   ├── __init__.py
│   │   └── fair_market_sim.py          # Fair market simulators
│   │
│   ├── anomaly/                        # Anomaly detection
│   │   ├── __init__.py
│   │   ├── price_volume_anomaly.py     # Price-volume anomalies
│   │   ├── volume_spike_anomaly.py     # Volume spike detection
│   │   └── structure_anomaly.py        # Structural anomalies
│   │
│   ├── factors/                        # Factor construction
│   │   ├── __init__.py
│   │   └── manipulation_score.py       # Manipulation score aggregation
│   │
│   └── backtest/                       # Backtesting
│       ├── __init__.py
│       ├── interfaces.py               # Strategy interfaces
│       └── pipeline.py                 # End-to-end pipeline
│
├── notebooks/                          # Jupyter notebooks
│   ├── explore_data.ipynb              # Data exploration
│   └── demo_simulation.ipynb           # Simulation demo
│
├── docs/                               # Documentation
│   ├── progress_log.md                 # Development progress
│   └── design_notes.md                 # Technical design notes
│
└── tests/                              # Unit tests
    ├── __init__.py
    ├── test_utils.py                   # Test utilities
    ├── test_data_prep.py               # Test data preprocessing
    └── test_simulation.py              # Test simulations
```

## 🎯 Module Responsibilities

### 1. **Configuration (`src/config/`)**
- `config.yaml`: Central configuration for all parameters
- Paths, timeframes, model parameters, weights, thresholds

### 2. **Utilities (`src/utils/`)**
- `paths.py`: Project root, data directory, config loading
- `logging_utils.py`: Centralized logging
- `time_utils.py`: Time parsing, time-of-day features

### 3. **Data Preprocessing (`src/data_prep/`)**
- `tick_loader.py`: Load tick data from CSV/Parquet
- `bar_aggregator.py`: Aggregate ticks to OHLCV bars
- `features_orderbook_proxy.py`: Construct orderbook proxy features

### 4. **Baseline Simulation (`src/baseline_sim/`)**
- `fair_market_sim.py`: 
  - Market A: Unlimited wealth (Gaussian random walk)
  - Market B: Limited wealth (mean reversion)

### 5. **Anomaly Detection (`src/anomaly/`)**
- `price_volume_anomaly.py`: Detect unusual price moves given volume
- `volume_spike_anomaly.py`: Detect volume spikes vs historical baseline
- `structure_anomaly.py`: Detect wash trading, extreme candlesticks

### 6. **Factor Construction (`src/factors/`)**
- `manipulation_score.py`: Aggregate anomaly scores into single factor

### 7. **Backtesting (`src/backtest/`)**
- `interfaces.py`: Strategy filtering interfaces
- `pipeline.py`: End-to-end backtesting pipeline

## 🚀 Quick Start Checklist

### First Time Setup

1. **Verify Python Installation**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Setup**
   ```bash
   python verify_setup.py
   ```

5. **Add Your Data**
   - Place tick data in `data/` directory
   - Format: `{symbol}_ticks.csv` or `{symbol}_ticks.parquet`

### Running Examples

1. **Market Simulation**
   ```bash
   python -m src.baseline_sim.fair_market_sim
   ```

2. **Full Pipeline Demo**
   ```bash
   python -m src.backtest.pipeline
   ```

3. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

4. **Jupyter Notebooks**
   ```bash
   jupyter notebook
   # Open notebooks/demo_simulation.ipynb
   ```

## 📊 Data Flow

```
Tick Data (CSV/Parquet)
    ↓
[tick_loader.py] Load & Parse
    ↓
[bar_aggregator.py] Aggregate to OHLCV Bars
    ↓
[features_orderbook_proxy.py] Add Features
    ↓
[anomaly/*.py] Detect Anomalies
    ↓
[manipulation_score.py] Compute ManipScore
    ↓
[backtest/pipeline.py] Apply to Strategy
    ↓
Performance Metrics & Comparison
```

## 🔧 Configuration

All parameters are in `src/config/config.yaml`:

- **Data paths**: Where to find tick data
- **Bar settings**: Timeframe, rolling windows
- **Simulation**: Number of days, traders, volatility
- **Anomaly detection**: Thresholds, windows, features
- **ManipScore weights**: How to combine anomaly scores
- **Backtesting**: Filter mode, transaction costs

## 📝 Development Workflow

1. **Make Changes**
   - Edit code in `src/`
   - Update tests in `tests/`
   - Document in `docs/progress_log.md`

2. **Test**
   ```bash
   pytest tests/
   ```

3. **Commit**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

4. **On New Machine**
   ```bash
   git clone <your-repo-url>
   cd market
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python verify_setup.py
   ```

## ⚠️ Important Notes

### Security
- **NEVER** commit `data/` directory
- **NEVER** commit `github.txt`
- **NEVER** commit `.env` files
- All sensitive files are in `.gitignore`

### Performance
- Use Parquet for large datasets (faster than CSV)
- Consider caching intermediate results
- For production, optimize hot loops with Numba

### Extensibility
- Add new anomaly detectors in `src/anomaly/`
- Add new strategies in `src/backtest/`
- Update weights in `config.yaml`

## 📚 Documentation

- **README.md**: Quick start and overview
- **docs/progress_log.md**: Development history and usage
- **docs/design_notes.md**: Technical details and assumptions
- **Docstrings**: All functions have detailed docstrings

## 🧪 Testing

- Unit tests in `tests/`
- Run with: `pytest tests/ -v`
- Coverage: `pytest --cov=src tests/`

## 📈 Next Steps

1. Add your tick data to `data/`
2. Run `verify_setup.py` to check everything works
3. Try the demo: `python -m src.backtest.pipeline`
4. Explore notebooks for interactive analysis
5. Customize `config.yaml` for your needs
6. Integrate with your existing strategies

---

**Version**: 0.1.0  
**Last Updated**: 2025-11-14  
**Status**: ✅ Ready for use

