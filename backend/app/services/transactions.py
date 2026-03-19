from __future__ import annotations

from datetime import date

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.orm import Session

from app.models import Transaction


def list_transactions(
    db: Session,
    *,
    user_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    type: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[Transaction]:
    clauses = [Transaction.user_id == user_id]
    if start_date:
        clauses.append(Transaction.date >= start_date)
    if end_date:
        clauses.append(Transaction.date <= end_date)
    if category:
        clauses.append(Transaction.category == category)
    if type:
        clauses.append(Transaction.type == type)

    stmt = (
        select(Transaction)
        .where(and_(*clauses))
        .order_by(desc(Transaction.date), desc(Transaction.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def create_transaction(db: Session, txn: Transaction) -> Transaction:
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def get_transaction(db: Session, txn_id: str) -> Transaction | None:
    stmt = select(Transaction).where(Transaction.id == txn_id)
    return db.execute(stmt).scalars().first()


def update_transaction(db: Session, txn: Transaction) -> Transaction:
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, txn_id: str) -> None:
    db.execute(delete(Transaction).where(Transaction.id == txn_id))
    db.commit()

