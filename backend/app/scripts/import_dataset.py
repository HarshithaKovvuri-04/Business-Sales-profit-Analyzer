#!/usr/bin/env python3
"""Import inventory and income transactions from a CSV dataset.

CSV columns expected:
- date
- item_name
- category
- quantity
- sales_amount
- cost
- profit
- cost_per_unit

Usage:
    python backend/app/scripts/import_dataset.py --business-id 3 --file backend/app/data/retail_dataset_with_costs.csv

PowerShell notes:
- Single-line (recommended):

```powershell
python -m app.scripts.import_dataset --business-id 3 --file backend/app/data/retail_dataset_with_costs.csv
```

- PowerShell multiline using backtick (`) as the continuation character:

```powershell
python -m app.scripts.import_dataset `
    --business-id 3 `
    --file backend/app/data/retail_dataset_with_costs.csv
```

Do NOT use backslash `\\` as a line continuation in PowerShell — it will cause syntax errors.

This script:
- Ensures inventory items exist for the given business (creates with default quantity 1000).
- Creates Income transactions linked to the inventory item with `used_quantity` equal to `quantity`.
- Sets transaction.created_at to the CSV `date` when parseable.
"""
import argparse
import csv
import sys
import random
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from collections import defaultdict
from app.db.session import SessionLocal
from app import models, crud


def parse_date(s: str):
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    # Try ISO first
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # Common fallbacks
    fmts = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    return None


def main():
    p = argparse.ArgumentParser(description='Import dataset: inventory + income transactions')
    p.add_argument('--business-id', type=int, required=True)
    p.add_argument('--file', required=True)
    args = p.parse_args()

    db = SessionLocal()
    rows_processed = 0
    inventory_created = 0
    transactions_created = 0

    # Resolve file path robustly: accept absolute paths, paths relative to
    # the current working directory, and paths that include a leading
    # 'backend/' segment when the command is executed from the backend folder.
    raw_path = Path(args.file)
    if not raw_path.is_absolute():
        # Try as provided relative to cwd
        candidate = Path.cwd() / raw_path
        if candidate.exists():
            filepath = candidate.resolve()
        else:
            # If path begins with 'backend/', strip that segment and try again
            parts = raw_path.parts
            if parts and parts[0] == 'backend':
                alt = Path(*parts[1:])
                alt_candidate = Path.cwd() / alt
                if alt_candidate.exists():
                    filepath = alt_candidate.resolve()
                else:
                    filepath = candidate.resolve()
            else:
                filepath = candidate.resolve()
    else:
        filepath = raw_path.resolve()

    if not filepath.exists():
        print(f"Dataset file not found: '{args.file}'")
        print(f"Tried resolving to: '{filepath}' (relative to CWD: {Path.cwd()})")
        print("Please provide the path relative to the backend folder, e.g. 'app/data/yourfile.csv', or an absolute path.")
        sys.exit(1)

    try:
        revenue_by_date = defaultdict(float)
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows_processed += 1
                # Read fields
                date_raw = row.get('date')
                item_name = (row.get('item_name') or '').strip()
                category = (row.get('category') or '').strip() or None
                qty_raw = row.get('quantity') or '0'
                sales_raw = row.get('sales_amount') or '0'
                cost_per_unit_raw = row.get('cost_per_unit') or ''

                try:
                    quantity = int(float(qty_raw))
                except Exception:
                    quantity = 0
                try:
                    sales_amount = float(sales_raw) if sales_raw not in (None, '') else 0.0
                except Exception:
                    sales_amount = 0.0
                try:
                    cost_price = float(cost_per_unit_raw) if cost_per_unit_raw not in (None, '') else 0.0
                except Exception:
                    cost_price = 0.0

                # Ensure inventory item exists
                inv = db.query(models.Inventory).filter(models.Inventory.business_id == args.business_id, models.Inventory.item_name == item_name).first()
                if not inv:
                    # create with default large quantity
                    try:
                        inv = crud.create_inventory(db, args.business_id, item_name, quantity=1000, cost_price=cost_price, category=category)
                        inventory_created += 1
                    except Exception as e:
                        print(f"Row {rows_processed}: failed to create inventory '{item_name}': {e}")
                        # Skip transaction creation for this row
                        continue

                # Use inventory.category if available for transaction category
                tx_category = inv.category if getattr(inv, 'category', None) not in (None, '') else category

                # Create income transaction linked to inventory
                try:
                    tx = crud.create_transaction_with_inventory(db, args.business_id, models.TransactionTypeEnum.Income, sales_amount, tx_category, inventory_id=inv.id, used_quantity=quantity, source='dataset_import')
                    # Set created_at from CSV if parseable
                    dt = parse_date(date_raw)
                    # Use date key as ISO date string (YYYY-MM-DD) for daily aggregation
                    date_key = None
                    if dt is not None:
                        try:
                            tx.created_at = dt
                            db.add(tx)
                            db.commit()
                            db.refresh(tx)
                        except Exception:
                            db.rollback()
                        date_key = dt.date().isoformat()
                    else:
                        # fallback: use today's date
                        date_key = datetime.utcnow().date().isoformat()

                    # accumulate daily revenue for operating expense calculation
                    try:
                        revenue_by_date[date_key] += float(sales_amount or 0.0)
                    except Exception:
                        revenue_by_date[date_key] += 0.0

                    transactions_created += 1
                except Exception as e:
                    print(f"Row {rows_processed}: failed to create transaction for '{item_name}': {e}")
                    continue

        # After creating all income transactions, create operating expense transactions per day
        expense_created = 0
        for date_key, daily_revenue in revenue_by_date.items():
            # realistic operating expense between 5% and 10% of daily revenue
            pct = random.uniform(0.05, 0.10)
            op_amount = round(daily_revenue * pct, 2)
            if op_amount <= 0:
                continue
            try:
                # create an expense transaction (no inventory linkage)
                exp_tx = crud.create_transaction(db, args.business_id, models.TransactionTypeEnum.Expense, op_amount, category='Operating')
                # set created_at to the day's date
                try:
                    exp_dt = datetime.fromisoformat(date_key)
                    exp_tx.created_at = exp_dt
                    db.add(exp_tx)
                    db.commit()
                    db.refresh(exp_tx)
                except Exception:
                    db.rollback()
                expense_created += 1
            except Exception as e:
                print(f"Failed to create operating expense for {date_key}: {e}")

    finally:
        db.close()

    print(f"Rows processed: {rows_processed}")
    print(f"Inventory items created: {inventory_created}")
    print(f"Income transactions created: {transactions_created}")
    print(f"Operating expense transactions created: {expense_created}")


if __name__ == '__main__':
    main()
