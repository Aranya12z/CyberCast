"""
app/api/predictions.py — Thin REST API router for prediction triggering & retrieval.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/predictions/*
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.prediction_orchestration import (
    get_latest_prediction_for_crime,
    run_prediction_pipeline,
)
from app.schemas.prediction import PredictionResponse

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post(
    "/{crime_id}",
    response_model=PredictionResponse,
    summary="Trigger synchronous prediction generation (Mode A)",
)
def trigger_prediction(
    crime_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Triggers synchronous 8-step prediction pipeline for a crime complaint.
    Returns Top-K risk-ranked candidate ATMs with explanations.
    """
    return run_prediction_pipeline(db=db, crime_id=crime_id)


@router.get(
    "/{crime_id}",
    response_model=PredictionResponse,
    summary="Retrieve latest prediction run for a crime",
)
def get_prediction_by_crime(
    crime_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve the most recent prediction run for a crime incident."""
    prediction_data = get_latest_prediction_for_crime(db=db, crime_id=crime_id)
    if not prediction_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prediction runs found for crime '{crime_id}'",
        )
    return prediction_data
