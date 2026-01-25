from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud
from .deps import get_db_dep, get_current_user
import logging

router = APIRouter()


@router.get('/weekly/{business_id}')
def weekly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure access via business-specific role
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # produce chart-ready structure: { labels: [...], income: [...], expense: [...] }
    raw = crud.analytics_weekly(db, business_id)
    labels = []
    income = []
    expense = []
    for item in raw:
        # prefer ISO date if present, otherwise fall back to label
        d = item.get('date') if isinstance(item, dict) and item.get('date') else item.get('label') if isinstance(item, dict) else None
        labels.append(d)
        income.append(float(item.get('income') or 0))
        expense.append(float(item.get('expense') or 0))
    # ensure arrays lengths match; pad with sensible defaults if not
    maxlen = max(len(labels), len(income), len(expense))
    if len(labels) < maxlen:
        labels.extend([''] * (maxlen - len(labels)))
    if len(income) < maxlen:
        income.extend([0.0] * (maxlen - len(income)))
    if len(expense) < maxlen:
        expense.extend([0.0] * (maxlen - len(expense)))
    logger = logging.getLogger(__name__)
    logger.info('analytics.weekly labels=%s income=%s expense=%s', labels, income, expense)
    return {'labels': labels, 'income': income, 'expense': expense}


@router.get('/monthly/{business_id}')
def monthly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    raw = crud.analytics_monthly(db, business_id)
    labels = []
    income = []
    expense = []
    for item in raw:
        d = item.get('date') if isinstance(item, dict) and item.get('date') else item.get('label') if isinstance(item, dict) else None
        labels.append(d)
        income.append(float(item.get('income') or 0))
        expense.append(float(item.get('expense') or 0))
    maxlen = max(len(labels), len(income), len(expense))
    if len(labels) < maxlen:
        labels.extend([''] * (maxlen - len(labels)))
    if len(income) < maxlen:
        income.extend([0.0] * (maxlen - len(income)))
    if len(expense) < maxlen:
        expense.extend([0.0] * (maxlen - len(expense)))
    logger = logging.getLogger(__name__)
    logger.info('analytics.monthly labels=%s income=%s expense=%s', labels, income, expense)
    return {'labels': labels, 'income': income, 'expense': expense}



@router.get('/categories/{business_id}')
def categories(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    return crud.categories_by_business(db, business_id)


@router.get('/profit/{business_id}')
def profit_trend(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # only owner can request profit trend
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    if role != 'owner':
        raise HTTPException(status_code=403, detail='Only owner may view profit trend')
    monthly = crud.analytics_monthly(db, business_id)
    return [{'month': m.get('label') if isinstance(m, dict) and 'label' in m else m.get('month') if isinstance(m, dict) else None,
             'profit': (m.get('income', 0) - m.get('expense', 0)) if isinstance(m, dict) else 0} for m in monthly]
