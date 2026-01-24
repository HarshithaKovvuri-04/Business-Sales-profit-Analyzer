from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.post('', response_model=schemas.BusinessOut)
def create_business(b_in: schemas.BusinessCreate, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    return crud.create_business(db, current_user.id, b_in.name, b_in.industry)


@router.get('', response_model=list[schemas.BusinessWithRole])
def list_businesses(db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # return businesses the user owns or is a member of, including role for current user
    bs = crud.list_businesses_for_user(db, current_user.id)
    out = []
    for b in bs:
        role = crud.get_user_business_role(db, current_user.id, b.id)
        out.append({
            'id': b.id,
            'owner_id': b.owner_id,
            'name': b.name,
            'industry': b.industry,
            'created_at': b.created_at,
            'role': role
        })
    return out


@router.post('/{business_id}/members', response_model=schemas.MemberOut)
def add_member(business_id: int, m_in: schemas.MemberAdd, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # only owner of business can add members
    from ..models import Business
    biz = crud.get_business(db, business_id)
    if not biz or biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized')

    # find user by username
    user = crud.get_user_by_username(db, m_in.username)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    # prevent duplicate membership
    existing = crud.get_member(db, business_id, user.id)
    if existing:
        raise HTTPException(status_code=400, detail='User is already a member')

    role = (m_in.role or '').lower()
    if role not in {'accountant', 'staff'}:
        raise HTTPException(status_code=400, detail="Invalid member role. valid: 'accountant', 'staff'")

    m = crud.add_member(db, business_id, user.id, role)
    return {
        'id': m.id,
        'business_id': m.business_id,
        'user_id': m.user_id,
        'role': m.role,
        'username': user.username
    }


@router.get('/{business_id}/members', response_model=list[schemas.MemberOut])
def list_members_route(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # only owner can view members
    biz = crud.get_business(db, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    if biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized')
    ms = crud.list_members(db, business_id)
    # enrich with username
    out = []
    for m in ms:
        out.append({'id': m.id, 'business_id': m.business_id, 'user_id': m.user_id, 'role': m.role, 'username': getattr(m.user, 'username', None)})
    return out


@router.delete('/{business_id}/members/{user_id}')
def delete_member_route(business_id: int, user_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    biz = crud.get_business(db, business_id)
    if not biz:
        raise HTTPException(status_code=404, detail='Business not found')
    if biz.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail='Not authorized')
    ok = crud.delete_member(db, business_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Member not found')
    return {'status':'ok'}


@router.get('/{business_id}/dashboard', response_model=schemas.DashboardOut)
def dashboard(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # determine role relative to business
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        # distinguish not found vs forbidden
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    biz = crud.get_business(db, business_id)
    summary = crud.summary_for_business(db, business_id)
    tx_count = crud.transactions_count_for_business(db, business_id)

    if role == 'owner':
        return {
            'total_income': summary['income'],
            'total_expense': summary['expense'],
            'net_profit': summary['income'] - summary['expense'],
            'transactions_count': tx_count,
            'business_name': biz.name,
            'role': role
        }
    elif role == 'accountant':
        return {
            'total_income': summary['income'],
            'total_expense': summary['expense'],
            'business_name': biz.name,
            'role': role
        }
    else:
        # staff
        return {
            'transactions_count': tx_count,
            'business_name': biz.name,
            'role': role
        }
