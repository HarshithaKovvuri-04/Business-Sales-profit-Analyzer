from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .deps import get_db_dep, get_current_user
from .. import crud

router = APIRouter()


@router.post('/query')
def chat_query(business_id: int, question: str, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    """Simple role-restricted chatbot query endpoint.

    This endpoint enforces strict role-based access: owners may ask any
    question; accountants may ask financial questions (but not ML predictions);
    staff may ask operational/inventory availability questions only.
    """
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')

    q = (question or '').strip().lower()
    # classify question intent using simple keyword heuristics
    financial_keywords = ('revenue', 'income', 'expense', 'profit', 'p&l', 'pnl', 'tax', 'cash flow', 'balance')
    ml_keywords = ('predict', 'prediction', 'forecast', 'model', 'ml', 'ai')
    inventory_keywords = ('inventory', 'stock', 'quantity', 'low-stock', 'low stock', 'available', 'availability')

    is_financial = any(k in q for k in financial_keywords)
    is_ml = any(k in q for k in ml_keywords)
    is_inventory = any(k in q for k in inventory_keywords)

    # Owner: full access
    if role == 'owner':
        return {'status': 'ok', 'answer': 'Chat access granted for owner (data access omitted in test implementation).'}

    # Accountant: allow only financial questions (but not ML predictions)
    if role == 'accountant':
        if is_ml:
            raise HTTPException(status_code=403, detail='Accountants are not allowed to request ML predictions')
        if is_financial:
            return {'status': 'ok', 'answer': 'Financial chatbot access granted to accountant (data omitted).'}
        raise HTTPException(status_code=403, detail='Accountants may only ask financial questions')

    # Staff: only inventory/operational questions
    if role == 'staff':
        if is_inventory:
            return {'status': 'ok', 'answer': 'Inventory chatbot access granted to staff (data omitted).'}
        raise HTTPException(status_code=403, detail='Staff may only ask operational or inventory availability questions')

    raise HTTPException(status_code=403, detail='Not authorized')
