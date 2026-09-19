"""
app/schemas/intelligence.py — Pydantic schemas for /api/intelligence/{crime_id}.

Reference: API_SPEC.md §/api/intelligence/*
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import LocationSchema, PredictedWindow
from app.schemas.crime import CrimeResponse
from app.schemas.prediction import ExplanationItem


class TopResultItem(BaseModel):
    atm_id: str = Field(..., description="Target ATM UUID")
    bank: Optional[str] = Field(default=None, description="Bank name")
    area: Optional[str] = Field(default=None, description="Area / locality name")
    location: Optional[LocationSchema] = Field(
        default=None, description="ATM WGS84 coordinates"
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Predicted risk likelihood [0, 1]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Certainty score [0, 1]")
    predicted_window: PredictedWindow = Field(..., description="6-hour operational window (UTC)")

    model_config = ConfigDict(from_attributes=True)


class LatestPredictionSummary(BaseModel):
    generated_at: datetime = Field(..., description="Prediction timestamp (UTC)")
    model_version: str = Field(..., description="Model version tag")
    status: Literal["ok", "insufficient_confidence", "insufficient_evidence"] = Field(
        ..., description="Prediction status"
    )
    top_result: Optional[TopResultItem] = Field(
        default=None, description="Winning candidate result or None"
    )

    model_config = ConfigDict(from_attributes=True)


class RelatedAlertItem(BaseModel):
    alert_id: str = Field(..., description="Alert UUID")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity")
    status: Literal["new", "acknowledged", "resolved"] = Field(..., description="Lifecycle status")

    model_config = ConfigDict(from_attributes=True)


class IntelligenceResponse(BaseModel):
    """
    Intelligence report payload strictly conforming to API_SPEC.md §/api/intelligence/*
    """
    crime_id: str = Field(..., description="Associated crime incident UUID")
    crime: CrimeResponse = Field(..., description="Crime details")
    latest_prediction: Optional[LatestPredictionSummary] = Field(
        default=None, description="Latest prediction summary or None"
    )
    evidence: List[ExplanationItem] = Field(
        default_factory=list, description="Winning candidate feature contributions"
    )
    related_alerts: List[RelatedAlertItem] = Field(
        default_factory=list, description="Associated alerts"
    )
    summary: str = Field(..., description="Human-readable operational briefing summary")

    model_config = ConfigDict(from_attributes=True)
