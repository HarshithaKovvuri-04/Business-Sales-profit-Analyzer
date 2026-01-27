"""Train a simple monthly profit prediction model.

This module provides a single function `train_profit_model(db, business_id)`
which loads the prepared monthly dataset, trains a LinearRegression model,
and returns the trained model along with basic evaluation metrics.

Notes:
- This is a lightweight, local trainer used for experimentation. It does NOT
  persist models or expose an API endpoint.
- The function raises informative errors when dependencies or data are missing.
"""
from typing import Tuple, Dict, List, Any
import logging


def train_profit_model(db: Any, business_id: int) -> Tuple[Any, Dict[str, float], List[str]]:
    """Train a LinearRegression model to predict monthly profit.

    Args:
        db: SQLAlchemy Session
        business_id: business identifier to filter data

    Returns:
        model: trained sklearn regressor
        metrics: dict with keys `r2` and `mae`
        features: list of feature column names used for training

    Raises:
        ImportError: if required packages (pandas or scikit-learn) are missing
        ValueError: if insufficient data (fewer than 6 rows) is available
    """
    logger = logging.getLogger(__name__)

    # lazy imports with helpful errors
    try:
        from backend.ml.data_loader import get_monthly_profit_dataset
    except Exception as e:
        raise ImportError('Could not import data loader. Ensure backend/ml/data_loader.py is present') from e

    try:
        import pandas as pd
    except Exception as e:
        raise ImportError('pandas is required to run training. Please install pandas') from e

    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_absolute_error
    except Exception as e:
        raise ImportError('scikit-learn is required to train models. Please install scikit-learn') from e

    # Load dataset
    df = get_monthly_profit_dataset(db, business_id)
    if df is None or len(df) == 0:
        raise ValueError(f'No monthly data available for business_id={business_id}')

    # Ensure required columns exist
    features = ['total_sales', 'total_cost', 'month_num', 'rolling_3m_sales', 'rolling_3m_profit']
    target = 'total_profit'

    missing = [c for c in features + [target] if c not in df.columns]
    if missing:
        raise ValueError(f'Missing required columns in dataset: {missing}')

    # Drop rows with missing target or feature values
    df_clean = df.dropna(subset=features + [target]).copy()

    if len(df_clean) < 6:
        raise ValueError(f'Insufficient data for training (need >=6 rows, got {len(df_clean)})')

    # Prepare feature matrix and target vector
    X = df_clean[features].astype(float)
    y = df_clean[target].astype(float)

    # Time-based split: last 20% as validation (no shuffle)
    n = len(df_clean)
    split_at = int(n * 0.8)
    if split_at < 1:
        split_at = 1

    X_train = X.iloc[:split_at].values
    X_val = X.iloc[split_at:].values
    y_train = y.iloc[:split_at].values
    y_val = y.iloc[split_at:].values

    # Fit model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predict and evaluate on validation set
    y_pred = model.predict(X_val)
    r2 = float(r2_score(y_val, y_pred))
    mae = float(mean_absolute_error(y_val, y_pred))

    metrics = {'r2': r2, 'mae': mae}
    logger.info('train_profit_model business_id=%s rows=%d split=%d r2=%.4f mae=%.4f', business_id, n, split_at, r2, mae)

    return model, metrics, features
