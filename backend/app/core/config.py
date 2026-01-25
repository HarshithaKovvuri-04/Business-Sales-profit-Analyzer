from pathlib import Path
from dotenv import load_dotenv

# Ensure .env in the backend root is loaded into the environment before
# pydantic reads values. This makes Settings() deterministic whether the
# app is started via the start script, uvicorn CLI, or imported directly.
root = Path(__file__).resolve().parents[2]
env_path = root / '.env'
if env_path.exists():
    # support files with BOM by using 'utf-8-sig' encoding
    try:
        load_dotenv(env_path, encoding='utf-8-sig')
    except TypeError:
        # older python-dotenv may not accept encoding kwarg
        load_dotenv(env_path)

    # If python-dotenv failed to populate vars (sometimes due to BOM or
    # environment nuances), fall back to a tiny parser that handles a BOM.
    import os
    if not os.environ.get('DATABASE_URL'):
        try:
            text = env_path.read_text(encoding='utf-8-sig')
        except Exception:
            text = env_path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

try:
    # pydantic v2 moved BaseSettings to pydantic-settings
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    # prefer uppercase env name. DATABASE_URL is required and must be supplied
    # via environment variables or backend/.env. Do not default to SQLite.
    DATABASE_URL: str
    database_url: str | None = None
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Threshold for low-stock reporting (items with quantity < LOW_STOCK_THRESHOLD are considered low stock)
    LOW_STOCK_THRESHOLD: int = 5
    # Stable development API port. Frontend dev server expects backend on port 8002.
    # Do not change this lightly; update frontend `.env` if you intentionally change it.
    API_PORT: int = 8002

    class Config:
        env_file = '.env'


try:
    settings = Settings()
    # normalize: if uppercase DATABASE_URL not provided but lowercase present, use that
    if not settings.DATABASE_URL and settings.database_url:
        settings.DATABASE_URL = settings.database_url
except Exception:
    # fallback: avoid pydantic validation issues in some environments by reading env vars directly
    import os
    class _SimpleSettings:
        pass
    settings = _SimpleSettings()
    settings.DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('database_url')
    settings.SECRET_KEY = os.environ.get('SECRET_KEY')
    settings.ALGORITHM = os.environ.get('ALGORITHM', 'HS256')
    try:
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 60))
    except Exception:
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
