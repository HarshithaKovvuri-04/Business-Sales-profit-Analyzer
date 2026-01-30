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
    if role == 'owner':
        rpt['net_profit'] = rpt['total_income'] - rpt['total_expense']
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
        rpt['net_profit'] = rpt['total_income'] - rpt['total_expense']
    return rpt
