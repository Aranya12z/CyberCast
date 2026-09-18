"""
app/schemas/prediction.py — Pydantic schemas for prediction endpoint response.

Reference: API_SPEC.md §/api/predictions/*
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LocationSchema, PredictedWindow


class ExplanationItem(BaseModel):
    """One feature explanation entry within a Top-K result."""
    feature: str = Field(..., description="Feature name (e.g. distance_from_crime)")
    value: float = Field(..., description="Feature value")
    contribution: Literal["high", "medium", "low"] = Field(
        ..., description="Contribution bucket: high | medium | low"
    )

    model_config = ConfigDict(from_attributes=True)


class PredictionResultItem(BaseModel):
    """One Top-K candidate ATM result within a prediction run."""
    atm_id: str = Field(..., description="Candidate ATM UUID")
    bank: Optional[str] = Field(default=None, description="Bank name (derived from ATM)")
    area: Optional[str] = Field(default=None, description="Area name (derived from ATM)")
    location: Optional[LocationSchema] = Field(
        default=None, description="ATM WGS84 location coordinates"
    )
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Predicted risk score [0, 1]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score [0, 1]")
    predicted_window: PredictedWindow = Field(
        ..., description="Predicted withdrawal time window (start & end UTC)"
    )
    explanation: List[ExplanationItem] = Field(
        default_factory=list, description="Top contributing feature explanations"
    )

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    """
    The core prediction response contract matching API_SPEC.md §/api/predictions/*
    
    Rule (ARCHITECTURE.md §10): if the model cannot produce a confident prediction,
    status must reflect that honestly: ok | insufficient_confidence | insufficient_evidence.
    """
    crime_id: str = Field(..., description="Associated crime incident UUID")
    generated_at: datetime = Field(..., description="Timestamp of prediction run (UTC)")
    model_version: str = Field(..., description="Model version tag used for inference")
    predictions: List[PredictionResultItem] = Field(
        ..., description="Top-K predicted candidate ATMs ranked by risk"
    )
    status: Literal["ok", "insufficient_confidence", "insufficient_evidence"] = Field(
        ..., description="Prediction run status: ok | insufficient_confidence | insufficient_evidence"
    )

    model_config = ConfigDict(from_attributes=True)
