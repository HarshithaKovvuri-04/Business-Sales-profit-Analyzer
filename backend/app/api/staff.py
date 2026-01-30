from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..api.deps import get_db_dep, get_current_user
from .. import crud, models

router = APIRouter()


def _ensure_staff_for_business(db: Session, user, business_id: int):
    role = crud.get_user_business_role(db, user.id, business_id)
    if role != 'staff':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')


@router.get('/low_stock')
def low_stock_alerts(business_id: int, threshold: int = 5, db: Session = Depends(get_db_dep), current_user = Depends(get_current_user)):
    # Show low stock only for businesses the staff is assigned to (i.e. where they are a member)
    _ensure_staff_for_business(db, current_user, business_id)
    items = crud.list_low_stock_for_business(db, business_id, threshold)
    # Return read-only minimal inventory fields
    return [{'id': i.id, 'item_name': i.item_name, 'quantity': int(i.quantity), 'cost_price': float(i.cost_price or 0.0)} for i in items]


@router.post('/sales/today')
def add_sale_today():
    # Removed: staff must use the unified /transactions endpoint for creating transactions.
    raise HTTPException(status_code=status.HTTP_410_GONE, detail='Use /transactions to create sales')


@router.get('/stats/today')
def stats_today(business_id: int, db: Session = Depends(get_db_dep), current_user = Depends(get_current_user)):
    _ensure_staff_for_business(db, current_user, business_id)
    # Start of today in UTC
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= start).all()
    total_items_sold = 0
    tx_count = 0
    for t in txs:
        # Only count sales (income)
        try:
            if str(t.type).lower() in ('income', 'income'):
                total_items_sold += int(t.used_quantity or 0)
                tx_count += 1
        except Exception:
            continue
    return {'total_items_sold_today': int(total_items_sold), 'transactions_today': int(tx_count)}
