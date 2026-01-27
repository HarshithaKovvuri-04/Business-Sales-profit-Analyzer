import sys
import os
# ensure repo root backend directory is on sys.path so `app` package is importable
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app.db.session import SessionLocal
from app import models
from sqlalchemy import select

def check(business_id=5, limit=10):
    db = SessionLocal()
    try:
        txs = db.execute(select(models.Transaction).where(models.Transaction.business_id==business_id)).scalars().all()
        inv = db.execute(select(models.Inventory).where(models.Inventory.business_id==business_id)).scalars().all()
        print(f"Transactions count for business {business_id}: {len(txs)}")
        for t in txs[:limit]:
            print({'id': t.id, 'type': str(t.type), 'amount': float(t.amount), 'category': t.category, 'created_at': t.created_at.isoformat() if t.created_at else None, 'inventory_id': t.inventory_id})
        print('\nInventory:')
        print(f"Inventory count for business {business_id}: {len(inv)}")
        for i in inv[:limit]:
            print({'id': i.id, 'item_name': i.item_name, 'quantity': i.quantity, 'cost_price': float(i.cost_price)})
    finally:
        db.close()

if __name__ == '__main__':
    import sys
    bid = int(sys.argv[1]) if len(sys.argv)>1 else 5
    check(bid)
