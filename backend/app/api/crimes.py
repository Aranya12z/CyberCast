"""
app/api/crimes.py — Thin REST API router for crime complaints.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/crimes/*
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.complaint_processing import (
    create_complaint,
    get_complaint,
    list_complaints,
)
from app.schemas.crime import CrimeCreate, CrimeResponse

router = APIRouter(prefix="/crimes", tags=["crimes"])


@router.get("", response_model=List[CrimeResponse], summary="List crime complaints")
def get_crimes(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List recent complaints."""
    crimes = list_complaints(db=db, limit=limit, offset=offset)
    return [
        CrimeResponse(
            crime_id=str(c.crime_id),
            crime_type=c.crime_type,
            timestamp=c.timestamp,
            location={"lat": float(c.latitude), "lng": float(c.longitude)},
            amount=float(c.amount),
        )
        for c in crimes
    ]


@router.get("/{crime_id}", response_model=CrimeResponse, summary="Get crime complaint details")
def get_crime_by_id(
    crime_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve details of a single crime incident."""
    crime = get_complaint(db=db, crime_id=crime_id)
    return CrimeResponse(
        crime_id=str(crime.crime_id),
        crime_type=crime.crime_type,
        timestamp=crime.timestamp,
        location={"lat": float(crime.latitude), "lng": float(crime.longitude)},
        amount=float(crime.amount),
    )


@router.post("", response_model=CrimeResponse, status_code=201, summary="Ingest crime complaint")
def post_crime(
    crime_in: CrimeCreate,
    db: Session = Depends(get_db),
):
    """Ingest and validate a new crime complaint."""
    crime = create_complaint(db=db, crime_in=crime_in)
    return CrimeResponse(
        crime_id=str(crime.crime_id),
        crime_type=crime.crime_type,
        timestamp=crime.timestamp,
        location={"lat": float(crime.latitude), "lng": float(crime.longitude)},
        amount=float(crime.amount),
    )
