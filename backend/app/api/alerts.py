"""
app/api/alerts.py — Thin REST API router for alert listing and acknowledgement.

Layer: L2 (API/Application)
Reference: API_SPEC.md §/api/alerts/*
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role
from app.domain.alert_generation import acknowledge_alert, list_alerts
from app.models.atm import ATM
from app.models.user import User
from app.schemas.alert import AlertAcknowledgeResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse], summary="List and filter alerts")
def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: low | medium | high"),
    status: Optional[str] = Query(None, description="Filter by status: new | acknowledged | resolved"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("investigator", "bank_analyst", "administrator")),
    db: Session = Depends(get_db),
):
    """List alerts with optional severity and status filters."""
    alerts = list_alerts(db=db, severity=severity, status_filter=status, limit=limit, offset=offset)
    
    # Enrich with ATM metadata (bank/area) for frontend convenience
    atm_ids = [al.atm_id for al in alerts]
    atms = {a.atm_id: a for a in db.query(ATM).filter(ATM.atm_id.in_(atm_ids)).all()} if atm_ids else {}

    return [
        AlertResponse(
            alert_id=str(al.alert_id),
            crime_id=str(al.prediction.crime_id) if al.prediction else str(al.prediction_id),
            atm_id=str(al.atm_id),
            bank=atms[al.atm_id].bank if al.atm_id in atms else None,
            area=atms[al.atm_id].area if al.atm_id in atms else None,
            severity=al.severity,
            created_at=al.created_at,
            status=al.status,
            channel=al.channel,
        )
        for al in alerts
    ]


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertAcknowledgeResponse,
    summary="Acknowledge an alert",
)
def post_acknowledge_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_role("investigator", "administrator")),
    db: Session = Depends(get_db),
):
    """Acknowledge an alert."""
    alert = acknowledge_alert(db=db, alert_id=alert_id, user_id=current_user.user_id)
    return AlertAcknowledgeResponse(
        success=True,
        alert_id=str(alert.alert_id),
        status="acknowledged",
    )
