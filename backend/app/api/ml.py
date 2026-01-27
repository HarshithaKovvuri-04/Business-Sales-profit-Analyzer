from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud
from .deps import get_db_dep, get_current_user
import logging

router = APIRouter()


@router.get('/predict-profit/{business_id}')
def predict_profit(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    """Return next-month profit prediction using persisted model for a business.

    Read-only: loads saved model and metadata, constructs features from the
    latest month and returns a numeric prediction and model metrics.
    """
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')

    logger = logging.getLogger(__name__)
    try:
        # lazy imports from ml package (use absolute imports to avoid relative-import issues)
        from backend.ml import ensure_ml_dependencies
        from backend.ml.data_loader import get_monthly_profit_dataset
        # run dependency check once (will raise ImportError if missing)
        ensure_ml_dependencies()
        # only now import model_store (it imports joblib at module level)
        from backend.ml import model_store
    except Exception as e:
        # Distinguish missing dependencies vs other import errors to give clearer feedback
        if isinstance(e, ImportError):
            logger.exception('ML dependencies not available: %s', e)
            raise HTTPException(status_code=500, detail=f'ML dependencies not available: {e}')
        logger.exception('ML utilities not available')
        raise HTTPException(status_code=500, detail='ML utilities not available')

    # load model and metadata (raises FileNotFoundError if missing)
    try:
        model, meta = model_store.load_profit_model(business_id)
    except FileNotFoundError:
        # Normalize missing model to a clear 404 for clients
        raise HTTPException(status_code=404, detail='Model not trained')
    except ImportError as ie:
        logger.exception('ML dependencies missing when loading model: %s', ie)
        raise HTTPException(status_code=500, detail=f'ML dependencies not available: {ie}')
    except Exception:
        logger.exception('Error loading model for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Error loading model')

    # perform prediction (may raise ValueError for insufficient data)
    try:
        predicted = model_store.predict_next_month_profit(db, business_id)
    except ValueError as ve:
        # insufficient data or prediction failure
        raise HTTPException(status_code=400, detail=str(ve))
    except ImportError as ie:
        logger.exception('ML dependencies missing during prediction: %s', ie)
        raise HTTPException(status_code=500, detail=f'ML dependencies not available: {ie}')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Model not trained')
    except Exception:
        logger.exception('Unexpected error during prediction for business_id=%s', business_id, exc_info=True)
        raise HTTPException(status_code=500, detail='Internal server error while predicting')

    # compute predicted_month based on latest data
    try:
        df = get_monthly_profit_dataset(db, business_id)
        if df is None or len(df) == 0:
            predicted_month = None
        else:
            last_month = str(df['month'].iloc[-1])
            # expect YYYY-MM
            parts = last_month.split('-')
            if len(parts) == 2:
                y = int(parts[0]); m = int(parts[1]);
                nm = (m % 12) + 1
                ny = y + 1 if nm == 1 and m == 12 else y
                predicted_month = f"{ny:04d}-{nm:02d}"
            else:
                predicted_month = None
    except Exception:
        logger.exception('Error computing predicted_month for business_id=%s', business_id)
        predicted_month = None

    metrics = meta.get('metrics') if isinstance(meta, dict) else None

    return {
        'business_id': int(business_id),
        'predicted_month': predicted_month,
        'predicted_profit': float(predicted),
        'model_metrics': metrics or {}
    }
