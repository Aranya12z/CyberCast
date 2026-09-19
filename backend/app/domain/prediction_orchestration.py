"""
app/domain/prediction_orchestration.py — Synchronous prediction orchestration pipeline.

Layer: L3 (Domain/Intelligence)
Architecture reference: ARCHITECTURE.md §6 (Synchronous MVP 8-step flow)
Contracts: ML_GIS_CONTRACTS.md, API_SPEC.md §/api/predictions/*, DATA_SCHEMA.md
"""
from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.alert_generation import evaluate_and_generate_alerts
from app.interfaces.model_interface import ModelInterface
from app.interfaces.spatial_interface import SpatialService, get_spatial_service
from ml import inference as ml_inference
from app.models.atm import ATM
from app.models.audit_log import AuditLog
from app.models.crime import Crime
from app.models.model_metadata import ModelMetadata
from app.models.prediction import Prediction, PredictionFeature, PredictionResult
from app.models.transaction import Transaction


def ensure_model_metadata(db: Session, model_version: str) -> None:
    """Ensure a row exists in model_metadata for foreign key integrity."""
    meta = db.get(ModelMetadata, model_version)
    if not meta:
        meta = ModelMetadata(
            model_version=model_version,
            trained_at=datetime.now(timezone.utc),
            algorithm="random_forest",
            eval_metrics={"status": "mvp_scaffold"},
        )
        db.add(meta)
        db.flush()


def run_prediction_pipeline(
    db: Session,
    crime_id: uuid.UUID,
    model: Optional[ModelInterface] = None,
    spatial_svc: Optional[SpatialService] = None,
    user_id: Optional[uuid.UUID] = None,
    search_radius_km: float = 5.0,
) -> Dict[str, Any]:
    """
    Executes the 8-step synchronous prediction flow per ARCHITECTURE.md §6.
    
    1. Retrieve complaint from DB
    2. Retrieve relevant ATM data from DB
    3. Retrieve candidate ATMs via SpatialInterface
    4. Generate spatial features & attach stored historical risk
    5. Retrieve relevant recent transactions
    6. Call ModelInterface.predict(payload)
    7. Persist prediction run, Top-K results, feature explanations, and generate alerts
    8. Return response shaped per API_SPEC.md
    """
    if model is None:
        # [IMPLEMENTED] Real ML inference — loads ml/models/latest.pkl via ml.inference.ModelInterface.
        # k=5 mirrors the Top-K contract; confidence_floor=0.35 per ML_SPEC.md §Confidence.
        model = ml_inference.ModelInterface(k=5)
    if spatial_svc is None:
        spatial_svc = get_spatial_service()

    # Step 1: Retrieve complaint
    crime = db.get(Crime, crime_id)
    if not crime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crime incident not found with id '{crime_id}'",
        )

    crime_loc = {"lat": float(crime.latitude), "lng": float(crime.longitude)}
    now_utc = datetime.now(timezone.utc)
    model_version = getattr(model, "model_version", "rf_v1.0.0")
    ensure_model_metadata(db, model_version)

    # Step 2: Retrieve all ATMs
    db_atms = db.query(ATM).all()
    if not db_atms:
        # Edge case (ARCHITECTURE.md §10): No ATMs in database
        prediction_run = Prediction(
            prediction_id=uuid.uuid4(),
            crime_id=crime.crime_id,
            generated_at=now_utc,
            model_version=model_version,
            status="insufficient_evidence",
        )
        db.add(prediction_run)
        db.commit()
        return {
            "crime_id": str(crime.crime_id),
            "generated_at": now_utc.isoformat(),
            "model_version": model_version,
            "predictions": [],
            "status": "insufficient_evidence",
        }

    atms_payload = [
        {
            "atm_id": str(atm.atm_id),
            "latitude": float(atm.latitude),
            "longitude": float(atm.longitude),
            "bank": atm.bank,
            "area": atm.area,
            "historical_risk_score": float(atm.historical_risk_score),
        }
        for atm in db_atms
    ]
    atm_map = {str(atm.atm_id): atm for atm in db_atms}

    # Step 3: Spatial filtering (Candidate selection)
    candidate_atms_raw = spatial_svc.get_candidate_atms(
        crime_location=crime_loc,
        radius_km=search_radius_km,
        atms=atms_payload,
    )

    if not candidate_atms_raw:
        # Edge case: No nearby ATM within radius -> honest status per ARCHITECTURE.md §10
        prediction_run = Prediction(
            prediction_id=uuid.uuid4(),
            crime_id=crime.crime_id,
            generated_at=now_utc,
            model_version=model_version,
            status="insufficient_evidence",
        )
        db.add(prediction_run)
        db.commit()
        return {
            "crime_id": str(crime.crime_id),
            "generated_at": now_utc.isoformat(),
            "model_version": model_version,
            "predictions": [],
            "status": "insufficient_evidence",
        }

    # Step 4: Spatial feature generation
    historical_crimes = [
        {"latitude": float(c.latitude), "longitude": float(c.longitude)}
        for c in db.query(Crime).filter(Crime.crime_id != crime.crime_id).limit(200).all()
    ]

    candidate_atms_input: List[Dict[str, Any]] = []
    candidate_atm_uuids = []

    for c_raw in candidate_atms_raw:
        c_atm_id = str(c_raw.get("atm_id"))
        orig_atm = atm_map.get(c_atm_id)
        if not orig_atm:
            continue

        atm_loc = {"lat": float(orig_atm.latitude), "lng": float(orig_atm.longitude)}
        spatial_features = spatial_svc.compute_spatial_features(
            crime_location=crime_loc,
            atm_location=atm_loc,
            historical_crimes=historical_crimes,
        )

        candidate_atms_input.append({
            "atm_id": c_atm_id,
            "location": atm_loc,
            "atm_historical_risk": float(orig_atm.historical_risk_score),
            "spatial_features": spatial_features,
        })
        candidate_atm_uuids.append(orig_atm.atm_id)

    # Step 5: Retrieve relevant recent transactions
    raw_txns = (
        db.query(Transaction)
        .filter(Transaction.atm_id.in_(candidate_atm_uuids))
        .all()
    )
    recent_transactions = [
        {
            "atm_id": str(tx.atm_id),
            "timestamp": tx.timestamp.isoformat(),
            "amount": float(tx.amount),
        }
        for tx in raw_txns
    ]

    # Step 6: Call ModelInterface.predict()
    ml_payload = {
        "crime": {
            "crime_id": str(crime.crime_id),
            "crime_type": crime.crime_type,
            "timestamp": crime.timestamp.isoformat(),
            "location": crime_loc,
            "amount": float(crime.amount),
        },
        "candidate_atms": candidate_atms_input,
        "recent_transactions": recent_transactions,
    }

    ml_output = model.predict(ml_payload)
    output_status = ml_output.get("status", "ok")
    output_predictions = ml_output.get("predictions", [])
    output_model_version = ml_output.get("model_version", model_version)

    # Step 7: Persist predictions & results
    prediction_record = Prediction(
        prediction_id=uuid.uuid4(),
        crime_id=crime.crime_id,
        generated_at=now_utc,
        model_version=output_model_version,
        status=output_status,
    )
    db.add(prediction_record)
    db.flush()

    saved_results: List[PredictionResult] = []

    if output_status == "ok":
        for pred_item in output_predictions:
            pred_atm_id = uuid.UUID(str(pred_item["atm_id"]))
            win = pred_item.get("predicted_window", {})
            start_dt = datetime.fromisoformat(str(win.get("start")).replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(str(win.get("end")).replace("Z", "+00:00"))

            result_row = PredictionResult(
                result_id=uuid.uuid4(),
                prediction_id=prediction_record.prediction_id,
                atm_id=pred_atm_id,
                risk_score=float(pred_item["risk_score"]),
                confidence=float(pred_item["confidence"]),
                predicted_window_start=start_dt,
                predicted_window_end=end_dt,
            )
            db.add(result_row)
            db.flush()
            saved_results.append(result_row)

            # Persist explanations (FK -> prediction_results.result_id)
            for exp in pred_item.get("explanation", []):
                feature_row = PredictionFeature(
                    feature_id=uuid.uuid4(),
                    result_id=result_row.result_id,
                    feature_name=str(exp["feature"]),
                    feature_value=float(exp["value"]),
                    contribution=str(exp["contribution"]),
                )
                db.add(feature_row)

        # Generate alerts per ADR-006
        evaluate_and_generate_alerts(
            db=db,
            prediction=prediction_record,
            results=saved_results,
            user_id=user_id,
        )

    # Record Audit Log
    audit_entry = AuditLog(
        user_id=user_id,
        action="prediction_generated",
        timestamp=now_utc,
        resource=f"prediction:{prediction_record.prediction_id}",
        metadata_={
            "crime_id": str(crime.crime_id),
            "status": output_status,
            "candidates_evaluated": len(candidate_atms_input),
            "results_count": len(saved_results),
        },
    )
    db.add(audit_entry)
    db.commit()

    # Step 8: Return API_SPEC.md response shape
    return {
        "crime_id": str(crime.crime_id),
        "generated_at": now_utc.isoformat(),
        "model_version": output_model_version,
        "predictions": output_predictions,
        "status": output_status,
    }


def get_latest_prediction_for_crime(
    db: Session,
    crime_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent prediction run for a crime."""
    prediction = (
        db.query(Prediction)
        .filter(Prediction.crime_id == crime_id)
        .order_by(Prediction.generated_at.desc())
        .first()
    )
    if not prediction:
        return None

    # Build atm_id → ATM lookup so we can attach bank/area/location
    # without a per-result query. Mirrors the atm_map pattern in run_prediction_pipeline.
    atm_ids = [res.atm_id for res in prediction.results]
    atms_for_results = db.query(ATM).filter(ATM.atm_id.in_(atm_ids)).all()
    atm_lookup = {atm.atm_id: atm for atm in atms_for_results}

    results_data = []
    for res in prediction.results:
        exps = [
            {
                "feature": feat.feature_name,
                "value": float(feat.feature_value),
                "contribution": feat.contribution,
            }
            for feat in res.features
        ]
        atm = atm_lookup.get(res.atm_id)
        results_data.append({
            "atm_id": str(res.atm_id),
            "bank": atm.bank if atm else None,
            "area": atm.area if atm else None,
            "location": (
                {"lat": float(atm.latitude), "lng": float(atm.longitude)}
                if atm else None
            ),
            "risk_score": float(res.risk_score),
            "confidence": float(res.confidence),
            "predicted_window": {
                "start": res.predicted_window_start.isoformat(),
                "end": res.predicted_window_end.isoformat(),
            },
            "explanation": exps,
        })

    # Sort results by risk_score descending
    results_data.sort(key=lambda x: x["risk_score"], reverse=True)

    return {
        "crime_id": str(prediction.crime_id),
        "generated_at": prediction.generated_at.isoformat(),
        "model_version": prediction.model_version,
        "predictions": results_data,
        "status": prediction.status,
    }
