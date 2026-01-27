"""ML helpers package for backend.ml.

Expose lazy wrappers for training and model-store utilities so importing
``backend.ml`` does not require all ML dependencies to be present. Also
provide `ensure_ml_dependencies()` to check & cache availability of
`pandas`, `scikit-learn`, and `joblib`.
"""
from typing import Any, Dict

# Dependency cache
_deps_checked = False
_missing_deps = None

def ensure_ml_dependencies():
    """Raise ImportError listing missing ML packages if any are not available.

    Caches result so repeated calls are fast and deterministic.
    """
    global _deps_checked, _missing_deps
    if _deps_checked:
        if _missing_deps:
            raise ImportError('Missing ML dependencies: ' + ', '.join(_missing_deps))
        return

    missing = []
    try:
        import pandas as pd  # noqa: F401
    except Exception:
        missing.append('pandas')
    try:
        import sklearn  # noqa: F401
    except Exception:
        missing.append('scikit-learn')
    try:
        import joblib  # noqa: F401
    except Exception:
        missing.append('joblib')

    _deps_checked = True
    _missing_deps = missing or None
    if _missing_deps:
        raise ImportError('Missing ML dependencies: ' + ', '.join(_missing_deps))


def train_profit_model(*args, **kwargs):
    from backend.ml.train_profit_model import train_profit_model as _fn
    return _fn(*args, **kwargs)


def save_profit_model(*args, **kwargs):
    from backend.ml.model_store import save_profit_model as _fn
    return _fn(*args, **kwargs)


def load_profit_model(*args, **kwargs):
    from backend.ml.model_store import load_profit_model as _fn
    return _fn(*args, **kwargs)


def predict_next_month_profit(*args, **kwargs):
    from backend.ml.model_store import predict_next_month_profit as _fn
    return _fn(*args, **kwargs)


__all__ = [
    'ensure_ml_dependencies', 'train_profit_model', 'save_profit_model',
    'load_profit_model', 'predict_next_month_profit'
]

