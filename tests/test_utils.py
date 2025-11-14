"""
Unit tests for utility modules.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.paths import get_project_root, get_config_path, load_config, get_data_dir
from src.utils.logging_utils import get_logger
from src.utils.time_utils import parse_timestamp, get_time_of_day_features


class TestPaths:
    """Tests for path utilities."""
    
    def test_get_project_root(self):
        """Test that project root can be found."""
        root = get_project_root()
        assert root.exists()
        assert (root / "requirements.txt").exists()
    
    def test_get_config_path(self):
        """Test that config path is correct."""
        config_path = get_config_path()
        assert config_path.exists()
        assert config_path.name == "config.yaml"
    
    def test_load_config(self):
        """Test that config can be loaded."""
        config = load_config()
        assert isinstance(config, dict)
        assert 'data' in config
        assert 'bars' in config
    
    def test_get_data_dir(self):
        """Test that data directory is created."""
        data_dir = get_data_dir(create_if_missing=True)
        assert data_dir.exists()
        assert data_dir.is_dir()


class TestLogging:
    """Tests for logging utilities."""
    
    def test_get_logger(self):
        """Test that logger can be created."""
        logger = get_logger(__name__)
        assert logger is not None
        assert logger.name == __name__


class TestTimeUtils:
    """Tests for time utilities."""
    
    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        ts = parse_timestamp('2024-01-01 09:30:00')
        assert isinstance(ts, pd.Timestamp)
        assert ts.year == 2024
        assert ts.month == 1
        assert ts.day == 1
    
    def test_get_time_of_day_features(self):
        """Test time-of-day feature extraction."""
        timestamps = pd.Series(pd.date_range('2024-01-01', periods=10, freq='1h'))
        features = get_time_of_day_features(timestamps)
        
        assert 'hour' in features.columns
        assert 'minute' in features.columns
        assert 'day_of_week' in features.columns
        assert len(features) == len(timestamps)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

