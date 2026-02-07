# Business-Sales-profit-Analyzer

BizAnalyzer AI

Full-stack business analytics app with role-based dashboards and reporting.

Full-stack business analytics starter app: React + Vite frontend and FastAPI backend with PostgreSQL.
See `frontend/` and `backend/` folders for source and `docs/SETUP.md` for install and run instructions.

Roles:
- owner: full access including member management and profit reports
- accountant: finance access including profit and reports
- staff: limited access (no profit/member management)

See `docs/SETUP.md` for more detailed setup and deployment notes.

---

## How to Run the Website Locally

Follow these steps to run the full-stack application (frontend + backend) on your machine.

### Prerequisites

- Node.js (v18 or later)
- Python (3.10+ recommended)
- PostgreSQL
- Git

### Backend setup (FastAPI)

1. Open a terminal and navigate to the `backend` folder:

```powershell
cd backend
```

2. Create and activate a Python virtual environment (PowerShell example):

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

3. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` folder with the following variables (do NOT commit real secrets):

```
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/bizanalyzer
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

5. Start the FastAPI backend on port 8002:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

6. Swagger/OpenAPI docs are available at:

```
http://localhost:8002/docs
```

### PostgreSQL setup

1. Create a PostgreSQL database named `bizanalyzer`:

```sql
-- run in psql or your preferred client
CREATE DATABASE bizanalyzer;
```

2. Make sure the `DATABASE_URL` in your `.env` matches the database credentials and host.

3. The backend will create necessary tables on startup (if configured). Check backend logs for any migration or creation messages.

### Frontend setup (Vite + React)

1. Open a new terminal and navigate to the `frontend` folder:

```powershell
cd frontend
```

2. Install frontend dependencies (npm):

```powershell
npm install
```

3. Start the Vite development server:

```powershell
npm run dev
```

4. The local frontend will be available at:

```
http://localhost:5173
```

### Final verification

- Backend running: `http://localhost:8002`
- Frontend running: `http://localhost:5173`
- You should be able to register, log in, create a business, and access role-based dashboards according to the configured roles.

Notes:

- Do NOT commit your `.env` or any real passwords to version control.
- If you need to change ports or host settings, update the `uvicorn` command or the frontend `vite` config accordingly.

Running the dataset import script (PowerShell)

Use a single-line command in PowerShell (recommended):

```powershell
python -m app.scripts.import_dataset --business-id 3 --file backend/app/data/retail_dataset_with_costs.csv
```

Or use PowerShell's backtick (`) for a multiline command:

```powershell
python -m app.scripts.import_dataset `
	--business-id 3 `
	--file backend/app/data/retail_dataset_with_costs.csv
```

Do NOT use backslash (`\`) as a line continuation in PowerShell — it will cause syntax errors.
