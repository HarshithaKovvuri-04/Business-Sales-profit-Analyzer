from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, crud, security
from .deps import get_db_dep, get_current_user

router = APIRouter()


@router.get('/me', response_model=schemas.UserOut)
def users_me(current_user=Depends(get_current_user)):
    return current_user


@router.put('/me/password')
def change_password(payload: schemas.PasswordChangeRequest, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # verify current password
    if not security.verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail='Current password is incorrect')
    # perform update
    ok = crud.change_user_password(db, current_user.id, payload.new_password)
    if not ok:
        raise HTTPException(status_code=500, detail='Failed to update password')
    return {'status': 'ok', 'message': 'Password updated successfully'}
