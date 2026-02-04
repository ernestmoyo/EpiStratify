# EpiStratify SNT Toolkit - Developer Guide

## Quick Links

| Service | URL | What it does |
|---------|-----|-------------|
| **Frontend (Vercel)** | https://vercel.com/ernests-projects-8625303b/epi-stratify | Hosts the Vue.js frontend |
| **Backend (Railway)** | https://railway.com/project/4f818c28-b2a0-46dc-8ac4-1f3b3d5a6c23 | Hosts the FastAPI backend + PostgreSQL |
| **Live App** | https://epi-stratify.vercel.app | The app your users visit |
| **API Docs** | https://epistratify-production.up.railway.app/docs | Swagger UI for all API endpoints |
| **API Health** | https://epistratify-production.up.railway.app/api/v1/health | Backend health check |
| **GitHub Repo** | https://github.com/ernestmoyo/EpiStratify | Source code |

## Project Structure

```
epistratify/
  backend/          -> Python FastAPI app (deployed on Railway)
  frontend/         -> Vue 3 + TypeScript app (deployed on Vercel)
  database/         -> SQL init scripts
  infrastructure/   -> Docker configs for local dev
  docs/             -> Documentation
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend**: Vue 3, TypeScript, Pinia, Ant Design Vue, Vite
- **Auth**: JWT tokens (access + refresh), bcrypt passwords

## How Deployment Works

### When you push to `main`:
1. **Vercel** auto-builds the frontend from `frontend/` folder
2. **Railway** auto-builds the backend from `backend/` folder
3. Both go live within ~1 minute

### Environment Variables

**Railway (backend):**
- `DATABASE_URL` - auto-set by Railway PostgreSQL
- `SECRET_KEY` - JWT signing key
- `FRONTEND_URL` - Vercel app URL (for CORS)

**Vercel (frontend):**
- `VITE_API_URL` - must be `https://epistratify-production.up.railway.app/api/v1`

## Common Tasks

### Run backend locally
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements/base.txt
# Set DATABASE_URL in .env (needs PostgreSQL running)
uvicorn app.main:app --reload
```

### Run frontend locally
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Check if backend is working
Visit: https://epistratify-production.up.railway.app/api/v1/health

### View all API endpoints
Visit: https://epistratify-production.up.railway.app/docs

### Check Railway logs
Railway dashboard -> EpiStratify service -> Deploy Logs

### Update environment variables
- **Railway**: Service -> Variables tab -> edit -> Deploy
- **Vercel**: Settings -> Environment Variables -> edit -> Redeploy

## What Has Been Built

### Phase 1 (Core)
- User auth (register, login, JWT tokens)
- Project management (create, list, update, archive)
- 10-step WHO SNT workflow engine
- Data source upload + quality checks (completeness, outliers, consistency)
- Stratification (risk thresholds, GeoJSON map output)

### Phase 2 (Advanced)
- Intervention tailoring (WHO Annex 6 decision trees, 8 interventions)
- Budget scenarios (cost modeling, ICER optimization)
- Impact forecasting (transmission model, DALY estimation)
- Report generation (JSON, CSV export)

### Total: 55 API endpoints, 17 unit tests passing
