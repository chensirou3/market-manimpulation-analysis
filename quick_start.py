"""
Quick Start Demo Script

This script demonstrates the complete workflow of the manipulation detection toolkit.
Run this after setting up the environment to verify everything works.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("=" * 70)
print("MARKET MANIPULATION DETECTION TOOLKIT - QUICK START DEMO")
print("=" * 70)
print()

# Step 1: Import modules
print("Step 1: Importing modules...")
try:
    from src.utils.paths import load_config
    from src.data_prep.bar_aggregator import ticks_to_bars
    from src.data_prep.features_orderbook_proxy import add_orderbook_proxy_features
    from src.baseline_sim.fair_market_sim import UnlimitedWealthMarketSimulator, LimitedWealthMarketSimulator
    from src.factors.manipulation_score import compute_manipulation_score
    from src.backtest.interfaces import apply_manipulation_filter, compare_strategies
    from src.backtest.pipeline import simple_moving_average_strategy
    print("✓ All modules imported successfully\n")
except Exception as e:
    print(f"✗ Error importing modules: {e}")
    print("Please run: pip install -r requirements.txt")
    exit(1)

# Step 2: Load configuration
print("Step 2: Loading configuration...")
try:
    config = load_config()
    print(f"✓ Configuration loaded: {len(config)} sections\n")
except Exception as e:
    print(f"✗ Error loading config: {e}\n")
    exit(1)

# Step 3: Generate synthetic tick data
print("Step 3: Generating synthetic tick data...")
np.random.seed(42)
n_ticks = 10000

ticks = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01 09:30', periods=n_ticks, freq='1s'),
    'price': np.random.randn(n_ticks).cumsum() * 0.1 + 1850,
    'volume': np.random.randint(1, 100, n_ticks),
    'side': np.random.choice(['buy', 'sell'], n_ticks)
})

print(f"✓ Generated {len(ticks):,} synthetic ticks")
print(f"  Price range: ${ticks['price'].min():.2f} - ${ticks['price'].max():.2f}\n")

# Step 4: Aggregate to bars
print("Step 4: Aggregating ticks to bars...")
bars = ticks_to_bars(ticks, timeframe='1min', compute_features=True)
print(f"✓ Created {len(bars):,} bars\n")

# Step 5: Add orderbook proxy features
print("Step 5: Computing orderbook proxy features...")
bars = add_orderbook_proxy_features(bars, ticks, window=20)
print(f"✓ Added {len(bars.columns)} features total\n")

# Step 6: Compute manipulation score
print("Step 6: Computing manipulation score...")
bars = compute_manipulation_score(bars, config.get('manipulation_score'), ticks)
print(f"✓ Manipulation score computed")
print(f"  Mean score: {bars['manip_score'].mean():.3f}")
print(f"  Max score: {bars['manip_score'].max():.3f}")
print(f"  High manipulation periods (>0.7): {(bars['manip_score'] > 0.7).sum()}\n")

# Step 7: Generate strategy signals
print("Step 7: Generating trading signals (MA crossover)...")
signals_raw = simple_moving_average_strategy(bars, fast_window=10, slow_window=30)
print(f"✓ Generated signals")
print(f"  Long positions: {(signals_raw == 1).sum()}")
print(f"  Short positions: {(signals_raw == -1).sum()}")
print(f"  Neutral: {(signals_raw == 0).sum()}\n")

# Step 8: Apply manipulation filter
print("Step 8: Applying manipulation filter...")
signals_filtered = apply_manipulation_filter(
    signals_raw,
    bars['manip_score'],
    threshold=0.7,
    mode='zero'
)
n_filtered = (signals_raw != signals_filtered).sum()
print(f"✓ Filter applied: {n_filtered} signals modified\n")

# Step 9: Calculate performance
print("Step 9: Calculating performance metrics...")
bars['returns'] = bars['close'].pct_change()

comparison = compare_strategies(
    bars['returns'],
    signals_raw,
    signals_filtered,
    config.get('backtest')
)

print("✓ Performance comparison:")
print(comparison[['Original', 'Filtered']].round(4))
print()

# Step 10: Run market simulations
print("Step 10: Running market simulations...")

sim_a = UnlimitedWealthMarketSimulator(n_days=100, seed=42)
results_a = sim_a.simulate()
print(f"✓ Market A (Unlimited Wealth) simulated")
print(f"  Final price: ${results_a.prices[-1]:.2f}")

sim_b = LimitedWealthMarketSimulator(n_days=100, seed=42)
results_b = sim_b.simulate()
print(f"✓ Market B (Limited Wealth) simulated")
print(f"  Final price: ${results_b.prices[-1]:.2f}\n")

# Step 11: Visualization
print("Step 11: Creating visualization...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Price and manipulation score
ax1 = axes[0, 0]
ax1_twin = ax1.twinx()
ax1.plot(bars.index, bars['close'], 'b-', linewidth=1, label='Price')
ax1_twin.plot(bars.index, bars['manip_score'], 'r-', linewidth=1, alpha=0.7, label='Manip Score')
ax1_twin.axhline(y=0.7, color='red', linestyle='--', alpha=0.5)
ax1.set_ylabel('Price', color='b')
ax1_twin.set_ylabel('Manipulation Score', color='r')
ax1.set_title('Price and Manipulation Score')
ax1.grid(True, alpha=0.3)

# Plot 2: Trading signals
ax2 = axes[0, 1]
ax2.plot(bars.index, bars['close'], 'k-', linewidth=1, alpha=0.5)
buy_signals = bars.index[signals_raw == 1]
sell_signals = bars.index[signals_raw == -1]
ax2.scatter(buy_signals, bars.loc[buy_signals, 'close'], color='green', marker='^', s=50, alpha=0.6, label='Buy')
ax2.scatter(sell_signals, bars.loc[sell_signals, 'close'], color='red', marker='v', s=50, alpha=0.6, label='Sell')
ax2.set_ylabel('Price')
ax2.set_title('Trading Signals')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Cumulative returns
ax3 = axes[1, 0]
returns_raw = signals_raw.shift(1) * bars['returns']
returns_filtered = signals_filtered.shift(1) * bars['returns']
cum_raw = (1 + returns_raw).cumprod()
cum_filtered = (1 + returns_filtered).cumprod()
ax3.plot(bars.index, cum_raw, label='Original Strategy', linewidth=1.5)
ax3.plot(bars.index, cum_filtered, label='Filtered Strategy', linewidth=1.5)
ax3.set_ylabel('Cumulative Return')
ax3.set_title('Strategy Performance')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Plot 4: Market simulations
ax4 = axes[1, 1]
ax4.plot(results_a.days, results_a.prices, label='Market A (Unlimited)', linewidth=1.5)
ax4.plot(results_b.days, results_b.prices, label='Market B (Limited)', linewidth=1.5)
ax4.set_xlabel('Day')
ax4.set_ylabel('Price')
ax4.set_title('Market Simulations')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
print("✓ Visualization created\n")

# Final summary
print("=" * 70)
print("QUICK START DEMO COMPLETED SUCCESSFULLY!")
print("=" * 70)
print()
print("Next steps:")
print("1. Add your own tick data to the data/ directory")
print("2. Customize config.yaml for your needs")
print("3. Run full pipeline: python -m src.backtest.pipeline")
print("4. Explore notebooks: jupyter notebook")
print("5. Run tests: pytest tests/ -v")
print()
print("For more information, see:")
print("- README.md")
print("- PROJECT_OVERVIEW.md")
print("- docs/progress_log.md")
print()

plt.show()

