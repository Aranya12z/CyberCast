"""
app/schemas/transaction.py — Pydantic schemas for transaction resources.

Reference: API_SPEC.md §/api/transactions/*
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TransactionResponse(BaseModel):
    """Transaction object schema matching API_SPEC.md §/api/transactions/*"""
    transaction_id: str = Field(..., description="Unique transaction UUID")
    atm_id: str = Field(..., description="Associated ATM UUID")
    timestamp: datetime = Field(..., description="Transaction timestamp (UTC)")
    amount: float = Field(..., ge=0.0, description="Transaction amount in INR")
    account_id: str = Field(..., description="Synthetic/anonymized account identifier")

    model_config = ConfigDict(from_attributes=True)
