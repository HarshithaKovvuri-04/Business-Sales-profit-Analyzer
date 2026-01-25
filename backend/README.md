# BizAnalyzer AI — Backend

Location: `backend/`

Quick start:

```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env to set DATABASE_URL and SECRET_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

API endpoints are under `/auth`, `/businesses`, `/transactions`, `/summary`, `/inventory`.

Important database notes:
- This backend requires a PostgreSQL `bizanalyzer` database. Set `DATABASE_URL` in `backend/.env` to a valid Postgres DSN (e.g. `postgresql://user:pass@host:5432/bizanalyzer`).
- The `inventory` table uses a `cost_price` numeric column (non-null). If your database was previously using a different schema (or SQLite), run a safe migration to add/rename the `cost_price` column and do NOT delete transactional data. See `backend/sql/create_tables.sql` for the desired schema.
