from dotenv import load_dotenv

# Load environment variables from backend/.env as early as possible so
# settings and DB engine initialization see them when modules are imported.
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .core.config import settings
from .db.session import engine
from .db.base import Base

from .api import auth, businesses, transactions, summary, inventory, analytics, users, reports

app = FastAPI(title='BizAnalyzer AI')

# Development-only CORS: allow the Vite dev server origins explicitly.
# Do NOT use '*' in production — this is intentionally restrictive to local dev hosts.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Fallback global exception handler to ensure CORS headers are present
# even when an unexpected error (500) occurs. This complements CORSMiddleware
# and makes sure browser preflights/responses are not blocked by missing CORS.
@app.exception_handler(Exception)
async def _handle_unexpected_exception(request: Request, exc: Exception):
    # log the exception server-side for diagnostics
    import logging
    logging.exception('Unhandled exception during request: %s', exc)

    # Respect the allowed origins used by CORSMiddleware rather than using '*'
    allowed = {"http://localhost:5173", "http://127.0.0.1:5173"}
    origin = request.headers.get('origin')
    headers = {}
    if origin in allowed:
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Credentials'] = 'true'
        headers['Access-Control-Allow-Methods'] = '*'
        headers['Access-Control-Allow-Headers'] = '*'

    # Return a neutral JSON response with CORS headers so the browser can see it
    return JSONResponse(status_code=500, content={"detail": "Internal server error"}, headers=headers)


@app.on_event('startup')
def on_startup():
    # create tables
    Base.metadata.create_all(bind=engine)
    # Safe dev-only verification log: print DB type, database name and user (no password).
    try:
        # engine.url is a SQLAlchemy URL object
        url = getattr(engine, 'url', None)
        dialect = getattr(engine, 'dialect', None)
        dbtype = getattr(dialect, 'name', None) or (url.get_backend_name() if url is not None else 'unknown')
        dbname = getattr(url, 'database', None) if url is not None else None
        dbuser = getattr(url, 'username', None) if url is not None else None
        if dbtype and dbname:
            import logging
            logging.info("Connected to %s database: %s as user %s", dbtype.capitalize(), dbname, dbuser or '<unknown>')
    except Exception:
        pass


app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(businesses.router, prefix='/businesses', tags=['businesses'])
app.include_router(transactions.router, prefix='/transactions', tags=['transactions'])
app.include_router(summary.router, prefix='/summary', tags=['summary'])
app.include_router(inventory.router, prefix='/inventory', tags=['inventory'])
app.include_router(analytics.router, prefix='/analytics', tags=['analytics'])
app.include_router(users.router, prefix='/users', tags=['users'])
app.include_router(reports.router, prefix='/reports', tags=['reports'])


@app.get('/')
def root():
    return {'status':'ok'}
