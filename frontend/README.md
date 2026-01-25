# BizAnalyzer AI — Frontend

Location: `frontend/`

Quick start:

```bash
cd frontend
npm install
cp .env.example .env
# adjust VITE_API_BASE if backend runs elsewhere
npm run dev
```

The frontend expects the backend to expose the authenticated APIs and will store the JWT in `localStorage` under `bizanalyzer_token`.
