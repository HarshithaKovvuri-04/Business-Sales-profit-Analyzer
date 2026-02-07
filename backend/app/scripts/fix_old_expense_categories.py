#!/usr/bin/env python3
"""One-time script to repair old Expense transactions missing categories.

Rules:
- Only update transactions where type == Expense, inventory_id is not NULL,
  and transaction.category is NULL or empty.
- If the linked inventory has a non-empty `category`, copy it to the transaction.
- Do not modify other fields.

Usage: run from repository root or from backend folder with PYTHONPATH so imports resolve.
Examples (PowerShell-friendly):

Single-line (recommended):

```powershell
python backend/app/scripts/fix_old_expense_categories.py
```

PowerShell multiline using backtick (`):

```powershell
python backend/app/scripts/fix_old_expense_categories.py `
    --dry-run
```

Do NOT use backslash `\\` as a line continuation in PowerShell.
"""
from sqlalchemy import func
from app.db.session import SessionLocal
from app import models


def main():
    db = SessionLocal()
    try:
        # Query transactions matching criteria
        txs = db.query(models.Transaction).filter(
            models.Transaction.type == models.TransactionTypeEnum.Expense,
            models.Transaction.inventory_id != None,
            (models.Transaction.category == None) | (func.trim(models.Transaction.category) == '')
        ).all()

        total_scanned = len(txs)
        total_updated = 0

        print(f"Found {total_scanned} candidate expense transaction(s) to inspect...")

        for tx in txs:
            inv = None
            if tx.inventory_id is not None:
                inv = db.query(models.Inventory).filter(models.Inventory.id == tx.inventory_id).first()
            if not inv:
                # No linked inventory row; skip
                continue
            inv_cat = getattr(inv, 'category', None)
            if inv_cat is None:
                # Inventory has no category; do not change transaction
                continue
            # Trim and ensure non-empty
            inv_cat_str = inv_cat.strip() if isinstance(inv_cat, str) else None
            if not inv_cat_str:
                continue
            # Update transaction category
            tx.category = inv_cat_str
            db.add(tx)
            total_updated += 1

        if total_updated > 0:
            db.commit()
        else:
            db.rollback()

        print(f"Total scanned: {total_scanned}")
        print(f"Total updated: {total_updated}")

    finally:
        db.close()


if __name__ == '__main__':
    main()
