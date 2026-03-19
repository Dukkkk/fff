# Personal Finance, but Smarter (MVP)

A modern consumer fintech MVP that goes beyond budgeting dashboards by combining:
- **Smart transaction tracking**
- **Predictive cash flow forecasting**
- **Behavioral insights**
- **Coach-style nudges**
- **Financial stress score**
- **Goal-based saving support**
- **Simple readiness / risk profile**

This is built as a production-minded monorepo:

```
/frontend   Next.js + TypeScript + Tailwind (mobile-first UI)
/backend    FastAPI + SQLAlchemy + SQLite (REST API + intelligence modules)
```

## Run locally

### Backend (runnable now)

```powershell
cd C:\git\fff\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# seed realistic demo data (creates backend/fff.db)
python -m app.seed

uvicorn app.main:app --reload --port 8000
```

Open API docs at `http://localhost:8000/docs`.

### Frontend (requires Node.js)

This machine doesn’t currently have Node/npm, but the frontend code is complete.

Install Node.js (18+ recommended), then:

```powershell
cd C:\git\fff\frontend
npm install
$env:NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev
```

Open `http://localhost:3000`.

## Demo flow / sample data

The backend seed creates a realistic demo user with patterned transactions (late-night delivery, weekend spikes, post-payday shopping, subscriptions).

After running:

```powershell
cd C:\git\fff\backend
.\.venv\Scripts\Activate.ps1
python -m app.seed
```

it prints a `user_id` you can use in API calls.

The UI onboarding creates a new user; for the seeded user, you can manually put the printed `user_id` into local storage key `fff_user_id` (or just use onboarding for a clean empty account).

## Product architecture (high level)

### Backend

- **REST API**: `backend/app/main.py`
- **DB models**: `backend/app/models.py`
- **Forecasting** (rule/heuristic): `backend/app/services/forecast.py`
  - Rolling daily spend + weekend multiplier + simple income schedule from `income_frequency`.
- **Insights** (pattern detection): `backend/app/services/insights.py`
  - Weekend overspend, late-night delivery, subscription creep, small spends add up, unusual outlier.
- **Nudges** (coach logic): `backend/app/services/nudges.py`
  - Behavioral-finance framing + actions like “low-spend mode”, “set a cap”, “review subscriptions”.
- **Stress score + risk profile**: `backend/app/services/stress.py`
  - Combines shortfall risk, buffer thinness, volatility, income stability.
- **Goals**: `backend/app/services/goals.py`

### Frontend

- **App shell + navigation**: `frontend/src/components/AppShell.tsx`
- **Screens**:
  - `frontend/src/app/onboarding/page.tsx`
  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/app/transactions/page.tsx`
  - `frontend/src/app/insights/page.tsx`
  - `frontend/src/app/goals/page.tsx`
  - `frontend/src/app/settings/page.tsx`
- **API client**: `frontend/src/lib/api.ts`

## What’s rule-based today vs upgradable to ML later

- **Rule-based now (MVP)**:
  - Pattern detection, scoring, nudges, baseline forecasting (rolling averages + cadence assumptions).
- **Easy upgrades later**:
  - Forecast: Prophet/ARIMA/GBM/LSTM with calendar features and learned seasonality.
  - Insights: merchant enrichment + embeddings + anomaly detection per user.
  - Nudges: personalized policy learning + experimentation framework (A/B testing).
  - Stress: calibrated model from real outcomes (overdraft events, missed bills).
