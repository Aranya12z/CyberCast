"""
app/schemas/alert.py — Pydantic schemas for alerts.

Reference: API_SPEC.md §/api/alerts/*
ADR reference: ADRS.md ADR-006 (Alert Generation Thresholds & Deduplication)
"""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertResponse(BaseModel):
    """
    Alert object schema matching API_SPEC.md §/api/alerts/*
    """
    alert_id: str = Field(..., description="Unique UUID of the alert")
    crime_id: str = Field(..., description="Associated crime incident UUID")
    atm_id: str = Field(..., description="Target ATM UUID")
    bank: Optional[str] = Field(default=None, description="Bank name (derived from ATM)")
    area: Optional[str] = Field(default=None, description="Area / locality name (derived from ATM)")
    severity: Literal["low", "medium", "high"] = Field(
        ..., description="Alert severity: low | medium | high"
    )
    created_at: datetime = Field(..., description="Alert generation timestamp (UTC)")
    status: Literal["new", "acknowledged", "resolved"] = Field(
        ..., description="Lifecycle status: new | acknowledged | resolved"
    )
    channel: Literal["dashboard", "mock_sms", "mock_email"] = Field(
        ..., description="Delivery channel: dashboard | mock_sms | mock_email"
    )

    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledgeResponse(BaseModel):
    success: bool = True
    alert_id: str
    status: Literal["acknowledged", "resolved"] = "acknowledged"
