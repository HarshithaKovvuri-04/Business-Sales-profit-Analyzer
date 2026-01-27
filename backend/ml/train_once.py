"""One-time admin script to train and save profit model for a business.

Run as:
  python -m backend.ml.train_once

This script is intentionally manual and must be run by an administrator.
"""
from __future__ import annotations
import logging
import sys

from backend.app.db.session import SessionLocal


def main(business_id: int = 3):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        from backend.ml import train_profit_model, save_profit_model
    except Exception as e:
        logger.exception('ML utilities import failed')
        print('Failed to import ML utilities:', e, file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        print(f'Training profit model for business_id={business_id}...')
        model, metrics, features = train_profit_model(db, business_id)
        print('Training complete.')
        print(f"R²: {metrics.get('r2'):.4f}    MAE: {metrics.get('mae'):.4f}")
        # save the model
        save_profit_model(model, business_id, features, metrics)
        print('Model and metadata saved to backend/ml/models/')
    except Exception as e:
        logger.exception('Training failed')
        print('Training failed:', e, file=sys.stderr)
        sys.exit(2)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == '__main__':
    # allow overriding business id via CLI arg
    bid = 3
    if len(sys.argv) > 1:
        try:
            bid = int(sys.argv[1])
        except Exception:
            print('Invalid business_id argument; using default 3')
    main(bid)
