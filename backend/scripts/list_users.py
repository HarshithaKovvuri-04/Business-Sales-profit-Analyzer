import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from app.db.session import SessionLocal
from app import models

def list_users():
    db = SessionLocal()
    try:
        us = db.query(models.User).all()
        print('Users:', len(us))
        for u in us:
            print({'id':u.id,'username':u.username,'role':str(u.role),'created_at':u.created_at.isoformat()})
    finally:
        db.close()

if __name__ == '__main__':
    list_users()
