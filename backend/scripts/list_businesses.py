import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app.db.session import SessionLocal
from app import models

def list_businesses():
    db = SessionLocal()
    try:
        bs = db.query(models.Business).all()
        print('Businesses:', len(bs))
        for b in bs:
            print({'id':b.id,'name':b.name,'owner_id':b.owner_id,'created_at':b.created_at.isoformat()})
    finally:
        db.close()

if __name__ == '__main__':
    list_businesses()
