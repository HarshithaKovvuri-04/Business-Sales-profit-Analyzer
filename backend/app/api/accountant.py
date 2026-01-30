from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..api.deps import get_db_dep, get_current_user
from .. import crud

router = APIRouter()


@router.get('/financials/overview')
def financials_overview(business_id: int, db: Session = Depends(get_db_dep), current_user = Depends(get_current_user)):
    # strictly allow only users who are assigned the 'accountant' role for the business
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role != 'accountant':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')

    # Aggregated, read-only financial views (derived from transactions only)
    weekly = crud.report_weekly(db, business_id)
    monthly = crud.report_monthly(db, business_id)
    summary = crud.summary_for_business(db, business_id)
    expense_breakdown = crud.categories_by_business(db, business_id)
    pl_monthly = crud.analytics_monthly(db, business_id)

    net_profit = float(summary.get('income', 0.0)) - float(summary.get('expense', 0.0))

    return {
        'weekly_summary': weekly,
        'monthly_summary': monthly,
        'expense_breakdown': expense_breakdown,
        'net_profit': net_profit,
        'summary_totals': summary,
        'pl_monthly': pl_monthly,
    }
