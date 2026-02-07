from sqlalchemy.orm import Session
from . import models, security
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, text
from .db.session import engine
from .models import TransactionTypeEnum


# NOTE: legacy helper `_tx_type_lower` removed. Use `_normalize_tx_type`
# which validates and normalizes Transaction types to the canonical
# strings 'income' or 'expense'. This avoids implicit assumptions and
# ensures all service-layer logic treats transaction kinds consistently.


def _normalize_tx_type(ttype) -> str:
    """Normalize a transaction type input to one of: 'income' or 'expense'.

    Accepts enum members or strings (case-insensitive). Raises ValueError
    for unknown types. This enforces the business rule that there are only
    two supported transaction kinds used throughout the service layer.
    """
    # accept enum-like objects with `.value`
    t = ttype
    if hasattr(ttype, 'value'):
        t = ttype.value
    if t is None:
        raise ValueError('Transaction type is required')
    tn = str(t).strip().lower()
    if tn in ('income',):
        return 'income'
    if tn in ('expense',):
        return 'expense'
    raise ValueError(f"Invalid transaction type '{ttype}'. allowed: Income, Expense")


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
    # Validate transaction type early and fail fast for invalid values.
    _ = _normalize_tx_type(ttype)
    # store original enum/string value into the DB model; SQLAlchemy will
    # coerce when using the SAEnum column type.
    tx = models.Transaction(business_id=business_id, type=ttype, amount=amount, category=category)
    db.add(tx); db.commit(); db.refresh(tx)
    return tx


def create_transaction_with_inventory(db: Session, business_id: int, ttype: str, amount: float, category: str = None, inventory_id: int = None, used_quantity: int = None, source: str = None):
    """Create a transaction and, if linked to inventory, adjust inventory atomically.

        Business rules (inventory stock behavior):
        - If a transaction has `source == 'inventory'`, `inventory_id` is set and
            `used_quantity > 0`, the inventory stock MUST be reduced by `used_quantity`.
        - Inventory rows are stock state only and MUST NOT be used to determine
            whether a transaction is Income or Expense, nor to compute transaction
            amounts for analytics.
    """
    try:
        # if linked to inventory, fetch and lock row first
        # Inventory update rules (strict):
        # - EXPENSE  = Purchasing inventory -> Money goes OUT, inventory QUANTITY INCREASES
        # - INCOME   = Selling inventory   -> Money comes IN, inventory QUANTITY DECREASES
        # Validation: only INCOME (sales) should check stock availability;
        # purchases (EXPENSE) must never fail due to low stock.
        tx_amount = amount
        if inventory_id is not None:
            inv = db.query(models.Inventory).filter(models.Inventory.id == inventory_id, models.Inventory.business_id == business_id).with_for_update().first()
            if not inv:
                raise ValueError('Inventory item not found')
            uq = int(used_quantity or 0)
            if uq < 0:
                raise ValueError('used_quantity must be non-negative')
            norm = _normalize_tx_type(ttype)
            if norm == 'income':
                # Selling items: ensure enough stock and then reduce
                if uq > 0:
                    if inv.quantity < uq:
                        raise ValueError('Insufficient inventory quantity')
                    inv.quantity = inv.quantity - uq
                    db.add(inv)
            elif norm == 'expense':
                # Purchasing items: increase stock (no availability check)
                if uq > 0:
                    inv.quantity = inv.quantity + uq
                    db.add(inv)
            # Ensure transaction.category is set from inventory when inventory is linked.
            # Preserve a provided non-empty category; otherwise use inventory.category.
            # If inventory.category is empty/null, fall back to 'Uncategorized' so
            # inventory-linked transactions never have a NULL category value.
            if category is None or (isinstance(category, str) and category.strip() == ''):
                inv_cat = getattr(inv, 'category', None)
                if isinstance(inv_cat, str) and inv_cat.strip() != '':
                    category = inv_cat
                else:
                    category = 'Uncategorized'
        tx = models.Transaction(business_id=business_id, type=ttype, amount=tx_amount, category=category, inventory_id=inventory_id, used_quantity=used_quantity or 0, source=source)
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return tx
    except Exception:
        db.rollback()
        raise


def list_transactions_for_business(db: Session, business_id: int):
    return db.query(models.Transaction).filter(models.Transaction.business_id == business_id).order_by(models.Transaction.created_at.desc()).all()


def create_inventory(db: Session, business_id: int, item_name: str, quantity: int, cost_price: float, category: str = None):
    # `cost_price` is the canonical per-unit cost for inventory items.
    if int(quantity) <= 0:
        raise ValueError('quantity must be greater than 0')
    if float(cost_price) < 0:
        raise ValueError('cost_price must be >= 0')
    it = models.Inventory(business_id=business_id, item_name=item_name, quantity=int(quantity), cost_price=cost_price, category=category)
    try:
        db.add(it)
        db.commit()
        db.refresh(it)
        return it
    except IntegrityError:
        logging.exception('Integrity error creating inventory')
        db.rollback()
        raise ValueError('Integrity error creating inventory')
    except Exception:
        logging.exception('Unexpected error creating inventory')
        db.rollback()
        raise


def list_low_stock_for_business(db: Session, business_id: int, threshold: int = 5):
    return db.query(models.Inventory).filter(models.Inventory.business_id == business_id, models.Inventory.quantity < threshold).all()


def list_inventory_for_business(db: Session, business_id: int):
    return db.query(models.Inventory).filter(models.Inventory.business_id == business_id).all()


def summary_for_business(db: Session, business_id: int):
    """Return separated totals. Unknown/invalid types are ignored to avoid
    accidentally mixing income and expense values.
    """
    income = 0.0
    expense = 0.0
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id).all()
    for t in txs:
        try:
            norm = _normalize_tx_type(t.type)
        except ValueError:
            # ignore unexpected transaction types
            continue
        if norm == 'income':
            income += float(t.amount)
        elif norm == 'expense':
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
    try:
        # handle inventory reconciliation by reversing the previous
        # inventory impact (if any) and then applying the new impact. We
        # restore previously consumed stock (if any) and then deduct the
        # new consumption. Per requirements, any inventory-linked
        # transaction that consumes `used_quantity` reduces stock. Thus:
        #  - restore old consumed quantity (add back)
        #  - deduct new consumed quantity (subtract)
        old_inv_id = tx.inventory_id
        old_used = int(tx.used_quantity or 0)
        # previous and new transaction types (may be Enum or str)
        old_type = tx.type
        new_type = fields.get('type', tx.type)
        new_inv_id = fields.get('inventory_id', old_inv_id)
        new_used = int(fields.get('used_quantity', old_used) or 0)

        # Reverse the previous transaction's inventory effect based on its type,
        # then apply the new transaction's effect based on the new type. Rules:
        # - EXPENSE = purchase -> original creation increased stock, so reversing
        #   a purchase must subtract that quantity (may fail if stock already used).
        # - INCOME = sale -> original creation decreased stock, so reversing a
        #   sale must add the quantity back.
        # Validation: only INCOME (sales) check availability when applying a
        # deduction; reversing a purchase may fail if stock has since been used.
        if old_inv_id is not None and old_used > 0:
            inv_old = db.query(models.Inventory).filter(models.Inventory.id == old_inv_id).with_for_update().first()
            if not inv_old:
                raise ValueError('Inventory item not found')
            old_norm = _normalize_tx_type(old_type)
            if old_norm == 'income':
                # previous was a sale: return items to stock
                inv_old.quantity = inv_old.quantity + old_used
            elif old_norm == 'expense':
                # previous was a purchase: undo purchase by subtracting
                if inv_old.quantity < old_used:
                    raise ValueError('Cannot reverse purchase; inventory already used')
                inv_old.quantity = inv_old.quantity - old_used
            db.add(inv_old)

        # Apply new effect
        if new_inv_id is not None and new_used > 0:
            inv_new = db.query(models.Inventory).filter(models.Inventory.id == new_inv_id).with_for_update().first()
            if not inv_new:
                raise ValueError('Inventory item not found')
            new_norm = _normalize_tx_type(new_type)
            if new_norm == 'income':
                # selling: ensure availability then decrease
                if inv_new.quantity < new_used:
                    raise ValueError('Insufficient inventory quantity for update')
                inv_new.quantity = inv_new.quantity - new_used
            elif new_norm == 'expense':
                # purchasing: increase stock
                inv_new.quantity = inv_new.quantity + new_used
            db.add(inv_new)

        # update fields; if transaction is inventory-linked expense, ensure amount is recalculated from cost_price
        for k, v in fields.items():
            if v is not None and hasattr(tx, k):
                setattr(tx, k, v)
        # Do NOT use inventory rows to override or compute transaction amounts.
        # Transaction.amount is authoritative for financial analytics.
        db.add(tx)
        db.commit(); db.refresh(tx)
        return tx
    except Exception:
        db.rollback()
        raise


def delete_transaction(db: Session, tx_id: int):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        return False
    try:
        # if transaction used inventory, reverse its effect based on type:
        # - INCOME (sale): previously decreased stock -> add used_quantity back
        # - EXPENSE (purchase): previously increased stock -> subtract used_quantity (ensure not negative)
        if tx.inventory_id is not None and int(tx.used_quantity or 0) > 0:
            inv = db.query(models.Inventory).filter(models.Inventory.id == tx.inventory_id).with_for_update().first()
            if inv:
                tx_norm = _normalize_tx_type(tx.type)
                if tx_norm == 'income':
                    inv.quantity = inv.quantity + int(tx.used_quantity or 0)
                elif tx_norm == 'expense':
                    if inv.quantity < int(tx.used_quantity or 0):
                        raise ValueError('Cannot delete purchase transaction: inventory already used')
                    inv.quantity = inv.quantity - int(tx.used_quantity or 0)
                db.add(inv)
        db.delete(tx)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def get_inventory_by_id(db: Session, inventory_id: int):
    return db.query(models.Inventory).filter(models.Inventory.id == inventory_id).first()


def list_available_inventory_for_business(db: Session, business_id: int):
    return db.query(models.Inventory).filter(models.Inventory.business_id == business_id, models.Inventory.quantity > 0).all()


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
    # IMPORTANT: aggregate strictly from `transactions` table only. Do NOT
    # consult inventory rows here — inventory represents stock state only.
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= start).all()
    sums = {}
    for t in txs:
        d = t.created_at.date()
        entry = sums.setdefault(d, {'income': 0.0, 'expense': 0.0})
        try:
            norm = _normalize_tx_type(t.type)
        except ValueError:
            # ignore unexpected transaction types
            continue
        if norm == 'income':
            entry['income'] += float(t.amount)
        elif norm == 'expense':
            entry['expense'] += float(t.amount)
    out = []
    for i in range(7):
        d = (start + timedelta(days=i)).date()
        label = d.strftime('%a')
        s = sums.get(d, {'income': 0.0, 'expense': 0.0})
        out.append({
            'date': d.isoformat(),
            'label': label,
            'income': float(s['income']),
            'expense': float(s['expense'])
        })
    return out


def analytics_monthly(db: Session, business_id: int):
    # Use SQL to generate a continuous series of months between the
    # earliest and latest transaction for the business and LEFT JOIN
    # aggregated sums so months with no transactions are returned with
    # zero values. This ensures the API is a faithful reflection of DB history.
    from sqlalchemy import text
    sql = text("""
        WITH bounds AS (
            SELECT date_trunc('month', MIN(created_at))::date AS min_month,
                         date_trunc('month', MAX(created_at))::date AS max_month
            FROM transactions
            WHERE business_id = :bid
        ), months AS (
            SELECT generate_series(min_month, max_month, interval '1 month')::date AS month
            FROM bounds
        ), agg AS (
            SELECT date_trunc('month', created_at)::date AS month,
                         SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS income,
                         SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            WHERE business_id = :bid
            GROUP BY month
        )
        SELECT to_char(months.month, 'YYYY-MM') AS month, COALESCE(agg.income, 0) AS income, COALESCE(agg.expense, 0) AS expense
        FROM months
        LEFT JOIN agg ON months.month = agg.month
        ORDER BY months.month ASC
        """)
    res = db.execute(sql, {'bid': business_id}).fetchall()
    out = []
    try:
        for row in res:
            # support different Row types (Row, RowMapping)
            mapping = None
            if hasattr(row, '_mapping'):
                mapping = row._mapping
            else:
                try:
                    mapping = dict(row)
                except Exception:
                    mapping = {0: row[0], 1: row[1], 2: row[2]}
            month = mapping.get('month') or mapping.get(0)
            income = mapping.get('income') or mapping.get(1) or 0.0
            expense = mapping.get('expense') or mapping.get(2) or 0.0
            out.append({'month': month, 'income': float(income or 0.0), 'expense': float(expense or 0.0)})
        return out
    except Exception as e:
        logging.exception('analytics_monthly: error processing query results')
        return []


def charts_income_expense_by_date(db: Session, business_id: int, start_date=None, end_date=None):
    """Return list of dates with separated income and expense sums.

    start_date/end_date: optional date or datetime to bound the query.
    """
    from datetime import datetime
    # For the charts 'all' endpoint we return monthly buckets spanning the
    # full history of transactions (min -> max) to ensure the frontend does
    # not implicitly filter or guess missing months. Reuse analytics_monthly
    # which already produces a continuous month series.
    months = analytics_monthly(db, business_id)
    out = []
    # Convert monthly rows to a shape historically expected by some callers
    # but include the canonical `month` field for strict contract use.
    for m in months:
        # m is {'month': 'YYYY-MM', 'income': .., 'expense': ..}
        out.append({'month': m.get('month'), 'date': f"{m.get('month')}-01", 'label': m.get('month'), 'income': float(m.get('income', 0.0)), 'expense': float(m.get('expense', 0.0))})
    return out


def top_selling_items(db: Session, business_id: int, limit: int = 10):
    """Return top selling items by sum(used_quantity) joined to inventory.item_name."""
    from sqlalchemy import func
    q = (
        db.query(models.Inventory.item_name.label('item_name'), func.sum(models.Transaction.used_quantity).label('total_sold'))
        .join(models.Transaction, models.Transaction.inventory_id == models.Inventory.id)
        .filter(models.Transaction.business_id == business_id, models.Transaction.type == models.TransactionTypeEnum.Income)
        .group_by(models.Inventory.item_name)
        .order_by(func.sum(models.Transaction.used_quantity).desc())
        .limit(limit)
    )
    results = q.all()
    return [{'item_name': r.item_name, 'total_sold': int(r.total_sold or 0)} for r in results]


def category_sales(db: Session, business_id: int):
    """Return category-wise sales amounts (Income only)."""
    from sqlalchemy import func
    q = (
        db.query(models.Transaction.category.label('category'), func.sum(models.Transaction.amount).label('amount'))
        .filter(models.Transaction.business_id == business_id, models.Transaction.type == models.TransactionTypeEnum.Income)
        .group_by(models.Transaction.category)
        .order_by(func.sum(models.Transaction.amount).desc())
    )
    results = q.all()
    out = []
    for row in results:
        cat = row.category or 'Uncategorized'
        out.append({'category': cat, 'amount': float(row.amount or 0.0)})
    # If there are no operating-expense categories from transactions,
    # fall back to using inventory COGS grouped by inventory.category
    if len(out) == 0:
        try:
            cogs_cats = expense_categories_by_business(db, business_id)
            # Map cogs_cats [{category, total}] -> [{category, amount}]
            fb = []
            for r in cogs_cats:
                fb.append({'category': r.get('category') or 'Uncategorized', 'amount': float(r.get('total') or 0.0)})
            return fb
        except Exception:
            # On any failure, return empty list rather than crash
            return []
    return out


def expense_categories_by_business(db: Session, business_id: int):
    """Return inventory-category cost totals using the ml_transactions view.

    Returns a list of dicts: [{ 'category': name, 'total': number }, ...]
    """
    sql = text("""
        SELECT COALESCE(i.category, 'Uncategorized') AS category,
               COALESCE(SUM(mt.cost_amount), 0) AS total
        FROM ml_transactions mt
        JOIN inventory i ON mt.inventory_id = i.id
        WHERE mt.business_id = :bid
        GROUP BY COALESCE(i.category, 'Uncategorized')
        ORDER BY total DESC
    """)
    rows = db.execute(sql, {'bid': business_id}).fetchall()
    out = []
    for row in rows:
        mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
        cat = mapping.get('category') or 'Uncategorized'
        out.append({'category': cat, 'total': float(mapping.get('total') or 0.0)})
    return out


def categories_by_business(db: Session, business_id: int):
    # For analytics we use transactions as the sole source of truth. Inventory
    # rows represent stock state only and must NOT be used to classify or
    # aggregate financial categories. Group by the transaction.category and
    # consider only Expense transactions for the expense category pie chart.
    # Resolve category from transaction first, then inventory when present.
    # Treat empty or whitespace-only category strings as missing. Only
    # Expense transactions are considered and all expense rows are included.
    # This prevents using inventory.item_name as a category.
    # SQL expression: COALESCE(NULLIF(TRIM(transaction.category), ''), NULLIF(TRIM(inventory.category), ''))
    category_expr = func.coalesce(
        func.nullif(func.trim(models.Transaction.category), ''),
        func.nullif(func.trim(models.Inventory.category), '')
    ).label('category')

    q = (
        db.query(
            category_expr,
            func.sum(models.Transaction.amount).label('amount')
        )
        .outerjoin(models.Inventory, models.Inventory.id == models.Transaction.inventory_id)
        .filter(models.Transaction.business_id == business_id, models.Transaction.type == models.TransactionTypeEnum.Expense)
        .group_by(category_expr)
        .order_by(func.sum(models.Transaction.amount).desc())
    )
    results = q.all()
    out = []
    for row in results:
        cat = row.category or 'Uncategorized'
        out.append({'category': cat, 'amount': float(row.amount or 0.0)})
    return out


def categories_for_accountant(db: Session, business_id: int):
    """Return expense categories for the accountant view.

    Behavior:
    1) Query operating expense categories from transactions (type='Expense') grouped by transaction.category.
    2) If the result is empty, fall back to inventory COGS grouped by inventory.category (ml_transactions join).

    Returns list of {'category': str, 'amount': float}
    """
    from sqlalchemy import func
    # Query operating expense categories (transaction.category only)
    q = (
        db.query(
            func.nullif(func.trim(models.Transaction.category), '').label('category'),
            func.coalesce(func.sum(models.Transaction.amount), 0).label('amount')
        )
        .filter(models.Transaction.business_id == business_id, models.Transaction.type == models.TransactionTypeEnum.Expense)
        .group_by(func.nullif(func.trim(models.Transaction.category), ''))
        .order_by(func.sum(models.Transaction.amount).desc())
    )
    results = q.all()
    out = []
    for row in results:
        cat = row.category or 'Uncategorized'
        out.append({'category': cat, 'amount': float(row.amount or 0.0)})
    if len(out) > 0:
        return out
    # Fallback to COGS grouped by inventory.category
    try:
        cogs = expense_categories_by_business(db, business_id)
        # expense_categories_by_business returns [{'category', 'total'}]
        fb = []
        for r in cogs:
            fb.append({'category': r.get('category') or 'Uncategorized', 'amount': float(r.get('total') or 0.0)})
        return fb
    except Exception:
        return []


def report_weekly(db: Session, business_id: int):
    """Return totals for the last 7 days (income, expense)."""
    from datetime import datetime, timedelta, timezone
    # Calculate current week boundaries in UTC: start of week (Monday 00:00:00) to start of next week
    now = datetime.utcnow()
    # start of current week (Monday)
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start = start_of_week
    end = start + timedelta(days=7)
    # Use transactions only; inventory is stock-state and should not affect totals
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= start, models.Transaction.created_at < end).all()
    income = 0.0
    expense = 0.0
    for t in txs:
        try:
            norm = _normalize_tx_type(t.type)
        except ValueError:
            continue
        if norm == 'income':
            income += float(t.amount)
        elif norm == 'expense':
            expense += float(t.amount)
    return {'total_income': income, 'total_expense': expense}


def report_monthly(db: Session, business_id: int):
    """Return totals for the current month (income, expense)."""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    # start of current month in UTC
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # compute start of next month
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year+1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month+1)
    # Use transactions only; inventory is stock-state and should not affect totals
    txs = db.query(models.Transaction).filter(models.Transaction.business_id == business_id, models.Transaction.created_at >= month_start, models.Transaction.created_at < next_month).all()
    income = 0.0
    expense = 0.0
    for t in txs:
        try:
            norm = _normalize_tx_type(t.type)
        except ValueError:
            continue
        if norm == 'income':
            income += float(t.amount)
        elif norm == 'expense':
            expense += float(t.amount)
    return {'total_income': income, 'total_expense': expense}
