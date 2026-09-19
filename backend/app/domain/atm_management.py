"""
app/domain/atm_management.py — ATM resource management and GeoJSON generation.

Layer: L3 (Domain/Intelligence)
Reference: API_SPEC.md §/api/atms/*, ML_GIS_CONTRACTS.md §2
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.interfaces.spatial_interface import SpatialService, get_spatial_service
from app.models.atm import ATM
from app.models.prediction import Prediction, PredictionResult


def list_atms(
    db: Session,
    limit: int = 100,
    offset: int = 0,
) -> List[ATM]:
    """List ATMs with pagination."""
    return db.query(ATM).offset(offset).limit(limit).all()


def get_atm(db: Session, atm_id: uuid.UUID) -> ATM:
    """Retrieve ATM by UUID. Raises 404 if not found."""
    atm = db.get(ATM, atm_id)
    if not atm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ATM not found with id '{atm_id}'",
        )
    return atm


def get_atms_geojson(
    db: Session,
    spatial_svc: Optional[SpatialService] = None,
) -> Dict[str, Any]:
    """
    Builds the GeoJSON FeatureCollection for all ATMs conforming strictly to ML_GIS_CONTRACTS.md §2.
    Merges recent prediction scores if available.
    """
    if spatial_svc is None:
        spatial_svc = get_spatial_service()

    atms = db.query(ATM).all()
    if not atms:
        return {"type": "FeatureCollection", "features": []}

    # Fetch latest prediction results for all ATMs to show live risk
    latest_results = (
        db.query(PredictionResult)
        .order_by(PredictionResult.predicted_window_start.desc())
        .all()
    )
    atm_prediction_map: Dict[uuid.UUID, PredictionResult] = {}
    for res in latest_results:
        if res.atm_id not in atm_prediction_map:
            atm_prediction_map[res.atm_id] = res

    features_input = []
    for atm in atms:
        res = atm_prediction_map.get(atm.atm_id)
        if res:
            risk_score = float(res.risk_score)
            confidence = float(res.confidence)
            win = {
                "start": res.predicted_window_start.isoformat(),
                "end": res.predicted_window_end.isoformat(),
            }
            exps = [
                f"{feat.feature_name.replace('_', ' ').title()} ({float(feat.feature_value)}) - {feat.contribution} impact"
                for feat in res.features
            ]
        else:
            # Baseline stored historical score
            risk_score = float(atm.historical_risk_score)
            confidence = 0.50
            win = None
            exps = [f"Historical baseline risk: {risk_score:.2f}"]

        features_input.append({
            "atm_id": str(atm.atm_id),
            "bank": atm.bank,
            "area": atm.area,
            "location": {"lat": float(atm.latitude), "lng": float(atm.longitude)},
            "risk_score": risk_score,
            "confidence": confidence,
            "predicted_window": win,
            "explanation": exps,
        })

    return spatial_svc.to_geojson(features_input)
