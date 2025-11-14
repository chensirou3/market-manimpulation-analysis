# Design Notes & Technical Details

## Overview

This document captures the core design decisions, model assumptions, and technical considerations for the Market Manipulation Detection Toolkit.

---

## 1. Baseline Market Simulation

### 1.1 Market A: Unlimited Wealth (Gaussian Random Walk)

**Assumptions**:
- Large number of independent traders
- Each trader submits buy/sell orders with prices drawn from a normal distribution centered on the previous day's price
- Traders have unlimited wealth (no budget constraints)
- Buy and sell distributions are symmetric

**Mathematical Model**:
```
P_t ~ N(P_{t-1}, σ²)
```

**Expected Behavior**:
- Pure random walk (no mean reversion)
- Price can drift arbitrarily far from initial value
- No inherent "fair value" or gravity center

**Implementation Notes**:
- Use batch auction clearing mechanism
- Match orders to maximize trading volume
- Price determined by market-clearing equilibrium

### 1.2 Market B: Limited Wealth (Gravity Model)

**Assumptions**:
- Traders have finite wealth W_i
- Buy orders limited by: max_buy_volume = W_i / P_current
- Sell orders limited by asset holdings (but can quote any price)
- Creates asymmetry: buying power decreases as price rises

**Expected Behavior**:
- Price exhibits mean reversion around a "gravity center"
- Forms a trading channel/range
- More realistic for modeling actual markets

**Key Insight**:
The wealth constraint creates a natural price ceiling and floor, preventing unbounded drift.

---

## 2. Anomaly Detection Framework

### 2.1 Price-Volume Anomaly

**Rationale**:
In normal markets, price movements correlate with volume and volatility. Manipulation often creates abnormal price moves given the volume context.

**Method**:
1. Fit regression model: |ΔP_t| ~ f(volume_t, rolling_vol_t, time_features)
2. Compute residuals: ε_t = |ΔP_t| - f(...)
3. Z-score: z_t = (ε_t - μ_ε) / σ_ε
4. Anomaly score: high |z_t| indicates unusual price-volume relationship

**TODO**:
- Experiment with non-linear models (Random Forest, XGBoost)
- Add more features (bid-ask spread proxy, order imbalance)

### 2.2 Volume Spike Detection

**Rationale**:
Sudden volume spikes, especially outside normal trading hours or without news, may indicate manipulation (pump-and-dump, spoofing).

**Method**:
1. Group historical data by time-of-day (to account for intraday seasonality)
2. Compute μ and σ for each time bucket
3. For new bar: z_t = (volume_t - μ_{time_bucket}) / σ_{time_bucket}
4. Flag if z_t > threshold (e.g., 3.0)

**Considerations**:
- Need sufficient history (30+ days recommended)
- May need to handle special events (earnings, news)

### 2.3 Structural Anomaly (Wash Trading Proxy)

**Rationale**:
Wash trading involves self-dealing to create artificial volume. Characteristics:
- High gross volume (sum of |trades|)
- Low net volume (sum of signed trades)
- Ratio: wash_index = gross_vol / (net_vol + ε)

**Method**:
1. Compute gross and net volume over rolling window
2. Calculate wash_index
3. Flag if wash_index > threshold (e.g., 5.0)

**Limitations**:
- Without Level 2 data or trader IDs, this is only a proxy
- High wash_index can occur naturally in ranging markets
- Future: analyze tick-level patterns (mirror trades, exact size matches)

### 2.4 Candlestick Pattern Anomalies

**Rationale**:
Extreme wicks with high volume but small body may indicate:
- Stop-loss hunting
- Spoofing (fake orders to move price, then cancel)
- Pump-and-dump (spike then immediate reversal)

**Features**:
- `upper_wick = high - max(open, close)`
- `lower_wick = min(open, close) - low`
- `body = |close - open|`
- `wick_ratio = (upper_wick + lower_wick) / (body + ε)`

**Detection**:
Flag bars with:
- High wick_ratio (e.g., > 3.0)
- High volume (e.g., > 95th percentile)
- Small body (price closes near open)

---

## 3. Manipulation Score Construction

### 3.1 Aggregation Method

**Approach**: Weighted average of normalized anomaly scores

```
ManipScore_t = Σ w_i × S_i,t
```

Where:
- S_i,t: Individual anomaly score (normalized to [0, 1])
- w_i: Weight for anomaly type i
- Σ w_i = 1.0

**Normalization Options**:
1. **Min-Max**: S = (x - min) / (max - min)
2. **Z-score + Sigmoid**: S = 1 / (1 + exp(-z))
3. **Percentile Rank**: S = percentile(x) / 100

**Current Default**: Min-max normalization with optional smoothing

### 3.2 Interpretation

- **Score ∈ [0, 1]**
- **0**: No anomaly detected (normal market behavior)
- **1**: Maximum anomaly (highly suspicious)
- **Threshold**: Typically 0.6-0.8 for filtering

**Important**: This is a statistical measure, NOT legal evidence of manipulation.

---

## 4. Backtesting Integration

### 4.1 Filter Modes

**Zero Mode**:
```python
if manip_score > threshold:
    signal = 0  # No position
```

**Reduce Mode**:
```python
if manip_score > threshold:
    signal *= reduce_factor  # Scale down position
```

**Adaptive Mode** (TODO):
```python
signal *= (1 - manip_score)  # Continuous scaling
```

### 4.2 Strategy Interface

External strategies should provide:
- `signal`: pd.Series with values {-1, 0, +1} or continuous
- `timestamp`: aligned with bar data

The pipeline will:
1. Compute manipulation score
2. Apply filter
3. Calculate performance metrics (return, Sharpe, drawdown)

---

## 5. Data Requirements

### 5.1 Tick Data Format

**Minimum Required**:
- `timestamp`: datetime
- `price`: float
- `volume`: float

**Optional but Recommended**:
- `side`: str ('buy' or 'sell')
- `bid`: float (best bid price)
- `ask`: float (best ask price)

**Supported Formats**:
- CSV (slower, human-readable)
- Parquet (faster, compressed)

### 5.2 Orderbook Proxy Features

Since we don't have Level 2 data, we construct proxies:

**From Ticks**:
- Signed volume: +volume if buy, -volume if sell
- Trade imbalance: (buy_vol - sell_vol) / (buy_vol + sell_vol)

**From Bars**:
- Wick ratios (as described above)
- VWAP vs close deviation
- Intrabar volatility proxy

**Future Enhancement**:
If Level 2 data becomes available, add:
- Bid-ask spread
- Order book imbalance
- Depth at various levels

---

## 6. Performance Considerations

### 6.1 Current Implementation

- Pure Python + NumPy/Pandas
- Suitable for research and moderate-scale backtesting
- Expected performance: ~1M ticks in <10 seconds (depends on features)

### 6.2 Future Optimizations

**If performance becomes an issue**:
1. **Numba**: JIT-compile hot loops (e.g., bar aggregation)
2. **Cython**: Rewrite critical paths in Cython
3. **Vectorization**: Ensure all operations are vectorized
4. **Parallel Processing**: Use multiprocessing for multiple symbols
5. **Database**: Store preprocessed bars in SQLite/PostgreSQL

---

## 7. Extensibility

### 7.1 Adding New Anomaly Detectors

1. Create new file in `src/anomaly/`
2. Implement function with signature:
   ```python
   def compute_xxx_anomaly(bars: pd.DataFrame, config: dict) -> pd.Series:
       """Compute XXX anomaly score."""
       ...
   ```
3. Add configuration to `config.yaml`
4. Update `manipulation_score.py` to include new score
5. Add weight in config

### 7.2 Adding New Markets/Assets

- No code changes needed
- Just add new data files to `data/`
- Update config if different parameters needed

### 7.3 Adding New Strategies

- Implement strategy to produce `signal` Series
- Use `backtest.interfaces.apply_manipulation_filter()`
- Run through `backtest.pipeline`

---

## 8. Known Limitations & Future Work

### Current Limitations

1. **No Level 2 Data**: Orderbook features are proxies only
2. **No Trader IDs**: Cannot detect cross-account wash trading
3. **Single Asset**: No cross-asset manipulation detection
4. **Batch Processing**: Not real-time (yet)

### Future Enhancements

- [ ] Real-time streaming support
- [ ] Multi-asset correlation analysis
- [ ] Deep learning models for pattern recognition
- [ ] Integration with news/sentiment data
- [ ] Regulatory reporting templates
- [ ] Web dashboard for monitoring

---

## 9. References & Inspiration

- **Gaussian Random Walk Models**: Classic efficient market hypothesis
- **Wealth-Limited Trading**: Behavioral finance literature
- **Wash Trading Detection**: SEC/CFTC enforcement cases
- **Market Microstructure**: O'Hara (1995), Hasbrouck (2007)

---

**Last Updated**: 2025-11-14  
**Maintainer**: Quant Team

