"""
app/schemas/dashboard.py — Pydantic schemas for dashboard summary.

Reference: API_SPEC.md §/api/dashboard/*
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class PredictionStats(BaseModel):
    total_predictions_run: int = Field(default=0, description="Total count of prediction runs")
    avg_confidence: float = Field(default=0.0, description="Mean confidence score [0, 1]")
    insufficient_evidence_rate: float = Field(
        default=0.0, description="Fraction of runs returning insufficient_evidence"
    )

    model_config = ConfigDict(from_attributes=True)


class RecentActivityItem(BaseModel):
    type: str = Field(
        ...,
        description="Activity type: prediction_generated | alert_created | alert_acknowledged | etc.",
    )
    timestamp: datetime = Field(..., description="Event timestamp (UTC)")
    crime_id: Optional[str] = Field(default=None, description="Affected crime UUID if applicable")
    summary: str = Field(..., description="Human-readable event summary")

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    """Dashboard aggregate summary matching API_SPEC.md §/api/dashboard/*"""
    active_alerts: int = Field(default=0, description="Count of alerts with status 'new'")
    high_risk_predictions: int = Field(
        default=0, description="Count of prediction results with risk_score >= 0.7"
    )
    prediction_stats: PredictionStats = Field(
        default_factory=PredictionStats, description="Aggregated prediction performance metrics"
    )
    recent_activity: List[RecentActivityItem] = Field(
        default_factory=list, description="Recent operational activity items"
    )

    model_config = ConfigDict(from_attributes=True)
