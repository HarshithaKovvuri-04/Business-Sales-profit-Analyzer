from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from .deps import get_db_dep, get_current_user
from typing import Optional
import os

router = APIRouter()


@router.post('', response_model=schemas.TransactionOut)
def create_transaction(tx_in: schemas.TransactionCreate, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure business belongs to user (owner or member)
    from ..models import Business, BusinessMember
    biz = db.query(Business).filter(Business.id == tx_in.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # allow owner or members (accountant/staff) to create transactions
    role = crud.get_user_business_role(db, current_user.id, tx_in.business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    return crud.create_transaction(db, tx_in.business_id, tx_in.type, tx_in.amount, tx_in.category)


@router.post('/upload')
def upload_invoice(business_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # Save uploaded file to backend/uploads/<business_id>/ and return URL path
    from ..models import Business, BusinessMember
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # allow owner or any member (accountant/staff) to upload invoices
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized')
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
    uploads_dir = os.path.abspath(uploads_dir)
    os.makedirs(uploads_dir, exist_ok=True)
    business_dir = os.path.join(uploads_dir, str(business_id))
    os.makedirs(business_dir, exist_ok=True)
    filename = f"{int(__import__('time').time())}_{file.filename}"
    path = os.path.join(business_dir, filename)
    with open(path, 'wb') as f:
        f.write(file.file.read())
    # return a path relative to server root
    return {'invoice_url': f'/uploads/{business_id}/{filename}'}


@router.get('', response_model=list[schemas.TransactionOut])
def list_transactions(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    from ..models import Business, BusinessMember
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized')
    # owners and members (accountant/staff) can view transactions
    return crud.list_transactions_for_business(db, business_id)


@router.put('/{tx_id}', response_model=schemas.TransactionOut)
def update_transaction_route(tx_id: int, tx_in: schemas.TransactionUpdate, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # only owner can edit
    tx = db.query(models.Transaction).filter(models.Transaction.id==tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail='Transaction not found')
    biz = db.query(models.Business).filter(models.Business.id==tx.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # only the business owner may edit transactions
    if biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Only owner may edit transactions')
    updated = crud.update_transaction(db, tx_id, type=tx_in.type, amount=tx_in.amount, category=tx_in.category, invoice_url=tx_in.invoice_url)
    if not updated:
        raise HTTPException(status_code=404)
    return updated


@router.delete('/{tx_id}')
def delete_transaction_route(tx_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    tx = db.query(models.Transaction).filter(models.Transaction.id==tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail='Transaction not found')
    biz = db.query(models.Business).filter(models.Business.id==tx.business_id).first()
    # only the business owner may delete transactions
    if not biz or biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Only owner may delete transactions')
    ok = crud.delete_transaction(db, tx_id)
    return {'deleted': ok}
