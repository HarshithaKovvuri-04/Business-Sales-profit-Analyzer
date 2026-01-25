import os
import sys
from pathlib import Path

from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
env_path = root / '.env'


def main():
    # load .env into environment using python-dotenv for robust parsing
    if env_path.exists():
        load_dotenv(env_path)

    # ensure backend root is on sys.path so 'app' package can be imported
    sys.path.insert(0, str(root))

    # start uvicorn programmatically on the stable development port.
    # The frontend dev server depends on the backend being available at port 8002.
    # bind to 127.0.0.1 to avoid external exposure
    import uvicorn
    # import settings as the single source-of-truth for the dev API port
    try:
        from app.core.config import settings
        port = int(getattr(settings, 'API_PORT', 8002))
    except Exception:
        port = 8002
    uvicorn.run('app.main:app', host='127.0.0.1', port=port, reload=True)


if __name__ == '__main__':
    main()
