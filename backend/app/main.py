from __future__ import annotations

from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db import Base, engine, get_db
from app.models import Goal, Transaction, User
from app.schemas import (
    ForecastOut,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    InsightOut,
    NudgeOut,
    RiskProfileOut,
    StressScoreOut,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
    UserCreate,
    UserOut,
)
from app.services.forecast import forecast
from app.services.goals import list_goals, recommend_contribution
from app.services.insights import generate_insights, list_latest_insights
from app.services.nudges import generate_nudges
from app.services.stress import compute_risk_profile, compute_stress_score
from app.services.transactions import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)
from app.settings import settings


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance, but Smarter", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# Users
@app.post("/users", response_model=UserOut)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(
        name=body.name,
        email=body.email,
        income_frequency=body.income_frequency,
        monthly_income_estimate=body.monthly_income_estimate,
        starting_balance=body.starting_balance,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Transactions
@app.post("/transactions", response_model=TransactionOut)
def post_transaction(body: TransactionCreate, db: Session = Depends(get_db)):
    txn = Transaction(
        user_id=body.user_id,
        date=body.date,
        amount=body.amount,
        type=body.type,
        category=body.category,
        merchant=body.merchant,
        note=body.note,
        tags=",".join(body.tags) if body.tags else None,
    )
    return create_transaction(db, txn)


@app.get("/transactions", response_model=list[TransactionOut])
def get_transactions(
    user_id: str = Query(...),
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    type: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    txns = list_transactions(
        db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        category=category,
        type=type,
        limit=limit,
        offset=offset,
    )
    # convert tags
    out = []
    for t in txns:
        dto = TransactionOut.model_validate(t)
        dto.tags = [x for x in (t.tags or "").split(",") if x] or None
        out.append(dto)
    return out


@app.put("/transactions/{txn_id}", response_model=TransactionOut)
def put_transaction(txn_id: str, body: TransactionUpdate, db: Session = Depends(get_db)):
    txn = get_transaction(db, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if body.date is not None:
        txn.date = body.date
    if body.amount is not None:
        txn.amount = body.amount
    if body.type is not None:
        txn.type = body.type
    if body.category is not None:
        txn.category = body.category
    if body.merchant is not None:
        txn.merchant = body.merchant
    if body.note is not None:
        txn.note = body.note
    if body.tags is not None:
        txn.tags = ",".join(body.tags) if body.tags else None

    updated = update_transaction(db, txn)
    dto = TransactionOut.model_validate(updated)
    dto.tags = [x for x in (updated.tags or "").split(",") if x] or None
    return dto


@app.delete("/transactions/{txn_id}")
def del_transaction(txn_id: str, db: Session = Depends(get_db)):
    txn = get_transaction(db, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    delete_transaction(db, txn_id)
    return {"ok": True}


# Forecast / Insights / Stress / Nudges
@app.get("/forecast", response_model=ForecastOut)
def get_forecast(user_id: str = Query(...), horizon_days: int = Query(default=30, ge=7, le=60), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    fc = forecast(db, user, as_of=date.today(), horizon_days=horizon_days)
    return ForecastOut(
        user_id=user_id,
        as_of=fc.as_of,
        current_balance=fc.current_balance,
        horizons_days=[7, 14, 30],
        curve=[{"date": d, "projected_balance": b} for d, b in fc.curve],
        days_until_broke=fc.days_until_broke,
        safety_status=fc.safety_status,  # type: ignore
        summary=fc.summary,
    )


@app.get("/insights", response_model=list[InsightOut])
def get_insights(user_id: str = Query(...), refresh: bool = Query(default=True), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if refresh:
        generate_insights(db, user_id)
    return list_latest_insights(db, user_id, limit=10)


@app.get("/stress-score", response_model=StressScoreOut)
def get_stress_score(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    s = compute_stress_score(db, user)
    return StressScoreOut(user_id=user_id, score=s.score, label=s.label, explanation=s.explanation, drivers=s.drivers)  # type: ignore


@app.get("/risk-profile", response_model=RiskProfileOut)
def get_risk_profile(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    rp = compute_risk_profile(db, user)
    return RiskProfileOut(user_id=user_id, profile=rp["profile"], explanation=rp["explanation"], signals=rp["signals"])  # type: ignore


@app.get("/nudges", response_model=list[NudgeOut])
def get_nudges(user_id: str = Query(...), refresh: bool = Query(default=True), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if refresh:
        return generate_nudges(db, user, limit=3)
    # fallback: still just generate for MVP
    return generate_nudges(db, user, limit=3)


# Goals
@app.post("/goals", response_model=GoalOut)
def post_goal(body: GoalCreate, db: Session = Depends(get_db)):
    goal = Goal(
        user_id=body.user_id,
        title=body.title,
        target_amount=body.target_amount,
        target_date=body.target_date,
        current_amount=body.current_amount,
        category=body.category,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@app.get("/goals", response_model=list[GoalOut])
def get_goals(user_id: str = Query(...), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return list_goals(db, user_id)


@app.put("/goals/{goal_id}", response_model=GoalOut)
def put_goal(goal_id: str, body: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if body.title is not None:
        goal.title = body.title
    if body.target_amount is not None:
        goal.target_amount = body.target_amount
    if body.target_date is not None:
        goal.target_date = body.target_date
    if body.current_amount is not None:
        goal.current_amount = body.current_amount
    if body.category is not None:
        goal.category = body.category
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@app.delete("/goals/{goal_id}")
def del_goal(goal_id: str, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return {"ok": True}


@app.get("/goals/{goal_id}/recommendation")
def goal_recommendation(goal_id: str, db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return recommend_contribution(goal)

