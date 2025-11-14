"""
Unit tests for data preprocessing modules.
"""

import pytest
import pandas as pd
import numpy as np

from src.data_prep.bar_aggregator import ticks_to_bars, add_technical_indicators
from src.data_prep.features_orderbook_proxy import (
    compute_candlestick_features,
    compute_volume_features,
    add_orderbook_proxy_features
)


class TestBarAggregator:
    """Tests for bar aggregation."""
    
    @pytest.fixture
    def sample_ticks(self):
        """Create sample tick data."""
        n_ticks = 1000
        return pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01 09:30', periods=n_ticks, freq='1s'),
            'price': np.random.randn(n_ticks).cumsum() + 100,
            'volume': np.random.randint(1, 100, n_ticks)
        })
    
    def test_ticks_to_bars(self, sample_ticks):
        """Test tick to bar aggregation."""
        bars = ticks_to_bars(sample_ticks, timeframe='1min', compute_features=True)
        
        assert len(bars) > 0
        assert 'open' in bars.columns
        assert 'high' in bars.columns
        assert 'low' in bars.columns
        assert 'close' in bars.columns
        assert 'volume' in bars.columns
        
        # Check OHLC consistency
        assert (bars['high'] >= bars['low']).all()
        assert (bars['high'] >= bars['open']).all()
        assert (bars['high'] >= bars['close']).all()
        assert (bars['low'] <= bars['open']).all()
        assert (bars['low'] <= bars['close']).all()
    
    def test_add_technical_indicators(self, sample_ticks):
        """Test technical indicator calculation."""
        bars = ticks_to_bars(sample_ticks, timeframe='1min')
        bars_with_ta = add_technical_indicators(bars)
        
        assert 'sma_20' in bars_with_ta.columns
        assert 'ema_12' in bars_with_ta.columns
        assert 'rsi_14' in bars_with_ta.columns


class TestOrderbookProxyFeatures:
    """Tests for orderbook proxy features."""
    
    @pytest.fixture
    def sample_bars(self):
        """Create sample bar data."""
        n_bars = 100
        bars = pd.DataFrame({
            'open': np.random.randn(n_bars).cumsum() + 100,
            'high': np.random.randn(n_bars).cumsum() + 102,
            'low': np.random.randn(n_bars).cumsum() + 98,
            'close': np.random.randn(n_bars).cumsum() + 100,
            'volume': np.random.randint(100, 1000, n_bars)
        }, index=pd.date_range('2024-01-01', periods=n_bars, freq='1min'))
        
        # Ensure OHLC consistency
        bars['high'] = bars[['open', 'close', 'high']].max(axis=1)
        bars['low'] = bars[['open', 'close', 'low']].min(axis=1)
        
        return bars
    
    def test_compute_candlestick_features(self, sample_bars):
        """Test candlestick feature computation."""
        bars_with_candles = compute_candlestick_features(sample_bars)
        
        assert 'body' in bars_with_candles.columns
        assert 'upper_wick' in bars_with_candles.columns
        assert 'lower_wick' in bars_with_candles.columns
        assert 'wick_ratio' in bars_with_candles.columns
        
        # Check non-negative values
        assert (bars_with_candles['body'] >= 0).all()
        assert (bars_with_candles['upper_wick'] >= 0).all()
        assert (bars_with_candles['lower_wick'] >= 0).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

