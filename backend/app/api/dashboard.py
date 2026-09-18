"""
app/api/dashboard.py — Thin REST API router for dashboard metrics.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/dashboard/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.dashboard_summary import get_dashboard_summary
from app.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse, summary="Get dashboard summary metrics")
def get_summary(db: Session = Depends(get_db)):
    """Retrieve operational dashboard summary metrics and activity."""
    return get_dashboard_summary(db=db)
