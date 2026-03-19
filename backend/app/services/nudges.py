from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Nudge, User
from app.services.forecast import ForecastResult, forecast
from app.services.insights import list_latest_insights
from app.services.stress import compute_stress_score


@dataclass(frozen=True)
class NudgeCandidate:
    title: str
    message: str
    action_label: str | None
    priority: int


def _nudge_for_cash_risk(fc: ForecastResult) -> NudgeCandidate | None:
    if fc.safety_status == "at_risk":
        du = fc.days_until_broke or 0
        return NudgeCandidate(
            title="Protect your runway",
            message=f"If you keep spending at this pace, you may run short in about {du} days. Try a 48‑hour “low-spend mode” to reset momentum.",
            action_label="Enter low-spend mode",
            priority=100,
        )
    if fc.safety_status == "tight":
        return NudgeCandidate(
            title="Keep a little breathing room",
            message="You’re likely to stay positive, but your buffer is tight. Cutting just 1–2 non‑essential spends this week can keep you comfortably above your floor.",
            action_label="Set a category cap",
            priority=70,
        )
    return NudgeCandidate(
        title="Lock in what’s working",
        message="Your cash flow looks stable right now. Consider moving a small amount to savings today so this week’s stability becomes a habit.",
        action_label="Move money to savings",
        priority=35,
    )


def _nudge_from_top_insight(insight_title: str, insight_type: str) -> NudgeCandidate | None:
    if insight_type == "late_night_delivery":
        return NudgeCandidate(
            title="Make late-night spending harder",
            message="Late-night delivery tends to be your costly default. A simple rule: decide before 10PM what you’ll eat — future-you will thank you.",
            action_label="Delay this purchase",
            priority=80,
        )
    if insight_type == "weekend_overspend":
        return NudgeCandidate(
            title="Put weekends on rails",
            message="Weekends are where your plan gets nudged off-track. Try a weekend “fun budget” you can spend guilt-free — and stop when it’s gone.",
            action_label="Set a weekend cap",
            priority=75,
        )
    if insight_type == "subscription_creep":
        return NudgeCandidate(
            title="Win back easy money",
            message="Subscriptions are sneaky because they feel small. Canceling just one you don’t use could buy you real breathing room every month.",
            action_label="Review subscriptions",
            priority=65,
        )
    if insight_type == "small_spends_add_up":
        return NudgeCandidate(
            title="Tiny cap, big effect",
            message="Small daily spends add up fast. Try a micro‑cap today: pick one category and keep it under a small number — just for 24 hours.",
            action_label="Start a 24h cap",
            priority=60,
        )
    return NudgeCandidate(
        title="One small upgrade",
        message=f"Based on your recent pattern (“{insight_title}”), a tiny rule change this week could noticeably reduce stress without feeling restrictive.",
        action_label="Set a rule",
        priority=45,
    )


def generate_nudges(db: Session, user: User, *, as_of: date | None = None, limit: int = 3) -> list[Nudge]:
    as_of = as_of or date.today()
    fc = forecast(db, user, as_of=as_of, horizon_days=30)
    stress = compute_stress_score(db, user, as_of=as_of)
    latest = list_latest_insights(db, user.id, limit=5)

    candidates: list[NudgeCandidate] = []
    cash = _nudge_for_cash_risk(fc)
    if cash:
        candidates.append(cash)

    if latest:
        top = latest[0]
        candidates.append(_nudge_from_top_insight(top.title, top.type))

    # framing based on stress
    if stress.label == "high":
        candidates.append(
            NudgeCandidate(
                title="Reduce pressure fast",
                message="When stress is high, don’t aim for perfect — aim for fewer decisions. Pick 1 category to pause for 3 days and let the runway recover.",
                action_label="Pause non-essentials",
                priority=85,
            )
        )
    elif stress.label == "low":
        candidates.append(
            NudgeCandidate(
                title="Build a streak",
                message="You’re doing well. Keeping the streak alive is easier than restarting it — schedule a tiny auto‑transfer to savings to lock in momentum.",
                action_label="Automate savings",
                priority=50,
            )
        )

    # prioritize and persist
    uniq = {}
    for c in sorted(candidates, key=lambda x: x.priority, reverse=True):
        uniq[c.title] = c
    chosen = list(uniq.values())[:limit]

    now = datetime.utcnow()
    out: list[Nudge] = []
    for c in chosen:
        n = Nudge(user_id=user.id, title=c.title, message=c.message, action_label=c.action_label, created_at=now)
        db.add(n)
        out.append(n)
    db.commit()
    for n in out:
        db.refresh(n)
    return out

