"""
app/domain/complaint_processing.py — Crime intake, validation, and retrieval.

Layer: L3 (Domain/Intelligence)
References:
  API_SPEC.md §/api/crimes/*
  DATA_SCHEMA.md §crimes
  ARCHITECTURE.md §10 (Failure & Edge-Case Handling)
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.crime import Crime
from app.schemas.crime import CrimeCreate


def create_complaint(
    db: Session,
    crime_in: CrimeCreate,
    user_id: Optional[uuid.UUID] = None,
) -> Crime:
    """
    Ingest and validate a new crime complaint.
    
    Edge-case checks (ARCHITECTURE.md §10):
      - Valid coordinates (lat in [-90, 90], lng in [-180, 180])
      - Positive amount (>= 0)
      - Duplicate complaint prevention
    """
    lat = float(crime_in.location.lat)
    lng = float(crime_in.location.lng)

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid coordinates: lat={lat}, lng={lng}. Must be valid WGS84 coordinates.",
        )

    if crime_in.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Crime amount cannot be negative.",
        )

    # Check for duplicate complaint (same type, location, amount, within 5 minutes)
    existing = (
        db.query(Crime)
        .filter(
            Crime.crime_type == crime_in.crime_type,
            Crime.latitude == lat,
            Crime.longitude == lng,
            Crime.amount == crime_in.amount,
        )
        .first()
    )
    if existing:
        ts1 = existing.timestamp if existing.timestamp.tzinfo else existing.timestamp.replace(tzinfo=timezone.utc)
        ts2 = crime_in.timestamp if crime_in.timestamp.tzinfo else crime_in.timestamp.replace(tzinfo=timezone.utc)
        time_diff = abs((ts1 - ts2).total_seconds())
        if time_diff < 300:  # within 5 minutes
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate complaint detected: matching incident already exists (crime_id={existing.crime_id}).",
            )

    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type=crime_in.crime_type,
        timestamp=crime_in.timestamp,
        latitude=lat,
        longitude=lng,
        amount=crime_in.amount,
    )
    db.add(crime)

    # Record audit log
    audit_entry = AuditLog(
        user_id=user_id,
        action="complaint_created",
        timestamp=datetime.now(timezone.utc),
        resource=f"crime:{crime.crime_id}",
        metadata_={"crime_type": crime.crime_type, "amount": float(crime.amount)},
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(crime)
    return crime


def get_complaint(db: Session, crime_id: uuid.UUID) -> Crime:
    """Retrieve a single crime complaint by UUID. Raises 404 if not found."""
    crime = db.get(Crime, crime_id)
    if not crime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crime incident not found with id '{crime_id}'",
        )
    return crime


def list_complaints(
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> List[Crime]:
    """List recent crime complaints ordered by timestamp descending."""
    return (
        db.query(Crime)
        .order_by(Crime.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
