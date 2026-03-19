from __future__ import annotations

from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Goal
from app.utils import safe_div


def list_goals(db: Session, user_id: str) -> list[Goal]:
    stmt = select(Goal).where(Goal.user_id == user_id).order_by(desc(Goal.created_at))
    return list(db.execute(stmt).scalars().all())


def recommend_contribution(goal: Goal, *, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    remaining = max(0.0, goal.target_amount - goal.current_amount)
    days_left = max(1, (goal.target_date - as_of).days)
    weeks_left = max(1.0, days_left / 7.0)
    months_left = max(1.0, days_left / 30.0)
    weekly = safe_div(remaining, weeks_left, 0.0)
    monthly = safe_div(remaining, months_left, 0.0)
    on_track = goal.current_amount >= goal.target_amount * (1.0 - min(0.9, days_left / 365.0))
    return {
        "remaining": float(remaining),
        "days_left": int(days_left),
        "weekly_recommended": float(weekly),
        "monthly_recommended": float(monthly),
        "on_track": bool(on_track),
    }

