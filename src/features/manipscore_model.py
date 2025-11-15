"""
ManipScore Model - Parameterized by timeframe

Fits a baseline model of "normal" |return| given microstructure features,
then computes ManipScore as the z-score of residuals.

Key: Each timeframe gets its own fitted model (do NOT reuse 5m coefficients for 30m).
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


@dataclass
class ManipScoreModel:
    """
    Fitted ManipScore model for a specific timeframe.
    """
    bar_size: str
    feature_cols: List[str]
    regressor: LinearRegression
    scaler_X: StandardScaler
    residual_mean: float
    residual_std: float
    
    def __repr__(self):
        return f"ManipScoreModel(bar_size={self.bar_size}, features={self.feature_cols})"


def fit_manipscore_model(
    bars: pd.DataFrame,
    bar_size: str,
    feature_cols: Optional[List[str]] = None,
    min_samples: int = 1000
) -> ManipScoreModel:
    """
    Fit a baseline model: |return| ~ f(microstructure features).
    
    Args:
        bars: DataFrame with returns and microstructure features
        bar_size: Timeframe identifier ('5min', '15min', etc.)
        feature_cols: List of feature column names to use
                     If None, auto-detect from available columns
        min_samples: Minimum number of samples required to fit
    
    Returns:
        Fitted ManipScoreModel
    """
    # Auto-detect features if not specified
    if feature_cols is None:
        feature_cols = []
        
        # Common microstructure features
        candidates = ['N_ticks', 'spread_mean', 'RV', 'volume']
        
        for col in candidates:
            if col in bars.columns:
                feature_cols.append(col)
        
        # Add lagged features if available
        if 'returns' in bars.columns:
            # Create lagged absolute returns
            bars['abs_ret_lag1'] = bars['returns'].abs().shift(1)
            bars['abs_ret_lag2'] = bars['returns'].abs().shift(2)
            feature_cols.extend(['abs_ret_lag1', 'abs_ret_lag2'])
        
        if len(feature_cols) == 0:
            raise ValueError("No microstructure features found in bars")
    
    # Prepare data
    bars_clean = bars.copy()
    
    # Target: absolute return
    bars_clean['abs_ret'] = bars_clean['returns'].abs()
    
    # Remove NaN
    required_cols = ['abs_ret'] + feature_cols
    bars_clean = bars_clean[required_cols].dropna()
    
    if len(bars_clean) < min_samples:
        raise ValueError(f"Insufficient data: {len(bars_clean)} < {min_samples}")
    
    # Prepare X and y
    X = bars_clean[feature_cols].values
    y = bars_clean['abs_ret'].values
    
    # Standardize features
    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    
    # Fit linear regression
    regressor = LinearRegression()
    regressor.fit(X_scaled, y)
    
    # Compute residuals
    y_pred = regressor.predict(X_scaled)
    residuals = y - y_pred
    
    # Compute residual statistics
    residual_mean = np.mean(residuals)
    residual_std = np.std(residuals)
    
    # Create model object
    model = ManipScoreModel(
        bar_size=bar_size,
        feature_cols=feature_cols,
        regressor=regressor,
        scaler_X=scaler_X,
        residual_mean=residual_mean,
        residual_std=residual_std
    )
    
    return model


def apply_manipscore(
    bars: pd.DataFrame,
    model: ManipScoreModel
) -> pd.DataFrame:
    """
    Apply fitted ManipScore model to bars.
    
    Adds 'ManipScore' column: z-score of residuals from baseline model.
    High ManipScore = unusually large |return| given microstructure context.
    
    Args:
        bars: DataFrame with microstructure features
        model: Fitted ManipScoreModel
    
    Returns:
        bars with 'ManipScore' column added
    """
    bars_out = bars.copy()
    
    # Ensure all required features exist
    missing_cols = set(model.feature_cols) - set(bars_out.columns)
    if missing_cols:
        # Try to create lagged features if missing
        if 'abs_ret_lag1' in missing_cols and 'returns' in bars_out.columns:
            bars_out['abs_ret_lag1'] = bars_out['returns'].abs().shift(1)
        if 'abs_ret_lag2' in missing_cols and 'returns' in bars_out.columns:
            bars_out['abs_ret_lag2'] = bars_out['returns'].abs().shift(2)
        
        # Check again
        missing_cols = set(model.feature_cols) - set(bars_out.columns)
        if missing_cols:
            raise ValueError(f"Missing required features: {missing_cols}")
    
    # Prepare features
    X = bars_out[model.feature_cols].values
    
    # Handle NaN
    valid_mask = ~np.isnan(X).any(axis=1)
    
    # Initialize ManipScore with NaN
    bars_out['ManipScore'] = np.nan
    
    if valid_mask.sum() == 0:
        return bars_out
    
    # Scale features
    X_valid = X[valid_mask]
    X_scaled = model.scaler_X.transform(X_valid)
    
    # Predict baseline |return|
    y_pred = model.regressor.predict(X_scaled)
    
    # Actual |return|
    y_actual = bars_out.loc[valid_mask, 'returns'].abs().values
    
    # Compute residuals
    residuals = y_actual - y_pred
    
    # Compute z-score (ManipScore)
    manip_scores = (residuals - model.residual_mean) / (model.residual_std + 1e-8)
    
    # Assign to output
    bars_out.loc[valid_mask, 'ManipScore'] = manip_scores
    
    return bars_out

