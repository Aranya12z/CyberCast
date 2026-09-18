"""
app/domain/alert_generation.py — Alert generation, lifecycle, and retrieval.

Layer: L3 (Domain/Intelligence)
Rule: ADRS.md ADR-006 (Alert Generation Thresholds & Deduplication)
  - risk_score >= 0.7 AND confidence >= 0.5 → severity: high
  - 0.4 <= risk_score < 0.7 AND confidence >= 0.5 → severity: medium
  - anything else → no alert created
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.prediction import Prediction, PredictionResult


def evaluate_and_generate_alerts(
    db: Session,
    prediction: Prediction,
    results: List[PredictionResult],
    user_id: Optional[uuid.UUID] = None,
) -> List[Alert]:
    """
    Applies the ADR-006 threshold to already-scored prediction results.
    Creates, deduplicates, and persists Alert rows.
    """
    generated_alerts: List[Alert] = []

    for res in results:
        risk = float(res.risk_score)
        conf = float(res.confidence)

        # ADR-006 Threshold Check
        severity: Optional[str] = None
        if conf >= 0.5:
            if risk >= 0.7:
                severity = "high"
            elif risk >= 0.4:
                severity = "medium"

        if severity is None:
            continue

        # Deduplication check: do not recreate active alert for same prediction & ATM
        existing_alert = (
            db.query(Alert)
            .filter(
                Alert.prediction_id == prediction.prediction_id,
                Alert.atm_id == res.atm_id,
            )
            .first()
        )
        if existing_alert:
            continue

        alert = Alert(
            alert_id=uuid.uuid4(),
            prediction_id=prediction.prediction_id,
            atm_id=res.atm_id,
            severity=severity,
            created_at=datetime.now(timezone.utc),
            status="new",
            channel="dashboard",
        )
        db.add(alert)
        generated_alerts.append(alert)

        # Write audit log per alert
        audit_entry = AuditLog(
            user_id=user_id,
            action="alert_created",
            timestamp=datetime.now(timezone.utc),
            resource=f"alert:{alert.alert_id}",
            metadata_={
                "prediction_id": str(prediction.prediction_id),
                "atm_id": str(res.atm_id),
                "severity": severity,
                "risk_score": risk,
                "confidence": conf,
            },
        )
        db.add(audit_entry)

    if generated_alerts:
        db.flush()

    return generated_alerts


def list_alerts(
    db: Session,
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Alert]:
    """List alerts with optional severity/status filters."""
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


def acknowledge_alert(
    db: Session,
    alert_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> Alert:
    """Acknowledge an alert and record audit log."""
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert not found with id '{alert_id}'",
        )

    alert.status = "acknowledged"
    audit_entry = AuditLog(
        user_id=user_id,
        action="alert_acknowledged",
        timestamp=datetime.now(timezone.utc),
        resource=f"alert:{alert.alert_id}",
        metadata_={"status": "acknowledged"},
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(alert)
    return alert
