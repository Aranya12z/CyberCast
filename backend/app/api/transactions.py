"""
app/api/transactions.py — Thin REST API router for transaction history.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/transactions/*
"""
from datetime import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role
from app.domain.transaction_management import list_transactions
from app.models.user import User
from app.schemas.transaction import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=List[TransactionResponse], summary="List / filter transactions")
def get_transactions(
    atm_id: Optional[uuid.UUID] = Query(None, description="Filter by ATM UUID"),
    account_id: Optional[str] = Query(None, description="Filter by account identifier"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO 8601 UTC)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO 8601 UTC)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("investigator", "bank_analyst", "administrator")),
    db: Session = Depends(get_db),
):
    """Filter transactions by ATM, account, or timestamp range."""
    txns = list_transactions(
        db=db,
        atm_id=atm_id,
        account_id=account_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return [
        TransactionResponse(
            transaction_id=str(t.transaction_id),
            atm_id=str(t.atm_id),
            timestamp=t.timestamp,
            amount=float(t.amount),
            account_id=t.account_id,
        )
        for t in txns
    ]
