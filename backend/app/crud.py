from sqlalchemy.orm import Session
from . import models, security
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from .db.session import engine


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, username: str, password: str, role: str = 'owner'):
    # normalize role and validate
    if role is None:
        role = 'owner'
    role_norm = role.lower()
    valid_roles = {r.value for r in models.RoleEnum}
    if role_norm not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. valid: {', '.join(sorted(valid_roles))}")

    hashed = security.get_password_hash(password)
    # use RoleEnum member to ensure database enum correctness
    try:
        role_member = models.RoleEnum(role_norm)
    except Exception:
        raise ValueError(f"Invalid role '{role}'. valid: {', '.join(sorted(valid_roles))}")

    db_user = models.User(username=username, password_hash=hashed, role=role_member)
    try:
        dialect = getattr(engine.dialect, 'name', None)
        logging.info('create_user: about to add user=%s role=%s db_dialect=%s', username, role_norm, dialect)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logging.info('create_user: commit successful id=%s username=%s', db_user.id, db_user.username)
        return db_user
    except IntegrityError as ie:
        logging.exception('Integrity error creating user')
        db.rollback()
        # bubble up a controlled error for the API layer
        raise ValueError('Username already registered')
    except Exception as e:
        logging.exception('Error creating user')
        db.rollback()
        raise


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password_hash):
        return None
    return user


def create_business(db: Session, owner_id: int, name: str, industry: str = None):
    b = models.Business(owner_id=owner_id, name=name, industry=industry)
    db.add(b); db.commit(); db.refresh(b)
    return b


def list_businesses_for_owner(db: Session, owner_id: int):
    return db.query(models.Business).filter(models.Business.owner_id == owner_id).all()


def list_businesses_for_user(db: Session, user_id: int):
    # return businesses owned by user or where user is a member
    from sqlalchemy import or_
    from .models import Business, BusinessMember
    member_subq = db.query(BusinessMember.business_id).filter(BusinessMember.user_id == user_id).subquery()
    return db.query(Business).filter(or_(Business.owner_id == user_id, Business.id.in_(member_subq))).all()


def get_user_business_role(db: Session, user_id: int, business_id: int):
    """Return 'owner' | 'accountant' | 'staff' or None depending on user's relation to the business."""
    b = db.query(models.Business).filter(models.Business.id == business_id).first()
    if not b:
        return None
    if b.owner_id == user_id:
        return 'owner'
    m = db.query(models.BusinessMember).filter(models.BusinessMember.business_id == business_id, models.BusinessMember.user_id == user_id).first()
    if m:
        return m.role
    return None


def create_transaction(db: Session, business_id: int, ttype: str, amount: float, category: str = None):
    tx = models.Transaction(business_id=business_id, type=ttype, amount=amount, category=category)
    db.add(tx); db.commit(); db.refresh(tx)
    return tx


def list_transactions_for_business(db: Session, business_id: int):
    return db.query(models.Transaction).filter(models.Transaction.business_id == business_id).order_by(models.Transaction.created_at.desc()).all()


def create_inventory(db: Session, business_id: int, item_name: str, quantity: int, cost_price: float):
    it = models.Inventory(business_id=business_id, item_name=item_name, quantity=quantity, cost_price=cost_price)
    db.add(it); db.commit(); db.refresh(it)
    return it


def list_inventory_for_business(db: Session, business_id: int):
    return db.query(models.Inventory).filter(models.Inventory.business_id == business_id).all()


def summary_for_business(db: Session, business_id: int):
    income = 0.0
    expense = 0.0
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id).all()
    for t in txs:
        if t.type.lower() == 'income':
            income += float(t.amount)
        else:
            expense += float(t.amount)
    return {'income': income, 'expense': expense}


def add_member(db: Session, business_id: int, user_id: int, role: str):
    m = models.BusinessMember(business_id=business_id, user_id=user_id, role=role)
    db.add(m); db.commit(); db.refresh(m)
    return m


def list_members(db: Session, business_id: int):
    return db.query(models.BusinessMember).filter(models.BusinessMember.business_id == business_id).all()


def get_business(db: Session, business_id: int):
    return db.query(models.Business).filter(models.Business.id == business_id).first()


def get_member(db: Session, business_id: int, user_id: int):
    return db.query(models.BusinessMember).filter(models.BusinessMember.business_id==business_id, models.BusinessMember.user_id==user_id).first()


def delete_member(db: Session, business_id: int, user_id: int):
    m = get_member(db, business_id, user_id)
    if not m:
        return False
    db.delete(m); db.commit()
    return True


def transactions_count_for_business(db: Session, business_id: int):
    return db.query(models.Transaction).filter(models.Transaction.business_id==business_id).count()


def update_transaction(db: Session, tx_id: int, **fields):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        return None
    for k, v in fields.items():
        if v is not None and hasattr(tx, k):
            setattr(tx, k, v)
    db.add(tx); db.commit(); db.refresh(tx)
    return tx


def delete_transaction(db: Session, tx_id: int):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        return False
    db.delete(tx); db.commit()
    return True


def change_user_password(db: Session, user_id: int, new_password: str):
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    pw_hash = security.get_password_hash(new_password)
    user.password_hash = pw_hash
    db.add(user); db.commit(); db.refresh(user)
    return True


def analytics_weekly(db: Session, business_id: int):
    # return list of last 7 days (Mon..Sun labels) with income and expense
    from datetime import datetime, timedelta
    end = datetime.utcnow()
    start = end - timedelta(days=6)
    # fetch transactions in the window and aggregate in Python to avoid SQL function compatibility issues
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= start).all()
    sums = {}
    for t in txs:
        d = t.created_at.date()
        entry = sums.setdefault(d, {'income': 0.0, 'expense': 0.0})
        if str(t.type).lower() == 'income':
            entry['income'] += float(t.amount)
        else:
            entry['expense'] += float(t.amount)
    out = []
    for i in range(7):
        d = (start + timedelta(days=i)).date()
        label = d.strftime('%a')
        s = sums.get(d, {'income': 0.0, 'expense': 0.0})
        out.append({'label': label, 'income': float(s['income']), 'expense': float(s['expense'])})
    return out


def analytics_monthly(db: Session, business_id: int):
    from datetime import datetime
    # fetch all transactions for the business and aggregate by month in Python
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id).all()
    sums = {}
    for t in txs:
        d = t.created_at
        mm = datetime(d.year, d.month, 1).date()
        entry = sums.setdefault(mm, {'income': 0.0, 'expense': 0.0})
        if str(t.type).lower() == 'income':
            entry['income'] += float(t.amount)
        else:
            entry['expense'] += float(t.amount)
    out = []
    now = datetime.utcnow()
    year = now.year
    month = now.month
    months = []
    for i in range(11, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))
    for y, m in months:
        d = datetime(y, m, 1).date()
        label = d.strftime('%b')
        s = sums.get(d, {'income': 0.0, 'expense': 0.0})
        out.append({'label': label, 'income': float(s['income']), 'expense': float(s['expense'])})
    return out


def categories_by_business(db: Session, business_id: int):
    # aggregate category expenses in Python to avoid SQL function issues
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.type == 'Expense').all()
    totals = {}
    for t in txs:
        cat = t.category or 'Uncategorized'
        totals[cat] = totals.get(cat, 0.0) + float(t.amount)
    out = [{'category': k, 'amount': float(v)} for k, v in sorted(totals.items(), key=lambda x: -x[1])]
    return out


def report_weekly(db: Session, business_id: int):
    """Return totals for the last 7 days (income, expense)."""
    from datetime import datetime, timedelta
    end = datetime.utcnow()
    start = end - timedelta(days=6)
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= start).all()
    income = 0.0
    expense = 0.0
    for t in txs:
        if str(t.type).lower() == 'income':
            income += float(t.amount)
        else:
            expense += float(t.amount)
    return {'total_income': income, 'total_expense': expense}


def report_monthly(db: Session, business_id: int):
    """Return totals for the current month (income, expense)."""
    from datetime import datetime
    now = datetime.utcnow()
    month_start = now.replace(day=1)
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= month_start).all()
    income = 0.0
    expense = 0.0
    for t in txs:
        if str(t.type).lower() == 'income':
            income += float(t.amount)
        else:
            expense += float(t.amount)
    return {'total_income': income, 'total_expense': expense}
