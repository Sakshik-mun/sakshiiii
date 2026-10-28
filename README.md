# Credit Assistant

AI-powered credit health platform for the Indian CIBIL ecosystem.
**Stack:** FastAPI · SQLAlchemy · SQLite · Google Gemini · React (Vite) · Recharts

## Features
- Registration / login with bcrypt hashing and JWT sessions, protected routes, logout
- Financial profile with validation and automatic CIBIL score history
- Analytics: DTI, credit utilization, savings rate, health score, risk flags, score improvement
- Gemini-powered credit analysis and chat advisor (rule-based fallback if no API key)
- Dashboard: score overview, utilization pie chart, score history line chart, AI panel

## Setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add your GEMINI_API_KEY and a strong SECRET_KEY
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (the dev server proxies `/api` to port 8000).

### Tests
```bash
cd backend && pytest -q
```

## API
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register, /login, /logout | Authentication |
| GET/PUT | /api/profile | Financial profile |
| GET/POST | /api/scores | Score history |
| GET | /api/dashboard | Metrics and chart data |
| POST | /api/advisor/analyze, /chat | Gemini advice |
| GET | /api/advisor/history | Past recommendations |

## Notes
- Never commit `.env`. Get a Gemini key at https://aistudio.google.com/.
- AI output is informational, not licensed financial advice.
