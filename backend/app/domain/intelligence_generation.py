"""
app/domain/intelligence_generation.py — Assembles intelligence reports.

Layer: L3 (Domain/Intelligence)
Reference: API_SPEC.md §/api/intelligence/*
Architecture: ARCHITECTURE.md §8 (Auditability)
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.atm import ATM
from app.models.audit_log import AuditLog
from app.models.crime import Crime
from app.models.prediction import Prediction, PredictionResult


def generate_intelligence_report(
    db: Session,
    crime_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Assembles the complete intelligence payload for a crime incident.
    Joins crime details, latest prediction run, winning candidate features (evidence),
    related alerts, and generates human-readable operational summary.
    """
    crime = db.get(Crime, crime_id)
    if not crime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crime incident not found with id '{crime_id}'",
        )

    crime_dict = {
        "crime_id": str(crime.crime_id),
        "crime_type": crime.crime_type,
        "timestamp": crime.timestamp.isoformat(),
        "location": {
            "lat": float(crime.latitude),
            "lng": float(crime.longitude),
        },
        "amount": float(crime.amount),
    }

    # Fetch most recent prediction run
    prediction = (
        db.query(Prediction)
        .filter(Prediction.crime_id == crime_id)
        .order_by(Prediction.generated_at.desc())
        .first()
    )

    latest_prediction_dict: Optional[Dict[str, Any]] = None
    evidence_list = []
    top_atm = None

    if prediction:
        top_result = (
            db.query(PredictionResult)
            .filter(PredictionResult.prediction_id == prediction.prediction_id)
            .order_by(PredictionResult.risk_score.desc())
            .first()
        )

        top_result_dict = None
        if top_result:
            top_atm = db.get(ATM, top_result.atm_id)
            top_result_dict = {
                "atm_id": str(top_result.atm_id),
                "risk_score": float(top_result.risk_score),
                "confidence": float(top_result.confidence),
                "predicted_window": {
                    "start": top_result.predicted_window_start.isoformat(),
                    "end": top_result.predicted_window_end.isoformat(),
                },
            }
            # Evidence is the winning candidate's prediction_features rows
            evidence_list = [
                {
                    "feature": feat.feature_name,
                    "value": float(feat.feature_value),
                    "contribution": feat.contribution,
                }
                for feat in top_result.features
            ]

        latest_prediction_dict = {
            "generated_at": prediction.generated_at.isoformat(),
            "model_version": prediction.model_version,
            "status": prediction.status,
            "top_result": top_result_dict,
        }

    # Related alerts for this crime
    alerts = (
        db.query(Alert)
        .join(Prediction, Alert.prediction_id == Prediction.prediction_id)
        .filter(Prediction.crime_id == crime_id)
        .order_by(Alert.created_at.desc())
        .all()
    )
    related_alerts = [
        {
            "alert_id": str(al.alert_id),
            "severity": al.severity,
            "status": al.status,
        }
        for al in alerts
    ]

    # Template-generated human-readable summary (API_SPEC.md note)
    if prediction and prediction.status == "ok" and latest_prediction_dict.get("top_result"):
        top_res = latest_prediction_dict["top_result"]
        atm_desc = f" ({top_atm.bank}, {top_atm.area})" if top_atm else ""
        summary_text = (
            f"Cash-out forecast: High-risk probability ({top_res['risk_score']:.1%}, "
            f"confidence {top_res['confidence']:.1%}) identified at candidate ATM "
            f"{top_res['atm_id']}{atm_desc} within 6-hour operational window."
        )
    elif prediction and prediction.status == "insufficient_confidence":
        summary_text = (
            "Predictive analysis completed with low model confidence (<35%). "
            "No high-confidence candidate ATM identified; exploratory surveillance recommended."
        )
    elif prediction and prediction.status == "insufficient_evidence":
        summary_text = (
            "Insufficient geospatial or transaction evidence within search radius. "
            "No nearby ATM matched the criteria for risk ranking."
        )
    else:
        summary_text = (
            f"Complaint registered for {crime.crime_type} (amount: INR {float(crime.amount):,.2f}). "
            "Awaiting predictive intelligence run."
        )

    # Record Audit Log
    audit_entry = AuditLog(
        user_id=user_id,
        action="intelligence_viewed",
        timestamp=datetime.now(timezone.utc),
        resource=f"crime:{crime.crime_id}",
        metadata_={"prediction_status": prediction.status if prediction else "none"},
    )
    db.add(audit_entry)
    db.commit()

    return {
        "crime_id": str(crime.crime_id),
        "crime": crime_dict,
        "latest_prediction": latest_prediction_dict,
        "evidence": evidence_list,
        "related_alerts": related_alerts,
        "summary": summary_text,
    }
