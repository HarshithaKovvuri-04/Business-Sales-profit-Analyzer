import traceback
from app.db.session import SessionLocal
from app import crud

def main():
    db = SessionLocal()
    try:
        user = crud.create_user(db, 'smoketest_user2', 'TestPass123!', 'owner')
        print('created', user.id, user.username, user.role)
    except Exception as e:
        print('error creating user:')
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    main()
