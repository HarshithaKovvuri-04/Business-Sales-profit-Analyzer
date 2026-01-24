from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import schemas, crud, security
import logging
from ..models import RoleEnum
from ..core.config import settings
from ..db.session import engine
from .deps import get_db_dep

router = APIRouter()


@router.post('/register', response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db_dep)):
    # normalize role at API boundary (MANDATORY)
    role_raw = (user_in.role or 'owner')
    role = role_raw.strip().lower()
    logging.info('Register: normalized role -> %s', role)

    # validate role strictly
    valid_roles = {r.value for r in RoleEnum}
    if role not in valid_roles:
        logging.warning('Register: invalid role provided: %s', role_raw)
        raise HTTPException(status_code=400, detail=f"Invalid role '{role_raw}'. valid: {', '.join(sorted(valid_roles))}")

    # debug: show which DB dialect is used (do not log full DSN)
    try:
        dialect = getattr(engine.dialect, 'name', None)
        logging.info('Register: db_dialect=%s', dialect)
    except Exception:
        logging.exception('Register: failed to read engine dialect')

    # uniqueness check for username
    existing = crud.get_user_by_username(db, user_in.username)
    if existing:
        logging.info('Register: username already exists: %s', user_in.username)
        raise HTTPException(status_code=409, detail='Username already registered')

    try:
        user = crud.create_user(db, user_in.username, user_in.password, role)
        logging.info('Register: user created id=%s username=%s', getattr(user, 'id', None), user.username)
        return user
    except ValueError as ve:
        # ValueError used for known validation/uniqueness issues
        msg = str(ve)
        logging.warning('Register: validation error: %s', msg)
        if 'username' in msg.lower():
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logging.exception('Registration error')
        raise HTTPException(status_code=500, detail='Registration failed; check server logs')


@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db_dep)):
    # using same schema for simplicity
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')
    token = security.create_access_token({'sub': user.username})
    return {'access_token': token, 'token_type': 'bearer'}


from .deps import get_current_user


@router.get('/me', response_model=schemas.UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
