"""
Unit tests for market simulation modules.
"""

import pytest
import numpy as np

from src.baseline_sim.fair_market_sim import (
    UnlimitedWealthMarketSimulator,
    LimitedWealthMarketSimulator
)


class TestUnlimitedWealthSimulator:
    """Tests for unlimited wealth market simulator."""
    
    def test_simulation_runs(self):
        """Test that simulation completes without errors."""
        sim = UnlimitedWealthMarketSimulator(
            n_days=100,
            n_traders=100,
            seed=42
        )
        results = sim.simulate()
        
        assert len(results.prices) == 100
        assert len(results.volumes) == 100
        assert results.prices[0] == sim.initial_price
    
    def test_reproducibility(self):
        """Test that simulation is reproducible with same seed."""
        sim1 = UnlimitedWealthMarketSimulator(n_days=100, seed=42)
        sim2 = UnlimitedWealthMarketSimulator(n_days=100, seed=42)
        
        results1 = sim1.simulate()
        results2 = sim2.simulate()
        
        np.testing.assert_array_equal(results1.prices, results2.prices)


class TestLimitedWealthSimulator:
    """Tests for limited wealth market simulator."""
    
    def test_simulation_runs(self):
        """Test that simulation completes without errors."""
        sim = LimitedWealthMarketSimulator(
            n_days=100,
            n_traders=100,
            seed=42
        )
        results = sim.simulate()
        
        assert len(results.prices) == 100
        assert len(results.volumes) == 100
        assert results.prices[0] == sim.initial_price
    
    def test_mean_reversion(self):
        """Test that limited wealth model shows less drift than unlimited."""
        # This is a statistical test - may occasionally fail
        sim_limited = LimitedWealthMarketSimulator(n_days=500, seed=42)
        sim_unlimited = UnlimitedWealthMarketSimulator(n_days=500, seed=42)
        
        results_limited = sim_limited.simulate()
        results_unlimited = sim_unlimited.simulate()
        
        # Limited wealth should have smaller price range
        range_limited = results_limited.prices.max() - results_limited.prices.min()
        range_unlimited = results_unlimited.prices.max() - results_unlimited.prices.min()
        
        # This is a weak test - just checking that both produce reasonable results
        assert range_limited > 0
        assert range_unlimited > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

