# 4H Strategy Enhancement Study - Executive Summary

## Objective

Test whether multi-timeframe confluence and signal clustering filters can improve the baseline 4h asymmetric strategy (Sharpe 4.03).

## Methodology

**Data**: 11 years (2015-2025), 17,187 4h bars, 3,341 daily bars  
**Strategy**: Asymmetric (UP=continuation, DOWN=reversal)  
**Baseline**: 4h extreme trend + high ManipScore → LONG

**Tested 4 variants**:
- A) Baseline (no filters)
- B) + Daily confluence filter
- C) + Clustering filter  
- D) + Both filters

## Key Results

### Main Experiment

| Variant | Signals | Retained | Sharpe | Total Return | Win Rate | Max DD |
|---------|---------|----------|--------|--------------|----------|--------|
| **A: Baseline** | **358** | **100%** | **4.03** 🥇 | **13.09%** 🥇 | 43.6% | -7.40% |
| B: Daily | 7 | 2.0% | - | - | - | - |
| C: Clustering | 67 | 18.7% | 1.58 | 3.59% | 44.8% | -4.40% |
| D: Both | 2 | 0.6% | - | - | - | - |

**Findings**:
- ✅ Baseline strategy is already optimal (Sharpe 4.03)
- ❌ Daily confluence too restrictive (only 2% signals retained)
- ❌ Clustering filter degrades performance (Sharpe drops to 1.58)

### Parameter Sensitivity Analysis

**Clustering Parameters** (9 combinations tested):

| W | min_count | q_manip | Signals | Retained | Sharpe | Return | Win Rate |
|---|-----------|---------|---------|----------|--------|--------|----------|
| **8** | **4** | **0.90** | **37** | **10.3%** | **3.96** 🥇 | **7.00%** | **54.1%** 🥇 |
| 4 | 2 | 0.90 | 163 | 45.5% | 3.81 | 10.35% | 44.8% |
| 4 | 2 | 0.85 | 203 | 56.7% | 3.69 | 10.54% | 43.8% |
| 6 | 3 | 0.90 | 67 | 18.7% | 1.58 | 3.59% | 44.8% |

**Best clustering params**: W=8, min_count=4, q_manip=0.90
- Sharpe 3.96 (close to baseline's 4.03)
- Win rate 54.1% (+10.5% vs baseline!)
- But only 37 trades (90% fewer signals)

**Daily Confluence Parameters** (6 combinations tested):

| q_trend | q_manip | Signals | Retained | Sharpe | Return | Win Rate |
|---------|---------|---------|----------|--------|--------|----------|
| 0.80 | 0.85 | 12 | 3.4% | 1.61 | 1.96% | 41.7% |
| 0.80 | 0.80 | 13 | 3.6% | 1.45 | 1.77% | 38.5% |
| 0.85 | 0.85 | 10 | 2.8% | -0.03 | -0.03% | 30.0% |

**Conclusion**: Even most lenient params (0.80, 0.80) only retain 3.6% signals with poor performance.

## Key Insights

### 1. Baseline Strategy is Already Excellent

The 4h asymmetric strategy (no extra filters) achieves:
- Sharpe 4.03 (exceptional risk-adjusted return)
- 11-year total return 13.09%
- 358 trades (~33/year)
- Max drawdown -7.40% (manageable)

**This strategy already captures the core manipulation patterns effectively.**

### 2. The Clustering Paradox

**Hypothesis**: Clustered high ManipScore events (sustained over multiple bars) should have higher quality than isolated spikes.

**Reality**: 
- Standard clustering (W=6, min_count=3): Sharpe **drops** to 1.58
- Optimal clustering (W=8, min_count=4): Sharpe 3.96, **approaches** baseline

**Possible reasons**:
- Isolated extreme ManipScore events may be the strongest reversal signals
- Clustered events may represent "normal" trend continuation, not manipulation
- Over-filtering removes valuable signals

### 3. Daily Confluence is Too Restrictive

**Problem**:
- 4h extreme events and daily extreme events have very low overlap (<5%)
- These timeframes capture **different types** of market behavior
- Forcing alignment over-constrains signals

**Conclusion**:
- 4h and daily should be **independent strategies**, not fused
- Or use looser daily conditions (e.g., directional alignment, not extremes)

### 4. Quality vs Quantity Trade-off

| Strategy | Signals | Sharpe | Win Rate | Avg Return/Trade |
|----------|---------|--------|----------|------------------|
| Baseline | 358 | 4.03 | 43.6% | 3.66 bps |
| Optimal Clustering | 37 | 3.96 | 54.1% | 18.92 bps |

**Finding**:
- Optimal clustering improves win rate (+10.5%) and return/trade (+5.2x)
- But 90% fewer signals → lower total return (13.09% → 7.00%)
- **Sharpe nearly identical** (4.03 vs 3.96)

## Recommendations

### Primary Recommendation

**Use Baseline 4H Asymmetric Strategy (no extra filters)**

**Rationale**:
1. ✅ Highest Sharpe (4.03)
2. ✅ Highest total return (13.09%)
3. ✅ Sufficient trade frequency (~33/year)
4. ✅ Simple, stable, interpretable

### Alternative (if higher win rate / fewer trades desired)

**Clustering Variant**: W=8, min_count=4, q_manip=0.90
- Sharpe 3.96 (slightly lower than baseline)
- Win rate 54.1% (significantly higher)
- 37 trades (~3.4/year)

### Not Recommended

❌ **Daily confluence filter**: Too restrictive, poor performance

## Future Research Directions

1. **Multi-timeframe portfolio**
   - Run 4h + daily as **independent strategies** in parallel
   - Not as confluence filter

2. **Dynamic parameters**
   - Adjust SL/TP based on market volatility
   - Adjust thresholds based on ManipScore distribution

3. **Risk management optimization**
   - Test different SL/TP parameters
   - Test time-only exit (no SL/TP)

4. **Factor combination**
   - Test other microstructure features
   - Test order flow imbalance metrics

## Files Generated

- `results/4h_filter_comparison_stats.csv` - Main experiment results
- `results/4h_clustering_sensitivity.csv` - Clustering parameter sensitivity
- `results/4h_daily_sensitivity.csv` - Daily parameter sensitivity
- `4H增强策略分析报告.md` - Detailed Chinese report

## Conclusion

The 4h asymmetric strategy is already an excellent strategy (Sharpe 4.03). Additional filters do not provide significant improvement. **Keep it simple.**

