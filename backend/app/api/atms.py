"""
app/api/atms.py — Thin REST API router for ATM locations.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/atms/*, ML_GIS_CONTRACTS.md §2
"""
import uuid
from typing import Any, List, Optional, Union
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role
from app.domain.atm_management import get_atm, get_atms_geojson, list_atms
from app.models.user import User
from app.schemas.atm import ATMResponse, GeoJSONFeatureCollection

router = APIRouter(prefix="/atms", tags=["atms"])


@router.get(
    "",
    response_model=Union[List[ATMResponse], GeoJSONFeatureCollection],
    summary="List ATMs or retrieve GeoJSON FeatureCollection",
)
def get_atms(
    format: Optional[str] = Query(None, description="Set to 'geojson' for RFC 7946 FeatureCollection"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("investigator", "bank_analyst", "administrator")),
    db: Session = Depends(get_db),
):
    """
    List ATMs as JSON objects or as GeoJSON FeatureCollection when format=geojson.
    """
    if format == "geojson":
        return get_atms_geojson(db=db)

    atms = list_atms(db=db, limit=limit, offset=offset)
    return [
        ATMResponse(
            atm_id=str(a.atm_id),
            location={"lat": float(a.latitude), "lng": float(a.longitude)},
            bank=a.bank,
            area=a.area,
            historical_risk_score=float(a.historical_risk_score),
        )
        for a in atms
    ]


@router.get("/{atm_id}", response_model=ATMResponse, summary="Get ATM details")
def get_atm_by_id(
    atm_id: uuid.UUID,
    current_user: User = Depends(require_role("investigator", "bank_analyst", "administrator")),
    db: Session = Depends(get_db),
):
    """Retrieve details of a single ATM."""
    atm = get_atm(db=db, atm_id=atm_id)
    return ATMResponse(
        atm_id=str(atm.atm_id),
        location={"lat": float(atm.latitude), "lng": float(atm.longitude)},
        bank=atm.bank,
        area=atm.area,
        historical_risk_score=float(atm.historical_risk_score),
    )
