from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response
from io import BytesIO
import logging
from sqlalchemy.orm import Session
from .. import schemas, crud, models
from .deps import get_db_dep, get_current_user
from typing import Optional
import os
from datetime import datetime

router = APIRouter()


@router.get("/{transaction_id}/receipt")
def transaction_receipt(transaction_id: int, db: Session = Depends(get_db_dep), current_user: models.User = Depends(get_current_user)):
    from ..models import Transaction, Business, Inventory

    try:
        # STEP 1 — safe transaction fetch
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail='Transaction not found')

        # business must exist
        biz = db.query(Business).filter(Business.id == transaction.business_id).first()
        if not biz:
            raise HTTPException(status_code=404, detail='Business not found')

        # verify user has access to this business (owner, accountant, or staff allowed)
        role_for_business = crud.get_user_business_role(db, current_user.id, biz.id)
        allowed_roles = {'owner', 'accountant', 'staff'}
        if role_for_business is None or role_for_business not in allowed_roles:
            raise HTTPException(status_code=403, detail='Not authorized for this business')

        # STEP 2 — safely load inventory
        inventory = None
        item_name = 'Manual Transaction'
        cost_price = 0.0
        if transaction.inventory_id:
            inventory = db.query(Inventory).filter(Inventory.id == transaction.inventory_id).first()
        if inventory:
            item_name = inventory.item_name or item_name
            cost_price = float(inventory.cost_price or 0.0)
        else:
            item_name = 'Manual Transaction'
            cost_price = 0.0

        # STEP 3 — safe numeric calculations
        quantity = int(transaction.used_quantity or 1)
        selling_price = float(transaction.amount or 0.0)
        try:
            profit = selling_price - (quantity * cost_price)
        except Exception:
            profit = 0.0

        # STEP 4 — protect role access: use the per-business role (owner/accountant/staff)
        role = role_for_business
        show_cost = role in ['owner', 'accountant']
        show_profit = role in ['owner', 'accountant']

        # STEP 5 — safe PDF generation
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
        except ImportError:
            logging.exception('ReportLab import failed')
            raise HTTPException(status_code=500, detail='PDF generation dependency missing (reportlab)')

        buffer = BytesIO()
        try:
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph('Transaction Receipt', styles['Title']))
            elements.append(Spacer(1, 12))

            elements.append(Paragraph(f'Business: {biz.name}', styles['Normal']))
            elements.append(Paragraph(f'Transaction ID: {transaction.id}', styles['Normal']))
            elements.append(Paragraph(f'Date: {transaction.created_at.isoformat() if transaction.created_at is not None else ""}', styles['Normal']))
            elements.append(Spacer(1, 8))

            elements.append(Paragraph(f'Item: {item_name}', styles['Normal']))
            elements.append(Paragraph(f'Quantity: {quantity}', styles['Normal']))
            elements.append(Paragraph(f'Selling Price: ₹{selling_price:.2f}', styles['Normal']))
            elements.append(Paragraph(f'Total Amount: ₹{selling_price:.2f}', styles['Normal']))

            if show_cost:
                elements.append(Paragraph(f'Cost Price: ₹{cost_price:.2f}', styles['Normal']))

            if show_profit:
                elements.append(Paragraph(f'Profit: ₹{profit:.2f}', styles['Normal']))

            doc.build(elements)
            buffer.seek(0)
            pdf_data = buffer.getvalue()
        except Exception as e:
            logging.exception('Receipt generation failed for tx %s', transaction_id)
            raise HTTPException(status_code=500, detail='Receipt generation failed')
        finally:
            try:
                buffer.close()
            except Exception:
                pass

        # STEP 6 — return response
        return Response(
            pdf_data,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=transaction_{transaction_id}.pdf'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        # STEP 7 — add error logging
        logging.exception('Receipt generation failed unexpectedly')
        raise HTTPException(status_code=500, detail=str(e))


@router.post('', status_code=status.HTTP_201_CREATED)
def create_transaction(tx_in: schemas.TransactionCreate, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure business belongs to user (owner or member)
    from ..models import Business, BusinessMember
    biz = db.query(Business).filter(Business.id == tx_in.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # allow only owner or staff to create transactions; accountants are denied
    role = crud.get_user_business_role(db, current_user.id, tx_in.business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized for this business')
    if role == 'accountant':
        # accountants are not allowed to perform sales entry or inventory updates
        raise HTTPException(status_code=403, detail='Accountants are not allowed to create transactions')
    # if inventory info provided, use inventory-aware creation
    # create using the canonical CRUD functions so behavior matches for owner and staff
    try:
        if tx_in.inventory_id is not None or tx_in.used_quantity is not None or tx_in.source is not None:
            tx = crud.create_transaction_with_inventory(db, tx_in.business_id, tx_in.type, tx_in.amount, tx_in.category, inventory_id=tx_in.inventory_id, used_quantity=tx_in.used_quantity, source=tx_in.source)
        else:
            tx = crud.create_transaction(db, tx_in.business_id, tx_in.type, tx_in.amount, tx_in.category)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Ensure staff-created transactions have created_at defaulted to now (server time)
    if role == 'staff':
        try:
            # overwrite created_at to server now to ensure 'today' semantics for staff
            tx.created_at = datetime.utcnow()
            db.add(tx)
            db.commit()
            db.refresh(tx)
        except Exception:
            db.rollback()
            # If we cannot update timestamp, still do not leak transaction data
        return {'detail': 'Transaction created'}
    return tx


@router.post('/upload')
def upload_invoice(business_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # Save uploaded file to backend/uploads/<business_id>/ and return URL path
    from ..models import Business, BusinessMember
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    # allow only owner to upload invoices; accountants and staff are denied
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized')
    if role != 'owner':
        raise HTTPException(status_code=403, detail='Only owner may upload invoices')
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
    # only owners and accountants may view transactions
    if role in ('owner', 'accountant'):
        return crud.list_transactions_for_business(db, business_id)
    # staff are not allowed to view any transaction history
    raise HTTPException(status_code=403, detail='Not authorized')


@router.get('/list')
def list_transactions_joined(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    """Return transactions joined with inventory item names for display.

    Returns JSON objects: date(created_at), item_name, used_quantity, amount, type
    """
    from sqlalchemy import select
    from ..models import Transaction, Inventory
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        raise HTTPException(status_code=403, detail='Not authorized')
    # allow staff to list transactions for their business (frontend will hide sensitive columns)
    q = (
        db.query(
            Transaction.id.label('id'),
            Transaction.created_at.label('created_at'),
            Inventory.item_name.label('item_name'),
            Transaction.used_quantity,
            Transaction.amount,
            Transaction.type,
            Transaction.category,
            Transaction.invoice_url,
            Transaction.source,
            Transaction.inventory_id
        )
        .join(Inventory, Transaction.inventory_id == Inventory.id, isouter=True)
        .filter(Transaction.business_id == business_id)
        .order_by(Transaction.created_at.desc())
    )
    results = q.all()
    out = []
    for r in results:
        out.append({
            'id': int(r.id),
            'created_at': r.created_at.isoformat() if r.created_at is not None else None,
            'item_name': r.item_name,
            'used_quantity': int(r.used_quantity or 0),
            'amount': float(r.amount or 0.0),
            'type': str(r.type) if r.type is not None else None,
            'category': r.category,
            'invoice_url': r.invoice_url,
            'source': r.source,
            'inventory_id': int(r.inventory_id) if r.inventory_id is not None else None
        })
    return out


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
    try:
        updated = crud.update_transaction(db, tx_id, type=tx_in.type, amount=tx_in.amount, category=tx_in.category, invoice_url=tx_in.invoice_url, inventory_id=tx_in.inventory_id, used_quantity=tx_in.used_quantity, source=tx_in.source)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
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
    try:
        ok = crud.delete_transaction(db, tx_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    return {'deleted': ok}
