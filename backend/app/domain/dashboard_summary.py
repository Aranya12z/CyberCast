"""
app/domain/dashboard_summary.py — Aggregates real operational metrics for the dashboard.

Layer: L3 (Domain/Intelligence)
Reference: API_SPEC.md §/api/dashboard/*
"""
from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.prediction import Prediction, PredictionResult


def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    """
    Computes real aggregate metrics across predictions, alerts, and audit logs.
    No new business logic — simple SQL aggregations per BACKEND_SPEC.md §dashboard.
    """
    # 1. Active alerts count (status == 'new')
    active_alerts = db.query(func.count(Alert.alert_id)).filter(Alert.status == "new").scalar() or 0

    # 2. High risk predictions count (risk_score >= 0.7)
    high_risk_predictions = (
        db.query(func.count(PredictionResult.result_id))
        .filter(PredictionResult.risk_score >= 0.7)
        .scalar()
        or 0
    )

    # 3. Prediction stats
    total_runs = db.query(func.count(Prediction.prediction_id)).scalar() or 0
    avg_conf = db.query(func.avg(PredictionResult.confidence)).scalar() or 0.0
    insufficient_count = (
        db.query(func.count(Prediction.prediction_id))
        .filter(Prediction.status == "insufficient_evidence")
        .scalar()
        or 0
    )
    insufficient_rate = round(float(insufficient_count) / float(total_runs), 2) if total_runs > 0 else 0.0

    prediction_stats = {
        "total_predictions_run": int(total_runs),
        "avg_confidence": round(float(avg_conf), 2),
        "insufficient_evidence_rate": insufficient_rate,
    }

    # 4. Recent activity from audit_logs
    recent_logs = (
        db.query(AuditLog)
        .filter(AuditLog.action.in_(["prediction_generated", "alert_created", "alert_acknowledged"]))
        .order_by(AuditLog.timestamp.desc())
        .limit(10)
        .all()
    )

    activity_items: List[Dict[str, Any]] = []
    for log in recent_logs:
        meta = log.metadata_ or {}
        crime_id = meta.get("crime_id")
        if not crime_id and log.resource and log.resource.startswith("crime:"):
            crime_id = log.resource.split("crime:")[1]

        # Template summary description
        if log.action == "prediction_generated":
            summary = f"Prediction run completed. {meta.get('candidates_evaluated', 0)} candidate ATMs evaluated."
        elif log.action == "alert_created":
            summary = f"{str(meta.get('severity', 'Risk')).capitalize()} risk alert generated for candidate ATM {meta.get('atm_id', '')}."
        elif log.action == "alert_acknowledged":
            summary = f"Alert {log.resource} acknowledged by operator."
        else:
            summary = f"System event '{log.action}' recorded."

        activity_items.append({
            "type": log.action,
            "timestamp": log.timestamp.isoformat(),
            "crime_id": str(crime_id) if crime_id else None,
            "summary": summary,
        })

    return {
        "active_alerts": int(active_alerts),
        "high_risk_predictions": int(high_risk_predictions),
        "prediction_stats": prediction_stats,
        "recent_activity": activity_items,
    }
