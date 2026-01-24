from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.post('', response_model=schemas.InventoryOut)
def create_inventory(item_in: schemas.InventoryCreate, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business
    biz = db.query(Business).filter(Business.id == item_in.business_id, Business.owner_id == current_user.id).first()
    if not biz:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.create_inventory(db, item_in.business_id, item_in.item_name, item_in.quantity, item_in.cost_price)


@router.get('', response_model=list[schemas.InventoryOut])
def list_inventory(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business
    biz = db.query(Business).filter(Business.id == business_id, Business.owner_id == current_user.id).first()
    if not biz:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.list_inventory_for_business(db, business_id)
