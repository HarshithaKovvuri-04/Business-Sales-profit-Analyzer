
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# Fail fast with clear error if DATABASE_URL is not configured or points to
# SQLite — we require PostgreSQL for this deployment to avoid accidental
# local sqlite fallback (which leads to detached/incorrect data).
if not getattr(settings, 'DATABASE_URL', None):
    raise RuntimeError(
        "DATABASE_URL is not set. Ensure backend/.env contains a valid postgresql DATABASE_URL (postgresql://<user>:<password>@host:port/bizanalyzer)."
    )

dsn = settings.DATABASE_URL
if dsn.startswith('sqlite') or 'sqlite://' in dsn:
    raise RuntimeError(
        "SQLite URLs are not permitted. Set DATABASE_URL to your PostgreSQL DSN for the 'bizanalyzer' database."
    )

# Parse the DSN to inspect the database name without relying on a hardcoded
# legacy name string. If the configured database name ends with '_db', signal
# that the name likely needs to be corrected to 'bizanalyzer'.
from sqlalchemy.engine import make_url
try:
    urlobj = make_url(dsn)
    dbname = getattr(urlobj, 'database', '')
    if dbname and dbname.endswith('_db'):
        raise RuntimeError(
            "Detected legacy-style database name ending with '_db'. Update DATABASE_URL to use the production database name 'bizanalyzer'."
        )
except Exception:
    # If parsing fails, continue and let create_engine produce a clear error
    dbname = None

engine = create_engine(dsn, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
