from __future__ import annotations

import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.models import Goal, Transaction, User


CATEGORIES = [
    "food",
    "transport",
    "rent",
    "shopping",
    "entertainment",
    "bills",
    "savings",
    "health",
    "salary",
    "freelance",
    "other",
]


def _d(days_ago: int) -> date:
    return (date.today() - timedelta(days=days_ago))


def seed(db: Session) -> dict:
    # reset for MVP demo
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    user = User(
        name="Ava",
        email=None,
        income_frequency="biweekly",
        monthly_income_estimate=4200.0,
        starting_balance=900.0,
        created_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # salary cadence every 14 days, with "salary-week impulse spending" pattern
    salary_days = [56, 42, 28, 14, 0]
    for ago in salary_days:
        db.add(
            Transaction(
                user_id=user.id,
                date=_d(ago),
                amount=2100.0,
                type="income",
                category="salary",
                merchant="Employer Payroll",
                note="Paycheck",
                tags=None,
                created_at=datetime.now(UTC),
            )
        )

    # recurring rent + subscriptions
    for ago in [55, 25]:
        db.add(
            Transaction(
                user_id=user.id,
                date=_d(ago),
                amount=1450.0,
                type="expense",
                category="rent",
                merchant="Landlord",
                note="Rent",
                tags="fixed",
                created_at=datetime.now(UTC),
            )
        )
    subs = [("Spotify", 11.99), ("Netflix", 16.99), ("iCloud", 2.99)]
    for m, amt in subs:
        for ago in [50, 20]:
            db.add(
                Transaction(
                    user_id=user.id,
                    date=_d(ago),
                    amount=amt,
                    type="expense",
                    category="bills",
                    merchant=m,
                    note="Subscription",
                    tags="subscription",
                    created_at=datetime.now(UTC),
                )
            )

    # transport baseline
    for ago in range(1, 60):
        if random.random() < 0.35:
            db.add(
                Transaction(
                    user_id=user.id,
                    date=_d(ago),
                    amount=round(random.uniform(2.75, 18.0), 2),
                    type="expense",
                    category="transport",
                    merchant=random.choice(["Metro", "Uber", "Lyft", "Gas Station"]),
                    note=None,
                    tags="small",
                    created_at=datetime.now(UTC),
                )
            )

    # groceries + food delivery with late-night pattern
    for ago in range(1, 60):
        dow = _d(ago).weekday()
        # groceries 1-2x/week
        if dow in (1, 5) and random.random() < 0.65:
            db.add(
                Transaction(
                    user_id=user.id,
                    date=_d(ago),
                    amount=round(random.uniform(45, 115), 2),
                    type="expense",
                    category="food",
                    merchant=random.choice(["Trader Joe's", "Whole Foods", "Local Market"]),
                    note="Groceries",
                    tags="groceries",
                    created_at=datetime.now(UTC),
                )
            )
        # delivery spikes 2-3x/week, biased to Thu-Sun and late-night tags
        if random.random() < (0.18 if dow in (3, 4, 5, 6) else 0.09):
            late = random.random() < (0.55 if dow in (4, 5, 6) else 0.35)
            amt = random.uniform(18, 55) * (1.25 if late else 1.0)
            db.add(
                Transaction(
                    user_id=user.id,
                    date=_d(ago),
                    amount=round(amt, 2),
                    type="expense",
                    category="food",
                    merchant=random.choice(["UberEats", "DoorDash"]),
                    note="Delivery",
                    tags="late-night" if late else "delivery",
                    created_at=datetime.now(UTC),
                )
            )

    # weekend entertainment spikes
    for ago in range(1, 60):
        d = _d(ago)
        if d.weekday() in (5, 6) and random.random() < 0.30:
            db.add(
                Transaction(
                    user_id=user.id,
                    date=d,
                    amount=round(random.uniform(20, 95), 2),
                    type="expense",
                    category="entertainment",
                    merchant=random.choice(["Bar", "Cinema", "Concert", "Events"]),
                    note=None,
                    tags="weekend",
                    created_at=datetime.now(UTC),
                )
            )

    # salary-week impulse shopping (first 3 days after income)
    income_dates = {_d(ago) for ago in salary_days}
    for inc in income_dates:
        for delta in [1, 2, 3]:
            if random.random() < 0.55:
                db.add(
                    Transaction(
                        user_id=user.id,
                        date=inc + timedelta(days=delta),
                        amount=round(random.uniform(35, 220), 2),
                        type="expense",
                        category="shopping",
                        merchant=random.choice(["Amazon", "Target", "Online Store"]),
                        note="Impulse buy",
                        tags="post-payday",
                        created_at=datetime.now(UTC),
                    )
                )

    # a couple unusual spikes
    db.add(
        Transaction(
            user_id=user.id,
            date=_d(9),
            amount=289.0,
            type="expense",
            category="shopping",
            merchant="Electronics",
            note="Headphones",
            tags="one-off",
            created_at=datetime.now(UTC),
        )
    )

    # goal
    goal = Goal(
        user_id=user.id,
        title="Emergency Fund",
        target_amount=2500.0,
        target_date=date.today() + timedelta(days=150),
        current_amount=420.0,
        category="savings",
        created_at=datetime.now(UTC),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return {"user_id": user.id, "goal_id": goal.id}


def main():
    db = SessionLocal()
    try:
        ids = seed(db)
        print("Seeded demo data.")
        print(ids)
    finally:
        db.close()


if __name__ == "__main__":
    main()

