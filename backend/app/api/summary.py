from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.get('/{business_id}', response_model=schemas.SummaryOut)
def get_summary(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        # check if business exists
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.summary_for_business(db, business_id)
