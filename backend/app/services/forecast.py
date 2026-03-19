from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Transaction, User
from app.utils import clamp, daterange, safe_div


DEFAULT_SAFETY_BUFFER = 200.0


@dataclass(frozen=True)
class ForecastResult:
    as_of: date
    current_balance: float
    curve: list[tuple[date, float]]
    days_until_broke: int | None
    safety_status: str
    summary: str


def _balance_as_of(db: Session, user: User, as_of: date) -> float:
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.date <= as_of)
        .order_by(desc(Transaction.date))
        .limit(2000)
    )
    txns = list(db.execute(stmt).scalars().all())

    bal = user.starting_balance
    for t in txns:
        bal += t.amount if t.type == "income" else -t.amount
    return float(bal)


def _daily_expense_stats(db: Session, user_id: str, as_of: date, lookback_days: int = 28) -> dict:
    start = as_of - timedelta(days=lookback_days)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= as_of,
        Transaction.type == "expense",
    )
    txns = list(db.execute(stmt).scalars().all())

    by_day: dict[date, float] = defaultdict(float)
    by_dow: dict[int, list[float]] = defaultdict(list)
    by_cat: dict[str, float] = defaultdict(float)
    for t in txns:
        by_day[t.date] += t.amount
        by_dow[t.date.weekday()].append(t.amount)
        by_cat[t.category] += t.amount

    days = max(1, lookback_days)
    total = sum(by_day.values())
    avg_per_day = safe_div(total, days, 0.0)
    # weekend multiplier based on observed pattern
    weekend = by_dow.get(5, []) + by_dow.get(6, [])
    weekday = (
        by_dow.get(0, [])
        + by_dow.get(1, [])
        + by_dow.get(2, [])
        + by_dow.get(3, [])
        + by_dow.get(4, [])
    )
    weekend_avg = safe_div(sum(weekend), max(1, len(weekend)), 0.0)
    weekday_avg = safe_div(sum(weekday), max(1, len(weekday)), 0.0)
    weekend_multiplier = clamp(safe_div(weekend_avg, max(0.01, weekday_avg), 1.0), 0.8, 1.8)

    return {
        "avg_per_day": float(avg_per_day),
        "weekend_multiplier": float(weekend_multiplier),
        "top_categories": sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:5],
    }


def _expected_income_schedule(user: User, as_of: date, horizon_days: int) -> dict[date, float]:
    # MVP: approximate income cadence using monthly estimate.
    # Later: derive from actual paychecks + payroll detection + calendaring.
    sched: dict[date, float] = defaultdict(float)
    if user.monthly_income_estimate <= 0:
        return sched

    freq = user.income_frequency
    if freq == "monthly":
        amount = user.monthly_income_estimate
        pay = (as_of.replace(day=1) + timedelta(days=32)).replace(day=1)  # first of next month
        while pay <= as_of + timedelta(days=horizon_days):
            sched[pay] += amount
            pay = (pay + timedelta(days=32)).replace(day=1)
    elif freq == "biweekly":
        amount = user.monthly_income_estimate / 2.0
        pay = as_of + timedelta(days=14 - (as_of.toordinal() % 14))
        for _ in range(0, horizon_days + 1, 14):
            if pay <= as_of + timedelta(days=horizon_days):
                sched[pay] += amount
            pay += timedelta(days=14)
    elif freq == "weekly":
        amount = user.monthly_income_estimate / 4.0
        pay = as_of + timedelta(days=7 - as_of.weekday())  # next Monday-ish
        for _ in range(0, horizon_days + 1, 7):
            if pay <= as_of + timedelta(days=horizon_days):
                sched[pay] += amount
            pay += timedelta(days=7)
    else:
        # irregular: no schedule
        return sched

    return sched


def forecast(db: Session, user: User, *, as_of: date | None = None, horizon_days: int = 30) -> ForecastResult:
    as_of = as_of or date.today()
    current_balance = _balance_as_of(db, user, as_of)
    stats = _daily_expense_stats(db, user.id, as_of, lookback_days=28)
    income_sched = _expected_income_schedule(user, as_of, horizon_days)

    curve: list[tuple[date, float]] = []
    bal = current_balance
    days_until_broke: int | None = None

    for i, d in enumerate(daterange(as_of, horizon_days + 1)):
        if i == 0:
            curve.append((d, float(bal)))
            continue
        # expenses: base avg, with weekend multiplier
        multiplier = stats["weekend_multiplier"] if d.weekday() in (5, 6) else 1.0
        expected_expense = stats["avg_per_day"] * multiplier
        bal = bal - expected_expense + income_sched.get(d, 0.0)
        curve.append((d, float(bal)))
        if days_until_broke is None and bal <= 0:
            days_until_broke = i

    min_bal = min(b for _, b in curve)
    buffer = DEFAULT_SAFETY_BUFFER
    if min_bal > buffer:
        safety_status = "safe"
        summary = "You look on track to stay above your safety buffer in the next month."
    elif min_bal > 0:
        safety_status = "tight"
        summary = "Your buffer looks tight — a couple of high-spend days could push you uncomfortably low."
    else:
        safety_status = "at_risk"
        du = days_until_broke if days_until_broke is not None else 0
        summary = f"At your current pace, your balance may hit $0 in about {du} days."

    return ForecastResult(
        as_of=as_of,
        current_balance=float(current_balance),
        curve=curve,
        days_until_broke=days_until_broke,
        safety_status=safety_status,
        summary=summary,
    )

