"""
Price-Volume anomaly detection module.

Detects anomalies in the relationship between price movements and volume.
In normal markets, large price moves should correlate with high volume and volatility.
"""

import pandas as pd
import numpy as np
from typing import Optional, Any, Dict
from sklearn.linear_model import LinearRegression
from scipy import stats

from ..utils.logging_utils import get_logger

logger = get_logger(__name__)


def fit_price_volume_model(
    bars: pd.DataFrame,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Fit a model for the price-volume relationship.
    
    Args:
        bars: DataFrame with OHLCV and features (must have 'returns', 'volume', 'rolling_vol').
        config: Configuration dict with parameters.
        
    Returns:
        dict: Fitted model and statistics.
        
    Model:
        |returns_t| ~ β0 + β1*log(volume_t) + β2*rolling_vol_t + β3*hour + ε_t
        
    Examples:
        >>> model = fit_price_volume_model(bars, config)
        >>> print(model.keys())
        dict_keys(['regressor', 'residual_mean', 'residual_std', 'features'])
    """
    if config is None:
        config = {}
    
    window = config.get('window', 100)
    features_list = config.get('features', ['volume', 'rolling_vol'])
    
    logger.info(f"Fitting price-volume model with window={window}")
    
    # Prepare data
    df = bars.copy()
    
    # Compute absolute returns if not present
    if 'returns' not in df.columns:
        df['returns'] = df['close'].pct_change()
    
    df['abs_returns'] = np.abs(df['returns'])
    
    # Add hour feature if timestamp index
    if isinstance(df.index, pd.DatetimeIndex):
        df['hour'] = df.index.hour
        if 'hour_of_day' not in features_list:
            features_list = features_list + ['hour']
    
    # Log transform volume (avoid log(0))
    if 'volume' in features_list:
        df['log_volume'] = np.log(df['volume'] + 1)
        features_list = [f if f != 'volume' else 'log_volume' for f in features_list]
    
    # Drop NaN
    df = df.dropna(subset=['abs_returns'] + features_list)
    
    # Use only recent data for fitting
    if len(df) > window:
        df = df.iloc[-window:]
    
    # Prepare X and y
    X = df[features_list].values
    y = df['abs_returns'].values
    
    # Fit linear regression
    regressor = LinearRegression()
    regressor.fit(X, y)
    
    # Compute residuals
    y_pred = regressor.predict(X)
    residuals = y - y_pred
    
    model = {
        'regressor': regressor,
        'residual_mean': np.mean(residuals),
        'residual_std': np.std(residuals),
        'features': features_list,
        'n_samples': len(df)
    }
    
    logger.info(f"Model fitted on {len(df)} samples. Residual std: {model['residual_std']:.6f}")
    
    return model


def compute_price_volume_anomaly(
    bars: pd.DataFrame,
    model: Optional[Dict[str, Any]] = None,
    config: Optional[Dict] = None
) -> pd.Series:
    """
    Compute price-volume anomaly scores.
    
    Args:
        bars: DataFrame with OHLCV and features.
        model: Pre-fitted model (if None, will fit on the data).
        config: Configuration dict.
        
    Returns:
        pd.Series: Anomaly scores (z-scores of residuals).
        
    Interpretation:
        - High positive z-score: Price moved more than expected given volume/volatility
        - High negative z-score: Price moved less than expected
        - |z| > 2.5: Potential anomaly
        
    Examples:
        >>> scores = compute_price_volume_anomaly(bars, config=config)
        >>> anomalies = scores[scores.abs() > 2.5]
    """
    if config is None:
        config = {}
    
    # Fit model if not provided
    if model is None:
        model = fit_price_volume_model(bars, config)
    
    logger.info("Computing price-volume anomaly scores")
    
    # Prepare data
    df = bars.copy()
    
    if 'returns' not in df.columns:
        df['returns'] = df['close'].pct_change()
    
    df['abs_returns'] = np.abs(df['returns'])
    
    # Add hour feature if needed
    if isinstance(df.index, pd.DatetimeIndex) and 'hour' in model['features']:
        df['hour'] = df.index.hour
    
    # Log transform volume
    if 'log_volume' in model['features']:
        df['log_volume'] = np.log(df['volume'] + 1)
    
    # Drop NaN
    valid_idx = df[['abs_returns'] + model['features']].dropna().index
    df_valid = df.loc[valid_idx]
    
    # Predict
    X = df_valid[model['features']].values
    y = df_valid['abs_returns'].values
    y_pred = model['regressor'].predict(X)
    
    # Compute residuals and z-scores
    residuals = y - y_pred
    z_scores = (residuals - model['residual_mean']) / (model['residual_std'] + 1e-8)
    
    # Create series with original index
    result = pd.Series(np.nan, index=bars.index, name='price_volume_anomaly')
    result.loc[valid_idx] = z_scores
    
    logger.info(f"Computed anomaly scores. Mean: {z_scores.mean():.3f}, Std: {z_scores.std():.3f}")
    logger.info(f"Anomalies (|z| > 2.5): {(np.abs(z_scores) > 2.5).sum()} / {len(z_scores)}")
    
    return result


if __name__ == "__main__":
    # Demo with synthetic data
    print("=== Price-Volume Anomaly Detection Demo ===\n")
    
    # Create synthetic bar data
    n_bars = 1000
    np.random.seed(42)
    
    bars = pd.DataFrame({
        'close': np.random.randn(n_bars).cumsum() + 100,
        'volume': np.random.randint(100, 1000, n_bars),
        'rolling_vol': np.random.rand(n_bars) * 0.02 + 0.01
    }, index=pd.date_range('2024-01-01', periods=n_bars, freq='1min'))
    
    bars['returns'] = bars['close'].pct_change()
    
    # Inject some anomalies (large price moves with low volume)
    anomaly_indices = [100, 250, 500, 750]
    for idx in anomaly_indices:
        bars.loc[bars.index[idx], 'returns'] = 0.05  # 5% move
        bars.loc[bars.index[idx], 'volume'] = 50     # Low volume
    
    print(f"Created {len(bars)} bars with {len(anomaly_indices)} injected anomalies\n")
    
    # Fit model
    config = {'window': 200, 'features': ['volume', 'rolling_vol']}
    model = fit_price_volume_model(bars, config)
    
    # Compute anomaly scores
    scores = compute_price_volume_anomaly(bars, model, config)
    
    print("\nTop 10 anomalies:")
    top_anomalies = scores.abs().nlargest(10)
    print(top_anomalies)
    
    print(f"\nDetected {(scores.abs() > 2.5).sum()} anomalies with |z| > 2.5")

