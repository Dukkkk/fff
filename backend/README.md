# Backend (FastAPI)

## Run (Windows / PowerShell)

```powershell
cd C:\git\fff\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt

# create local sqlite db + seed demo user + demo transactions
python -m app.seed

# run API
uvicorn app.main:app --reload --port 8000
```

API base: `http://localhost:8000`

