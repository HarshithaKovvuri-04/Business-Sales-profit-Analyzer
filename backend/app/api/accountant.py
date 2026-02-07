from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from ..api.deps import get_db_dep, get_current_user
from .. import crud

router = APIRouter()


@router.get('/financials/overview')
def financials_overview(business_id: int, db: Session = Depends(get_db_dep), current_user = Depends(get_current_user)):
    # strictly allow only users who are assigned the 'accountant' role for the business
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role != 'accountant':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')

    # Aggregated, read-only financial views
    weekly = crud.report_weekly(db, business_id)
    monthly = crud.report_monthly(db, business_id)
    # summary_for_business is transaction-only; compute authoritative totals here
    # Revenue and operating expense from transactions (safe COALESCE in SQL)
    try:
        rev_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS revenue FROM transactions WHERE business_id = :bid AND type = 'Income'"), {'bid': business_id}).fetchone()
        total_income = float(rev_row._mapping['revenue'] if hasattr(rev_row, '_mapping') else (rev_row[0] if rev_row and len(rev_row) > 0 else 0.0))
    except Exception:
        total_income = 0.0
    try:
        exp_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS expenses FROM transactions WHERE business_id = :bid AND type = 'Expense'"), {'bid': business_id}).fetchone()
        operating_expense = float(exp_row._mapping['expenses'] if hasattr(exp_row, '_mapping') else (exp_row[0] if exp_row and len(exp_row) > 0 else 0.0))
    except Exception:
        operating_expense = 0.0
    try:
        cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid"), {'bid': business_id}).fetchone()
        cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))
    except Exception:
        cogs = 0.0

    # Display expense = operating_expense + cogs
    display_expense = (operating_expense or 0.0) + (cogs or 0.0)

    # Build expense_breakdown for accountant: prefer operating expense categories,
    # but fall back to COGS-by-category when no Expense transactions exist.
    expense_breakdown = crud.categories_for_accountant(db, business_id)

    # Build monthly P&L (use analytics_monthly for continuity, then merge COGS per month)
    pl_monthly = crud.analytics_monthly(db, business_id)
    try:
        ml_rows = db.execute(text("SELECT month, COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid GROUP BY month ORDER BY month ASC"), {'bid': business_id}).fetchall()
        cogs_map = {}
        for row in ml_rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            mon = mapping.get('month')
            cogs_map[mon] = float(mapping.get('cogs') or 0.0)
    except Exception:
        cogs_map = {}

    # For each monthly row, replace expense with operating_expense + cogs for that month
    pl_out = []
    for m in pl_monthly:
        mon = m.get('month')
        monthly_oper = float(m.get('expense') or 0.0)
        monthly_cogs = float(cogs_map.get(mon) or 0.0)
        monthly_display = monthly_oper + monthly_cogs
        pl_out.append({'month': mon, 'income': float(m.get('income') or 0.0), 'expense': float(monthly_display)})

    # Monthly summary (current month): merge report_monthly with current-month COGS
    try:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year+1, month=1, day=1)
        else:
            nm = month_start.month + 1
            ny = month_start.year
            next_month = month_start.replace(month=nm, year=ny, day=1)
        # use the ml_transactions.month string for matching
        mstr = month_start.strftime('%Y-%m')
        cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid AND month = :m"), {'bid': business_id, 'm': mstr}).fetchone()
        month_cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))
    except Exception:
        month_cogs = 0.0

    monthly_summary = {
        'total_income': float(monthly.get('total_income') or 0.0),
        'operating_expense': float(monthly.get('total_expense') or 0.0),
        'cogs': month_cogs,
        'total_expense': float((monthly.get('total_expense') or 0.0) + (month_cogs or 0.0))
    }

    net_profit = float(total_income or 0.0) - (cogs or 0.0) - (operating_expense or 0.0)

    return {
        'weekly_summary': weekly,
        'monthly_summary': monthly_summary,
        'expense_breakdown': expense_breakdown,
        'net_profit': net_profit,
        'summary_totals': {'income': total_income, 'expense': operating_expense},
        'pl_monthly': pl_out,
    }
