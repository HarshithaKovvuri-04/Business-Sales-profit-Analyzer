from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .. import crud
from .deps import get_db_dep, get_current_user
import logging

router = APIRouter()


@router.get('/summary/{business_id}')
def summary(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # Read canonical totals from analytics_summary view only.
    try:
        sql = text("SELECT total_sales, total_cost, total_profit FROM analytics_summary WHERE business_id = :bid")
        row = db.execute(sql, {'bid': business_id}).fetchone()
        if not row:
            return {'total_income': 0.0, 'total_expense': 0.0, 'profit': 0.0}
        # support RowMapping or tuple-like rows
        mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
        total_sales = float(mapping.get('total_sales') or mapping.get(0) or 0.0)
        total_cost = float(mapping.get('total_cost') or mapping.get(1) or 0.0)
        total_profit = float(mapping.get('total_profit') or mapping.get(2) or 0.0)
        return {'total_income': total_sales, 'total_expense': total_cost, 'profit': total_profit}
    except Exception:
        logging.exception('Error fetching analytics summary for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching analytics summary')


@router.get('/charts/{business_id}')
def charts(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    logger = logging.getLogger(__name__)
    try:
        income_vs_expense = crud.charts_income_expense_by_date(db, business_id)
        top_selling = crud.top_selling_items(db, business_id)
        category_sales = crud.category_sales(db, business_id)
        return {'income_vs_expense': income_vs_expense, 'top_selling': top_selling, 'category_sales': category_sales}
    except Exception as e:
        logger.exception('Error generating charts for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while generating charts')


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
    logger = logging.getLogger(__name__)
    try:
        sql = text("SELECT month, sales, cost, profit FROM analytics_monthly WHERE business_id = :bid ORDER BY month ASC")
        rows = db.execute(sql, {'bid': business_id}).fetchall()
        out = []
        for row in rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            month = mapping.get('month')
            # ensure month is serializable (string)
            if month is not None and not isinstance(month, str):
                try:
                    month = str(month)
                except Exception:
                    month = mapping.get('month')
            sales = mapping.get('sales') or 0.0
            cost = mapping.get('cost') or 0.0
            profit = mapping.get('profit') or 0.0
            out.append({
                'month': month,
                'income': float(sales),
                'expense': float(cost),
                'profit': float(profit)
            })
        return out
    except Exception:
        logger.exception('Error fetching monthly analytics for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching monthly analytics')


@router.get('/top-items/{business_id}')
def top_items(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure access via business-specific role
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    logger = logging.getLogger(__name__)
    try:
        sql = text("SELECT * FROM analytics_top_items WHERE business_id = :bid")
        rows = db.execute(sql, {'bid': business_id}).fetchall()
        out = []
        for row in rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            rec = {}
            for k, v in mapping.items():
                try:
                    rec[k] = float(v) if hasattr(v, 'as_tuple') or isinstance(v, (int, float)) and not isinstance(v, bool) and not isinstance(v, str) else v
                except Exception:
                    rec[k] = v
            out.append(rec)
        return out
    except Exception:
        logger.exception('Error fetching top items for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching top items')



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
    # Provide aggregate totals as a safe, numeric response for owners.
    logger = logging.getLogger(__name__)
    try:
        s = crud.summary_for_business(db, business_id) or {}
        income = float(s.get('income') or 0.0)
        expense = float(s.get('expense') or 0.0)
        return {'total_income': income, 'total_expense': expense, 'profit': income - expense}
    except Exception:
        logger.exception('Error computing profit totals for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while computing profit')


@router.get('/profit_trend/{business_id}')
def profit_trend_series(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # Return per-month profit series for plotting; kept separate to avoid
    # changing the totals contract used by other integrations.
    logger = logging.getLogger(__name__)
    try:
        monthly = crud.analytics_monthly(db, business_id)
        out = []
        for m in monthly:
            mon = m.get('month') if isinstance(m, dict) else None
            income = float(m.get('income', 0) if isinstance(m, dict) else 0)
            expense = float(m.get('expense', 0) if isinstance(m, dict) else 0)
            out.append({'month': mon, 'profit': income - expense})
        return out
    except Exception:
        logger.exception('Error computing profit trend for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while computing profit trend')
