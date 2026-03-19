from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Insight, Transaction
from app.utils import clamp, safe_div


def _load_recent_txns(db: Session, user_id: str, as_of: date, lookback_days: int = 60) -> list[Transaction]:
    start = as_of - timedelta(days=lookback_days)
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id, Transaction.date >= start, Transaction.date <= as_of)
        .order_by(desc(Transaction.date))
        .limit(5000)
    )
    return list(db.execute(stmt).scalars().all())


def generate_insights(db: Session, user_id: str, *, as_of: date | None = None) -> list[Insight]:
    as_of = as_of or date.today()
    txns = _load_recent_txns(db, user_id, as_of, 60)

    expenses = [t for t in txns if t.type == "expense"]
    if not expenses:
        return []

    insights: list[Insight] = []

    # Weekend overspend (Sat/Sun vs weekdays)
    wknd = [t.amount for t in expenses if t.date.weekday() in (5, 6)]
    wkdy = [t.amount for t in expenses if t.date.weekday() not in (5, 6)]
    wknd_avg = safe_div(sum(wknd), max(1, len(wknd)))
    wkdy_avg = safe_div(sum(wkdy), max(1, len(wkdy)))
    ratio = safe_div(wknd_avg, max(0.01, wkdy_avg), 1.0)
    if ratio >= 1.35 and len(wknd) >= 6:
        sev = "high" if ratio >= 1.7 else "medium"
        insights.append(
            Insight(
                user_id=user_id,
                type="weekend_overspend",
                title="Weekend spending is dragging your plan",
                description=f"You spend about {ratio:.1f}x more per transaction on weekends than weekdays. A small weekend cap could meaningfully extend your runway.",
                severity=sev,
            )
        )

    # Late-night food delivery spikes (merchant/note heuristic)
    late = []
    base = []
    for t in expenses:
        text = (t.merchant or "") + " " + (t.note or "")
        if t.category in ("food", "entertainment") and any(
            k in text.lower() for k in ("ubereats", "doordash", "deliveroo", "grubhub", "delivery")
        ):
            # approximate "late-night" by tag keyword (seed adds it) for MVP
            if t.tags and "late-night" in t.tags:
                late.append(t.amount)
            else:
                base.append(t.amount)

    if len(late) >= 4:
        late_avg = safe_div(sum(late), len(late))
        base_avg = safe_div(sum(base), max(1, len(base)), late_avg)
        ratio_ln = safe_div(late_avg, max(0.01, base_avg), 1.0)
        if ratio_ln >= 1.3:
            sev = "medium" if ratio_ln < 1.8 else "high"
            insights.append(
                Insight(
                    user_id=user_id,
                    type="late_night_delivery",
                    title="Late-night delivery is quietly expensive",
                    description=f"Your late-night delivery orders run about {ratio_ln:.1f}x higher than your other food spends. Try a 10PM cutoff or a preset cart limit.",
                    severity=sev,
                )
            )

    # Subscription creep: repeated merchants with small monthly-ish charges
    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for t in expenses:
        if t.merchant:
            by_merchant[t.merchant.lower()].append(t)
    subs = []
    for m, ts in by_merchant.items():
        if len(ts) >= 2:
            amounts = [x.amount for x in ts]
            avg = safe_div(sum(amounts), len(amounts))
            if avg <= 35:  # typical subscription size
                ts_sorted = sorted(ts, key=lambda x: x.date)
                gaps = [(ts_sorted[i + 1].date - ts_sorted[i].date).days for i in range(len(ts_sorted) - 1)]
                if gaps and any(24 <= g <= 34 for g in gaps):
                    subs.append((m, avg))
    if subs:
        m, avg = sorted(subs, key=lambda x: x[1], reverse=True)[0]
        insights.append(
            Insight(
                user_id=user_id,
                type="subscription_creep",
                title="Subscriptions are adding up",
                description=f"We detected recurring charges like “{m.title()}” (~${avg:.0f}). Reviewing subscriptions this week could free up breathing room.",
                severity="medium",
            )
        )

    # Small daily purchases add up in a category
    by_cat_small: dict[str, float] = defaultdict(float)
    by_cat_cnt: dict[str, int] = defaultdict(int)
    for t in expenses:
        if t.amount <= 12:
            by_cat_small[t.category] += t.amount
            by_cat_cnt[t.category] += 1
    if by_cat_small:
        cat, total = sorted(by_cat_small.items(), key=lambda kv: kv[1], reverse=True)[0]
        cnt = by_cat_cnt[cat]
        if total >= 80 and cnt >= 8:
            sev = "medium" if total < 140 else "high"
            insights.append(
                Insight(
                    user_id=user_id,
                    type="small_spends_add_up",
                    title=f"Small {cat} spends are adding up",
                    description=f"{cnt} small purchases in {cat} added up to about ${total:.0f} recently. Bundling purchases or setting a tiny daily cap could help without feeling restrictive.",
                    severity=sev,
                )
            )

    # Unusual purchase: large outlier vs recent distribution
    amounts = sorted([t.amount for t in expenses])
    p90 = amounts[int(0.9 * (len(amounts) - 1))]
    recent_7 = [t for t in expenses if t.date >= as_of - timedelta(days=7)]
    big_recent = [t for t in recent_7 if t.amount >= max(80, 2.0 * p90)]
    if big_recent:
        t = sorted(big_recent, key=lambda x: x.amount, reverse=True)[0]
        insights.append(
            Insight(
                user_id=user_id,
                type="unusual_purchase",
                title="A recent purchase stands out",
                description=f"${t.amount:.0f} in {t.category} ({t.merchant or 'recent purchase'}) is unusually high compared to your typical spending. If it’s one-off, you’re fine — if it repeats, it’ll squeeze your month.",
                severity="low",
            )
        )

    # Persist (replace existing generated insights for MVP simplicity)
    # In a real system: upsert by (user_id, type, window) and keep history.
    now = datetime.utcnow()
    for ins in insights:
        ins.created_at = now
        db.add(ins)
    db.commit()
    return insights


def list_latest_insights(db: Session, user_id: str, limit: int = 10) -> list[Insight]:
    stmt = (
        select(Insight)
        .where(Insight.user_id == user_id)
        .order_by(desc(Insight.created_at))
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())

