"""
app/domain/transaction_management.py — Transaction queries and filtering.

Layer: L3 (Domain/Intelligence)
Reference: API_SPEC.md §/api/transactions/*
"""
from __future__ import annotations

from datetime import datetime
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def list_transactions(
    db: Session,
    atm_id: Optional[uuid.UUID] = None,
    account_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Transaction]:
    """Filter transactions by ATM, account, or timestamp range."""
    query = db.query(Transaction)
    if atm_id:
        query = query.filter(Transaction.atm_id == atm_id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if start_time:
        query = query.filter(Transaction.timestamp >= start_time)
    if end_time:
        query = query.filter(Transaction.timestamp <= end_time)

    return (
        query.order_by(Transaction.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
