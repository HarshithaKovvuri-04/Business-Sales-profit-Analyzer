from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.get('/weekly/{business_id}')
def weekly_report(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # staff must not view reports or transaction history
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    rpt = crud.report_weekly(db, business_id)
    # include COGS for owner calculations: net_profit = income - cogs - operating_expense
    if role == 'owner':
        try:
            # Recompute week boundaries to query ml_transactions for COGS in the same window
            from datetime import datetime, timedelta
            from sqlalchemy import text
            now = datetime.utcnow()
            start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            start = start_of_week.date()
            end = (start_of_week + timedelta(days=7)).date()
            cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid AND date >= :start AND date < :end"), {'bid': business_id, 'start': start, 'end': end}).fetchone()
            cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))
        except Exception:
            cogs = 0.0
        # operating_expense is the transaction-sourced expense from the weekly report
        operating_expense = float(rpt.get('total_expense') or 0.0)
        display_expense = operating_expense + (cogs or 0.0)
        rpt['operating_expense'] = operating_expense
        rpt['cogs'] = cogs
        rpt['total_expense'] = display_expense
        rpt['net_profit'] = float(rpt.get('total_income', 0.0)) - (cogs or 0.0) - operating_expense
    return rpt


@router.get('/monthly/{business_id}')
def monthly_report(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # staff must not view reports or transaction history
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    rpt = crud.report_monthly(db, business_id)
    if role == 'owner':
        try:
            from datetime import datetime
            from sqlalchemy import text
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year+1, month=1, day=1)
            else:
                # increment month
                nm = month_start.month + 1
                ny = month_start.year
                next_month = month_start.replace(month=nm, year=ny, day=1)
            cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid AND month >= :mstart AND month < :mend"), {'bid': business_id, 'mstart': month_start.strftime('%Y-%m'), 'mend': next_month.strftime('%Y-%m')}).fetchone()
            cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))
        except Exception:
            cogs = 0.0
        operating_expense = float(rpt.get('total_expense') or 0.0)
        display_expense = operating_expense + (cogs or 0.0)
        rpt['operating_expense'] = operating_expense
        rpt['cogs'] = cogs
        rpt['total_expense'] = display_expense
        rpt['net_profit'] = float(rpt.get('total_income', 0.0)) - (cogs or 0.0) - operating_expense
    return rpt
