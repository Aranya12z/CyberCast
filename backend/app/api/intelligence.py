"""
app/api/intelligence.py — Thin REST API router for crime intelligence dossiers.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/intelligence/*
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.intelligence_generation import generate_intelligence_report
from app.schemas.intelligence import IntelligenceResponse

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get(
    "/{crime_id}",
    response_model=IntelligenceResponse,
    summary="Get intelligence dossier for a crime",
)
def get_intelligence(
    crime_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve joined intelligence report for a crime incident."""
    return generate_intelligence_report(db=db, crime_id=crime_id)
