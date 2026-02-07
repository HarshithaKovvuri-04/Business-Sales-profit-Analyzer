
PostgreSQL & Project Setup
==========================

This guide covers installing PostgreSQL on Windows/macOS/Linux, creating the `bizanalyzer` database, configuring the backend, and running frontend and backend locally.

1) Install PostgreSQL
- Windows:
	- Download the installer from https://www.postgresql.org/download/windows/ and run it.
	- Note the `postgres` superuser password you set during install.
	- Use `pgAdmin` (included) or `psql` from the installation to run SQL commands.

- macOS:
	- With Homebrew: `brew install postgresql`
	- Start the server: `brew services start postgresql`

- Linux (Ubuntu/Debian):
	- `sudo apt update && sudo apt install postgresql postgresql-contrib`
	- Start or enable the service: `sudo systemctl enable --now postgresql`

2) Create the database and a dedicated user
- Switch to the `postgres` user and open psql (or use pgAdmin):

```bash
sudo -u postgres psql
```

- Inside `psql`, run these commands (change password to a secure value):

```sql
CREATE USER bizuser WITH PASSWORD 'bizpass';
CREATE DATABASE bizanalyzer OWNER bizuser;
GRANT ALL PRIVILEGES ON DATABASE bizanalyzer TO bizuser;
\q
```

-- Example DATABASE_URL (use this in backend `.env`):

```
postgresql://bizuser:bizpass@localhost:5432/bizanalyzer
```

3) Backend setup (FastAPI)
- Prepare Python environment and install dependencies:

```bash
cd backend
python -m venv .venv
## Windows
.\.venv\Scripts\activate
## macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

- Create a `.env` file in the `backend/` folder (copy from `.env.example`) and set at least:

```
DATABASE_URL=postgresql://bizuser:bizpass@localhost:5432/bizanalyzer
SECRET_KEY=replace-with-a-secure-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

- The backend uses SQLAlchemy `create_all()` at startup to create tables. Start the server with:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

Notes:
- For production, use proper migration tooling (Alembic) and a secure `SECRET_KEY`.
- Ensure the DB server is reachable from the backend; on Windows with installers the server usually listens on `localhost`.

4) Frontend setup (Vite + React + Tailwind)
- From the project root:

```bash
cd frontend
npm install
```

- Copy `frontend/.env.example` to `frontend/.env` and adjust if your backend runs at a different host/port:

```
VITE_API_BASE=http://localhost:8002
```

- Start the dev server:

```bash
npm run dev
```

Open the site (Vite will print the local URL, typically `http://localhost:5173`).

5) Testing the Application (manual)
- Register a user: open `/register` in the frontend and create an account (role: Owner or Manager).
- Login: open `/login` and sign in. On success the frontend stores the JWT in `localStorage` under `bizanalyzer_token` and redirects to the dashboard.
- Create a business: go to `Businesses` and add a new business — this calls `POST /businesses`.
- Add transactions: open `Finance` and use `Add Transaction` to save incomes/expenses — this calls `POST /transactions`.
- Verify profit: Dashboard metrics read `GET /summary/{business_id}` to calculate total income, total expense, and net profit.

Running the dataset import script (PowerShell compatibility)

If you need to import datasets using the provided import script, PowerShell does not accept the Unix backslash (`\`) as a line continuation. Run the import in one of these ways:

- Single-line (recommended):

```powershell
python -m app.scripts.import_dataset --business-id 3 --file backend/app/data/retail_dataset_with_costs.csv
```

- PowerShell multiline using backtick (`) as the continuation character:

```powershell
python -m app.scripts.import_dataset `
	--business-id 3 `
	--file backend/app/data/retail_dataset_with_costs.csv
```

Do NOT use backslash `\` to continue lines in PowerShell — it causes parsing errors like "Missing expression after unary operator '--'".

6) Troubleshooting
- If you see database connection errors, verify `DATABASE_URL` and that PostgreSQL is running and reachable.
- If the frontend cannot reach the backend, ensure `VITE_API_BASE` matches the running `uvicorn` host and port, and that CORS is allowed (server is configured with permissive CORS for development).

