from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.get('/weekly/{business_id}')
def weekly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure access via business-specific role
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    return crud.analytics_weekly(db, business_id)


@router.get('/monthly/{business_id}')
def monthly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    return crud.analytics_monthly(db, business_id)



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
