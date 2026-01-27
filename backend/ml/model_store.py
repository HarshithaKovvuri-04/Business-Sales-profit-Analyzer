"""Model persistence and inference utilities for profit models.

Functions:
- save_profit_model(model, business_id, feature_columns, metrics)
- load_profit_model(business_id) -> (model, metadata)
- predict_next_month_profit(db, business_id) -> float

Models and metadata are stored under `backend/ml/models/` using joblib
and JSON for metadata.
"""
from pathlib import Path
import os
import json
from datetime import datetime
from typing import Any, Dict, Tuple
import logging

import joblib


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
_logger = logging.getLogger(__name__)


def _model_paths(business_id: int) -> Tuple[Path, Path]:
    base = MODELS_DIR / f'profit_model_business_{business_id}'
    model_path = base.with_suffix('.joblib')
    meta_path = Path(str(base) + '_meta.json')
    return model_path, meta_path


def save_profit_model(model: Any, business_id: int, feature_columns: list, metrics: Dict[str, float]):
    """Serialize model and metadata for a business.

    Args:
        model: trained scikit-learn estimator
        business_id: business identifier
        feature_columns: list of feature column names used for training
        metrics: dict containing evaluation metrics (e.g., r2, mae)
    """
    model_path, meta_path = _model_paths(business_id)
    # write model
    joblib.dump(model, str(model_path))
    # write metadata
    meta = {
        'business_id': int(business_id),
        'trained_at': datetime.utcnow().isoformat() + 'Z',
        'feature_columns': list(feature_columns),
        'metrics': metrics
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_profit_model(business_id: int) -> Tuple[Any, Dict]:
    """Load a saved profit model and its metadata.

    Raises FileNotFoundError if model or metadata is missing.
    Returns (model, metadata)
    """
    model_path, meta_path = _model_paths(business_id)
    _logger.info('Loading model for business_id=%s from %s', business_id, model_path)
    if not model_path.exists() or not meta_path.exists():
        _logger.warning('Model or metadata missing for business_id=%s (model=%s meta=%s)', business_id, model_path.exists(), meta_path.exists())
        # normalize missing model to a clear FileNotFoundError
        raise FileNotFoundError('Model not trained')
    try:
        model = joblib.load(str(model_path))
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        _logger.info('Model loaded successfully for business_id=%s', business_id)
        return model, meta
    except Exception as e:
        _logger.exception('Failed to load model/metadata for business_id=%s', business_id)
        raise


def predict_next_month_profit(db: Any, business_id: int) -> float:
    """Load model and predict next month's profit for the business.

    The feature vector is constructed from the latest row in
    `get_monthly_profit_dataset(db, business_id)`. For the next-month
    `month_num` the function increments the last month (wraps at 12).
    Other numeric features are taken from the latest row as-is.

    Raises:
        FileNotFoundError: if model not found
        ValueError: if dataset is empty or model prediction fails
    """
    # lazy import to avoid unnecessary deps at module import time
    try:
        from backend.ml.data_loader import get_monthly_profit_dataset
    except ImportError:
        _logger.exception('ML dependencies missing when importing data_loader')
        # propagate a clear ImportError so callers can translate to 5xx with helpful message
        raise ImportError('Required ML dependencies (pandas) are not installed')
    except Exception:
        _logger.exception('Unexpected error importing data_loader')
        raise

    _logger.info('Predicting next month profit for business_id=%s', business_id)
    model, meta = load_profit_model(business_id)
    df = get_monthly_profit_dataset(db, business_id)
    if df is None or len(df) == 0:
        _logger.warning('No monthly data available for business_id=%s', business_id)
        raise ValueError(f'No monthly data available for business_id={business_id}')

    # Expect feature columns in metadata
    feature_columns = meta.get('feature_columns')
    if not feature_columns:
        raise ValueError('Model metadata does not include feature_columns')

    # Use the most recent month row as basis for next-month features
    last = df.sort_values('month', ascending=True).iloc[-1]

    # build feature vector dict
    fv = {}
    for col in feature_columns:
        if col == 'month_num':
            last_month = int(last.get('month_num') or 0)
            next_month = (last_month % 12) + 1
            fv['month_num'] = next_month
        else:
            # take value from last row; coerce missing to 0.0
            val = last.get(col) if col in last.index else None
            try:
                fv[col] = float(val) if val is not None else 0.0
            except Exception:
                fv[col] = 0.0

    # Ensure order of features matches feature_columns
    X = [fv.get(c, 0.0) for c in feature_columns]

    # basic sanity check: if all feature values are zero this likely indicates
    # a mismatch between model feature columns and available dataset values
    if feature_columns and all((x == 0.0 or x is None) for x in X):
        _logger.warning('All feature values are zero for business_id=%s; possible feature mismatch', business_id)
        raise ValueError('Insufficient feature data available for prediction; feature mismatch or empty dataset')

    try:
        _logger.debug('Feature vector for prediction: %s', X)
        pred = model.predict([X])
    except Exception as e:
        _logger.exception('Model prediction failed for business_id=%s', business_id)
        raise ValueError(f'Model prediction failed: {e}') from e

    try:
        return float(pred[0])
    except Exception:
        raise ValueError('Model returned non-numeric prediction')
