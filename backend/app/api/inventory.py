from fastapi import APIRouter, Depends, HTTPException
from ..core.config import settings
import logging
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .. import schemas, crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.post('', response_model=schemas.InventoryOut, status_code=201)
def create_inventory(item_in: dict, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business
    # Accept flexible payloads from clients; perform explicit parsing and
    # validation here to return clear 400 errors instead of 422. This
    # prevents Unprocessable Entity logs when clients send slightly
    # malformed values (empty strings, etc.).
    try:
        business_id = int(item_in.get('business_id'))
        item_name = str(item_in.get('item_name') or '').strip()
        quantity_raw = item_in.get('quantity')
        cost_price_raw = item_in.get('cost_price')
        category = item_in.get('category')
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid request payload')

    # ensure business exists
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=400, detail='Business not found')
    # ensure current user is owner
    if biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized for this business')

    # parse and validate numeric fields with friendly errors
    try:
        quantity = int(quantity_raw)
    except Exception:
        raise HTTPException(status_code=400, detail='quantity must be an integer')
    try:
        cost_price = float(cost_price_raw)
    except Exception:
        raise HTTPException(status_code=400, detail='cost_price must be a number')

    if quantity <= 0:
        raise HTTPException(status_code=400, detail='quantity must be greater than 0')
    if cost_price < 0:
        raise HTTPException(status_code=400, detail='cost_price must be >= 0')

    try:
        inv = crud.create_inventory(db, business_id, item_name, quantity, cost_price, category)
        return inv
    except IntegrityError as ie:
        logging.exception('Integrity error in create_inventory endpoint')
        try:
            db.rollback()
        except Exception:
            logging.exception('Error rolling back DB after integrity error')
        detail = str(ie.orig) if getattr(ie, 'orig', None) is not None else 'Integrity error'
        raise HTTPException(status_code=400, detail=detail)
    except ValueError as ve:
        logging.info('Validation failure creating inventory: %s', ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        logging.exception('Unexpected error in create_inventory endpoint')
        try:
            db.rollback()
        except Exception:
            logging.exception('Error rolling back DB after unexpected error')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('', response_model=list[schemas.InventoryOut])
def list_inventory(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business
    biz = db.query(Business).filter(Business.id == business_id, Business.owner_id == current_user.id).first()
    if not biz:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.list_inventory_for_business(db, business_id)


@router.get('/available', response_model=list[schemas.InventoryOut])
def list_available_inventory(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # owners and members can view available inventory
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.list_available_inventory_for_business(db, business_id)


@router.get('/low_stock', response_model=list[schemas.InventoryOut])
def low_stock_items(business_id: int, threshold: int | None = None, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    """Return inventory items with quantity below `threshold` for a business.

    Threshold defaults to application configuration; owners and members can view.
    """
    from ..models import Business
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    th = int(threshold) if threshold is not None else getattr(settings, 'LOW_STOCK_THRESHOLD', 5)
    try:
        items = crud.list_low_stock_for_business(db, business_id, th)
        return items
    except Exception:
        logging.exception('Error fetching low stock items')
        raise HTTPException(status_code=500, detail='Internal server error')
