# Market Manipulation Detection Toolkit

A comprehensive Python toolkit for **trade-based manipulation detection** using tick-level market data. This project implements market simulation, anomaly detection, and manipulation scoring to identify suspicious trading patterns.

## 📖 Project Overview

This toolkit is inspired by research on trade-based market manipulation, implementing:

- **Baseline Market Simulation**: Two models of fair markets (unlimited wealth Gaussian random walk & limited wealth with price gravity)
- **Anomaly Detection**: Multi-dimensional detection of suspicious patterns (price-volume anomalies, volume spikes, structural anomalies)
- **Manipulation Score Factor**: Aggregated risk metric for filtering trading strategies
- **Backtesting Integration**: Seamless integration with existing trend/reversal strategies

### Key Features

- ✅ Modular, extensible architecture
- ✅ Type-annotated codebase with comprehensive docstrings
- ✅ Configuration-driven design (YAML-based)
- ✅ Multi-machine development support (Git + GitHub workflow)
- ✅ Data security (sensitive files excluded from version control)

## 📁 Project Structure

```
market/
├── data/                          # Raw tick data and intermediate results (NOT in Git)
├── src/
│   ├── config/                    # Configuration management
│   │   └── config.yaml           # Main configuration file
│   ├── data_prep/                # Data preprocessing
│   │   ├── tick_loader.py        # Tick data loading
│   │   ├── bar_aggregator.py     # Tick → Bar aggregation
│   │   └── features_orderbook_proxy.py  # Orderbook proxy features
│   ├── baseline_sim/             # Fair market simulation
│   │   └── fair_market_sim.py    # Gaussian & wealth-limited simulators
│   ├── anomaly/                  # Anomaly detection
│   │   ├── price_volume_anomaly.py
│   │   ├── volume_spike_anomaly.py
│   │   └── structure_anomaly.py
│   ├── factors/                  # Factor construction
│   │   └── manipulation_score.py # Manipulation score aggregation
│   ├── backtest/                 # Backtesting integration
│   │   ├── interfaces.py         # Strategy interfaces
│   │   └── pipeline.py           # End-to-end pipeline
│   └── utils/                    # Utilities
│       ├── paths.py              # Path management
│       ├── logging_utils.py      # Logging configuration
│       └── time_utils.py         # Time utilities
├── notebooks/                     # Jupyter notebooks for exploration
├── docs/                         # Documentation
│   ├── progress_log.md           # Development progress log
│   └── design_notes.md           # Design decisions and assumptions
├── tests/                        # Unit tests
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### Option 1: Run Quick Start Demo (Recommended for First Time)

```bash
# After installing dependencies (see below)
python quick_start.py
```

This will run a complete demonstration of the toolkit with synthetic data, showing:
- Data loading and preprocessing
- Manipulation score calculation
- Strategy filtering
- Performance comparison
- Market simulations
- Visualization

### Option 2: Step-by-Step Setup

#### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-ssh-url>
cd market

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Verify Setup

```bash
# Run verification script
python verify_setup.py
```

This will check:
- Python version (3.10+ required)
- All dependencies installed
- Project structure complete
- Modules can be imported

#### 3. Data Preparation

Place your tick data in the `data/` directory. Expected format:

**CSV Format** (example):
```csv
timestamp,price,volume,side
2024-01-01 09:30:00.123,1850.25,100,buy
2024-01-01 09:30:00.456,1850.30,50,sell
...
```

**Required columns**:
- `timestamp`: datetime (will be parsed to pandas datetime)
- `price`: float
- `volume`: float
- `side`: str (optional, 'buy'/'sell')

#### 4. Run Examples

```bash
# Run baseline market simulation
python -m src.baseline_sim.fair_market_sim

# Run full backtesting pipeline
python -m src.backtest.pipeline

# Run quick start demo (recommended)
python quick_start.py
```

#### 5. Explore with Notebooks

```bash
# Start Jupyter
jupyter notebook

# Open notebooks/demo_simulation.ipynb
```

## ⚙️ Configuration

Edit `src/config/config.yaml` to customize:

- Data paths
- Bar timeframes (1min, 5min, etc.)
- Simulation parameters
- Anomaly detection thresholds
- Manipulation score weights

## 📊 Usage Example

```python
from src.data_prep.tick_loader import load_tick_data
from src.data_prep.bar_aggregator import ticks_to_bars
from src.factors.manipulation_score import compute_manipulation_score

# Load tick data
ticks = load_tick_data(symbol='XAUUSD', start_date='2024-01-01')

# Aggregate to bars
bars = ticks_to_bars(ticks, timeframe='1min')

# Compute manipulation score
bars_with_score = compute_manipulation_score(bars, config)

# Use in your strategy
# ... (see notebooks for full examples)
```

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

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 📚 Documentation

- **Progress Log**: See `docs/progress_log.md` for development history
- **Design Notes**: See `docs/design_notes.md` for technical details
- **API Docs**: See docstrings in source code (Google-style)

## 🤝 Contributing

This is a personal/team project. When making changes:

1. Create a feature branch
2. Make your changes with proper type hints and docstrings
3. Update `docs/progress_log.md`
4. Test your changes
5. Submit a pull request (or push to main if solo)

## 📄 License

[Specify your license here]

## 🔗 References

- Inspired by research on trade-based market manipulation
- Gaussian random walk models for fair market simulation
- Wealth-limited trading models

---

**Disclaimer**: This toolkit is for research and educational purposes only. Manipulation scores are statistical anomaly measures and do not constitute legal evidence of market manipulation.

