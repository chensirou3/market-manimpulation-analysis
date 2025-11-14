"""
Fair market simulation module.

Implements two baseline market models without manipulation:
1. Market A: Unlimited wealth (Gaussian random walk)
2. Market B: Limited wealth (gravity/mean-reversion model)

These serve as benchmarks for detecting anomalous behavior.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from dataclasses import dataclass

from ..utils.logging_utils import get_logger
from ..utils.paths import load_config

logger = get_logger(__name__)


@dataclass
class SimulationResult:
    """Container for simulation results."""
    prices: np.ndarray
    volumes: np.ndarray
    days: np.ndarray
    metadata: dict


class UnlimitedWealthMarketSimulator:
    """
    Market A: Unlimited Wealth Gaussian Random Walk Simulator.
    
    Assumptions:
        - Large number of independent traders
        - Each trader submits orders with prices from N(P_prev, σ²)
        - Unlimited wealth (no budget constraints)
        - Symmetric buy/sell distributions
        
    Expected Behavior:
        - Pure random walk (no mean reversion)
        - Price can drift arbitrarily far from initial value
        
    Reference:
        Based on efficient market hypothesis and random walk theory.
    """
    
    def __init__(
        self,
        n_days: int = 500,
        n_traders: int = 1000,
        price_sigma: float = 0.02,
        initial_price: float = 100.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the simulator.
        
        Args:
            n_days: Number of trading days to simulate.
            n_traders: Number of traders per day.
            price_sigma: Standard deviation of price distribution (as fraction of price).
            initial_price: Starting price.
            seed: Random seed for reproducibility.
        """
        self.n_days = n_days
        self.n_traders = n_traders
        self.price_sigma = price_sigma
        self.initial_price = initial_price
        self.seed = seed
        
        if seed is not None:
            np.random.seed(seed)
    
    def simulate(self) -> SimulationResult:
        """
        Run the simulation.
        
        Returns:
            SimulationResult: Simulation results with price path and metadata.
        """
        logger.info(f"Running unlimited wealth simulation for {self.n_days} days")
        
        prices = np.zeros(self.n_days)
        volumes = np.zeros(self.n_days)
        prices[0] = self.initial_price
        
        for day in range(1, self.n_days):
            prev_price = prices[day - 1]
            
            # Generate buy and sell orders from normal distribution
            buy_prices = np.random.normal(
                prev_price,
                prev_price * self.price_sigma,
                self.n_traders // 2
            )
            sell_prices = np.random.normal(
                prev_price,
                prev_price * self.price_sigma,
                self.n_traders // 2
            )
            
            # Market clearing: price where supply meets demand
            # Simplified: use median of all orders
            all_prices = np.concatenate([buy_prices, sell_prices])
            prices[day] = np.median(all_prices)
            
            # Volume: number of matched trades (simplified)
            volumes[day] = self.n_traders // 2
        
        metadata = {
            'model': 'UnlimitedWealth',
            'n_traders': self.n_traders,
            'price_sigma': self.price_sigma,
            'seed': self.seed
        }
        
        logger.info(f"Simulation complete. Final price: {prices[-1]:.2f}")
        
        return SimulationResult(
            prices=prices,
            volumes=volumes,
            days=np.arange(self.n_days),
            metadata=metadata
        )


class LimitedWealthMarketSimulator:
    """
    Market B: Limited Wealth Market Simulator with Mean Reversion.
    
    Assumptions:
        - Traders have finite wealth W_i
        - Buy orders limited by: max_buy = W_i / P_current
        - Sell orders limited by asset holdings
        - Creates asymmetry: buying power decreases as price rises
        
    Expected Behavior:
        - Price exhibits mean reversion around a "gravity center"
        - Forms a trading channel/range
        - More realistic than pure random walk
        
    Reference:
        Based on wealth-limited trading models in behavioral finance.
    """
    
    def __init__(
        self,
        n_days: int = 500,
        n_traders: int = 1000,
        initial_price: float = 100.0,
        initial_wealth_mean: float = 10000.0,
        initial_wealth_std: float = 2000.0,
        initial_asset_mean: float = 50.0,
        initial_asset_std: float = 10.0,
        wealth_limit_factor: float = 0.8,
        seed: Optional[int] = None
    ):
        """
        Initialize the simulator.
        
        Args:
            n_days: Number of trading days.
            n_traders: Number of traders.
            initial_price: Starting price.
            initial_wealth_mean: Mean initial wealth per trader.
            initial_wealth_std: Std dev of initial wealth.
            initial_asset_mean: Mean initial asset holdings.
            initial_asset_std: Std dev of initial assets.
            wealth_limit_factor: Fraction of wealth available for trading.
            seed: Random seed.
        """
        self.n_days = n_days
        self.n_traders = n_traders
        self.initial_price = initial_price
        self.initial_wealth_mean = initial_wealth_mean
        self.initial_wealth_std = initial_wealth_std
        self.initial_asset_mean = initial_asset_mean
        self.initial_asset_std = initial_asset_std
        self.wealth_limit_factor = wealth_limit_factor
        self.seed = seed
        
        if seed is not None:
            np.random.seed(seed)
    
    def simulate(self) -> SimulationResult:
        """
        Run the simulation.
        
        Returns:
            SimulationResult: Simulation results.
        """
        logger.info(f"Running limited wealth simulation for {self.n_days} days")
        
        # Initialize trader wealth and assets
        wealth = np.random.normal(
            self.initial_wealth_mean,
            self.initial_wealth_std,
            self.n_traders
        )
        wealth = np.maximum(wealth, 0)  # Ensure non-negative
        
        assets = np.random.normal(
            self.initial_asset_mean,
            self.initial_asset_std,
            self.n_traders
        )
        assets = np.maximum(assets, 0)
        
        prices = np.zeros(self.n_days)
        volumes = np.zeros(self.n_days)
        prices[0] = self.initial_price
        
        for day in range(1, self.n_days):
            current_price = prices[day - 1]
            
            # Calculate maximum buy quantity for each trader
            # Limited by wealth: can only buy W / P worth of assets
            max_buy_qty = (wealth * self.wealth_limit_factor) / current_price
            
            # Calculate maximum sell quantity (limited by holdings)
            max_sell_qty = assets * self.wealth_limit_factor
            
            # Generate buy and sell interest
            buy_interest = np.random.rand(self.n_traders) * max_buy_qty
            sell_interest = np.random.rand(self.n_traders) * max_sell_qty
            
            # Total buy and sell pressure
            total_buy = buy_interest.sum()
            total_sell = sell_interest.sum()
            
            # Price adjustment based on imbalance
            # If more buying pressure, price increases (but limited by wealth constraint)
            imbalance = (total_buy - total_sell) / (total_buy + total_sell + 1e-8)
            
            # Price change is dampened by wealth constraints
            price_change_pct = imbalance * 0.01  # Small adjustment
            prices[day] = current_price * (1 + price_change_pct)
            
            # Volume (simplified)
            volumes[day] = min(total_buy, total_sell)
        
        metadata = {
            'model': 'LimitedWealth',
            'n_traders': self.n_traders,
            'initial_wealth_mean': self.initial_wealth_mean,
            'wealth_limit_factor': self.wealth_limit_factor,
            'seed': self.seed
        }
        
        logger.info(f"Simulation complete. Final price: {prices[-1]:.2f}")
        logger.info(f"Price range: [{prices.min():.2f}, {prices.max():.2f}]")
        
        return SimulationResult(
            prices=prices,
            volumes=volumes,
            days=np.arange(self.n_days),
            metadata=metadata
        )


def plot_simulation_results(
    results: SimulationResult,
    title: Optional[str] = None,
    save_path: Optional[str] = None
) -> None:
    """
    Plot simulation results.
    
    Args:
        results: SimulationResult object.
        title: Optional plot title.
        save_path: Optional path to save the figure.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Price plot
    ax1.plot(results.days, results.prices, linewidth=1.5)
    ax1.set_ylabel('Price', fontsize=12)
    ax1.set_title(title or f"{results.metadata['model']} Simulation", fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    # Volume plot
    ax2.plot(results.days, results.volumes, linewidth=1.5, color='orange')
    ax2.set_xlabel('Day', fontsize=12)
    ax2.set_ylabel('Volume', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {save_path}")
    
    plt.show()


if __name__ == "__main__":
    print("=== Fair Market Simulation Demo ===\n")
    
    # Load config
    config = load_config()
    sim_config = config.get('simulation', {})
    
    # Run Market A: Unlimited Wealth
    print("Running Market A: Unlimited Wealth (Gaussian Random Walk)...")
    sim_a = UnlimitedWealthMarketSimulator(
        n_days=sim_config.get('n_days', 500),
        n_traders=sim_config.get('unlimited_wealth', {}).get('n_traders', 1000),
        price_sigma=sim_config.get('unlimited_wealth', {}).get('price_sigma', 0.02),
        initial_price=sim_config.get('unlimited_wealth', {}).get('initial_price', 100.0),
        seed=sim_config.get('seed', 42)
    )
    results_a = sim_a.simulate()
    plot_simulation_results(results_a, title="Market A: Unlimited Wealth (Random Walk)")
    
    # Run Market B: Limited Wealth
    print("\nRunning Market B: Limited Wealth (Mean Reversion)...")
    sim_b = LimitedWealthMarketSimulator(
        n_days=sim_config.get('n_days', 500),
        n_traders=sim_config.get('limited_wealth', {}).get('n_traders', 1000),
        initial_price=sim_config.get('limited_wealth', {}).get('initial_price', 100.0),
        seed=sim_config.get('seed', 42)
    )
    results_b = sim_b.simulate()
    plot_simulation_results(results_b, title="Market B: Limited Wealth (Mean Reversion)")
    
    print("\nSimulation complete!")

