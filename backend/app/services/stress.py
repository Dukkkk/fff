from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction, User
from app.services.forecast import forecast
from app.utils import clamp, safe_div


@dataclass(frozen=True)
class StressResult:
    score: int
    label: str
    explanation: str
    drivers: dict[str, float]


def _recent_volatility(db: Session, user_id: str, as_of: date, days: int = 21) -> float:
    start = as_of - timedelta(days=days)
    stmt = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= as_of,
        Transaction.type == "expense",
    )
    txns = list(db.execute(stmt).scalars().all())
    if len(txns) < 8:
        return 0.25
    amts = [t.amount for t in txns]
    mean = safe_div(sum(amts), len(amts), 0.0)
    var = safe_div(sum((x - mean) ** 2 for x in amts), len(amts), 0.0)
    std = var**0.5
    # coefficient of variation
    return float(clamp(safe_div(std, max(0.01, mean), 0.0), 0.0, 2.0))


def _income_regular(db: Session, user: User, as_of: date) -> float:
    # MVP proxy: uses user income_frequency plus presence of recent income txns.
    start = as_of - timedelta(days=45)
    stmt = select(Transaction).where(
        Transaction.user_id == user.id,
        Transaction.date >= start,
        Transaction.date <= as_of,
        Transaction.type == "income",
    )
    incomes = list(db.execute(stmt).scalars().all())
    freq = user.income_frequency
    base = {"weekly": 0.85, "biweekly": 0.78, "monthly": 0.7, "irregular": 0.35}[freq]
    if len(incomes) >= 2:
        base = min(1.0, base + 0.1)
    return float(clamp(base, 0.0, 1.0))


def compute_stress_score(db: Session, user: User, *, as_of: date | None = None) -> StressResult:
    as_of = as_of or date.today()
    fc = forecast(db, user, as_of=as_of, horizon_days=30)

    # Drivers normalized 0..1 where higher is worse (except income stability)
    volatility = _recent_volatility(db, user.id, as_of)  # 0..2
    volatility_n = clamp(volatility / 1.2, 0.0, 1.0)

    income_stability = _income_regular(db, user, as_of)  # 0..1 higher better
    income_instability = 1.0 - income_stability

    buffer = max(0.0, fc.current_balance)
    buffer_n = clamp(1.0 - (buffer / 1000.0), 0.0, 1.0)  # < $1k buffer => higher stress

    shortfall_risk = 1.0 if fc.safety_status == "at_risk" else 0.55 if fc.safety_status == "tight" else 0.2

    low_balance_freq = 0.0
    if fc.days_until_broke is not None:
        low_balance_freq = clamp((30 - fc.days_until_broke) / 30.0, 0.0, 1.0)

    drivers = {
        "shortfall_risk": float(shortfall_risk),
        "buffer_thinness": float(buffer_n),
        "spending_volatility": float(volatility_n),
        "income_instability": float(income_instability),
        "low_balance_pressure": float(low_balance_freq),
    }

    # weighted score
    score_f = (
        0.33 * drivers["shortfall_risk"]
        + 0.22 * drivers["buffer_thinness"]
        + 0.18 * drivers["spending_volatility"]
        + 0.17 * drivers["income_instability"]
        + 0.10 * drivers["low_balance_pressure"]
    )
    score = int(round(clamp(score_f, 0.0, 1.0) * 100))

    if score >= 70:
        label = "high"
        explanation = "Your buffer is thin and the next few weeks look tight. A couple of targeted cuts can quickly reduce pressure."
    elif score >= 40:
        label = "moderate"
        explanation = "You’re mostly stable, but your cash flow has a few pressure points. A small buffer boost would improve resilience."
    else:
        label = "low"
        explanation = "Your cash flow looks stable right now. Keep the good habits and consider automating savings to lock it in."

    return StressResult(score=score, label=label, explanation=explanation, drivers=drivers)


def compute_risk_profile(db: Session, user: User, *, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    fc = forecast(db, user, as_of=as_of, horizon_days=30)
    stress = compute_stress_score(db, user, as_of=as_of)

    income_stability = 1.0 - stress.drivers["income_instability"]
    surplus_signal = clamp(fc.current_balance / 1500.0, 0.0, 1.0)
    buffer_signal = 1.0 - stress.drivers["buffer_thinness"]
    volatility_signal = 1.0 - stress.drivers["spending_volatility"]

    signals = {
        "income_stability": float(income_stability),
        "buffer_strength": float(buffer_signal),
        "surplus_capacity": float(surplus_signal),
        "spending_control": float(volatility_signal),
    }

    readiness = 0.35 * signals["buffer_strength"] + 0.30 * signals["income_stability"] + 0.20 * signals[
        "spending_control"
    ] + 0.15 * signals["surplus_capacity"]

    if readiness < 0.45:
        profile = "cautious"
        explanation = "Focus on liquidity and predictability first: build a small buffer and reduce volatility before taking on longer-term risk."
    elif readiness < 0.72:
        profile = "balanced"
        explanation = "You’re in a decent spot — keep building buffer and consistency. Once you’re comfortably above your safety floor, you’ll be ready for more growth-focused steps."
    else:
        profile = "growth-ready"
        explanation = "Your cash flow is stable and your buffer is solid. You can start thinking about longer-term growth after keeping your safety buffer intact."

    return {"profile": profile, "explanation": explanation, "signals": signals}

