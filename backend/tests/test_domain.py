"""
backend/tests/test_domain.py — Tests for domain orchestration, complaint processing,
prediction pipeline (ARCHITECTURE.md §6), ADR-006 alert generation, and intelligence assembly.
"""
from datetime import datetime, timezone
import uuid
from pydantic import ValidationError
import pytest
from fastapi import HTTPException

from app.domain.alert_generation import (
    acknowledge_alert,
    evaluate_and_generate_alerts,
    list_alerts,
)
from app.domain.complaint_processing import (
    create_complaint,
    get_complaint,
    list_complaints,
)
from app.domain.intelligence_generation import generate_intelligence_report
from app.domain.prediction_orchestration import (
    get_latest_prediction_for_crime,
    run_prediction_pipeline,
)
from app.interfaces.model_interface import MockModelInterface
from app.models.alert import Alert
from app.models.atm import ATM
from app.models.crime import Crime
from app.models.prediction import Prediction, PredictionResult
from app.models.transaction import Transaction
from app.schemas.common import LocationSchema
from app.schemas.crime import CrimeCreate


def test_complaint_intake_and_validation(db_session):
    """Test valid crime complaint creation and invalid edge-case rejection."""
    valid_payload = CrimeCreate(
        crime_type="phishing",
        timestamp=datetime.now(timezone.utc),
        location=LocationSchema(lat=12.9716, lng=77.5946),
        amount=50000.0,
    )
    crime = create_complaint(db_session, valid_payload)
    assert crime.crime_id is not None
    assert crime.crime_type == "phishing"
    assert float(crime.amount) == 50000.0

    # Negative amount rejection (Pydantic schema level)
    with pytest.raises(ValidationError):
        CrimeCreate(
            crime_type="fraud",
            timestamp=datetime.now(timezone.utc),
            location=LocationSchema(lat=12.9716, lng=77.5946),
            amount=-100.0,
        )

    # Invalid coordinates rejection (Domain validation level)
    with pytest.raises(HTTPException) as exc:
        create_complaint(
            db_session,
            CrimeCreate(
                crime_type="fraud",
                timestamp=datetime.now(timezone.utc),
                location=LocationSchema(lat=95.0, lng=77.5946),
                amount=1000.0,
            ),
        )
    assert exc.value.status_code == 422

    # Duplicate complaint rejection
    with pytest.raises(HTTPException) as exc:
        create_complaint(db_session, valid_payload)
    assert exc.value.status_code == 409


def test_prediction_pipeline_end_to_end(db_session):
    """Test the full 8-step synchronous prediction orchestration flow (ARCHITECTURE.md §6)."""
    now = datetime.now(timezone.utc)

    # 1. Create ATM co-located with crime for maximum distance_from_crime signal.
    # historical_risk_score=0.90 and 8 txns within 1h produce real model:
    #   risk_score ~0.42, confidence ~0.85 -> ADR-006 alert threshold (>=0.4, >=0.5) met.
    atm = ATM(
        atm_id=uuid.uuid4(),
        latitude=12.9716,
        longitude=77.5946,
        bank="SBI",
        area="MG Road",
        historical_risk_score=0.90,
    )
    db_session.add(atm)

    # 8 transactions within the 1h window before crime time
    from datetime import timedelta
    for i in range(8):
        db_session.add(Transaction(
            transaction_id=uuid.uuid4(),
            atm_id=atm.atm_id,
            timestamp=now - timedelta(minutes=5 * i),
            amount=15000.0,
            account_id=f"ACC-{i:03d}",
        ))

    # 3. Create Crime at same coords
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type="atm_fraud",
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
        amount=80000.0,
    )
    db_session.add(crime)
    db_session.commit()

    # Run Prediction Pipeline
    response = run_prediction_pipeline(
        db=db_session,
        crime_id=crime.crime_id,
        search_radius_km=5.0,
    )

    assert response["status"] == "ok"
    assert response["crime_id"] == str(crime.crime_id)
    assert len(response["predictions"]) == 1

    pred = response["predictions"][0]
    assert pred["atm_id"] == str(atm.atm_id)
    assert pred["risk_score"] > 0.0
    assert pred["confidence"] >= 0.35
    assert len(pred["explanation"]) > 0

    # Verify DB persistence of Prediction, PredictionResult, PredictionFeature
    persisted_run = (
        db_session.query(Prediction)
        .filter(Prediction.crime_id == crime.crime_id)
        .first()
    )
    assert persisted_run is not None
    assert len(persisted_run.results) == 1
    assert len(persisted_run.results[0].features) > 0

    # Verify Alert was generated per ADR-006 (since risk > 0.4 and conf >= 0.5)
    alerts = db_session.query(Alert).filter(Alert.prediction_id == persisted_run.prediction_id).all()
    assert len(alerts) >= 1

    # Verify retrieval via get_latest_prediction_for_crime
    latest = get_latest_prediction_for_crime(db_session, crime.crime_id)
    assert latest is not None
    assert latest["crime_id"] == str(crime.crime_id)
    assert latest["status"] == "ok"


def test_prediction_edge_case_no_nearby_atm(db_session):
    """Verify that when no ATMs are nearby, pipeline returns insufficient_evidence without fabricating."""
    now = datetime.now(timezone.utc)
    # ATM far away (Delhi)
    atm_far = ATM(
        atm_id=uuid.uuid4(),
        latitude=28.6139,
        longitude=77.2090,
        bank="HDFC",
        area="Connaught Place",
        historical_risk_score=0.10,
    )
    db_session.add(atm_far)

    # Crime in Bengaluru
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type="vishing",
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
        amount=20000.0,
    )
    db_session.add(crime)
    db_session.commit()

    response = run_prediction_pipeline(
        db=db_session,
        crime_id=crime.crime_id,
        search_radius_km=5.0,  # 5km search radius -> no ATMs found
    )
    assert response["status"] == "insufficient_evidence"
    assert response["predictions"] == []


def test_alert_generation_adr006_thresholds(db_session):
    """Test ADR-006 threshold matrix for alert creation."""
    now = datetime.now(timezone.utc)
    atm = ATM(
        atm_id=uuid.uuid4(),
        latitude=12.9716,
        longitude=77.5946,
        bank="ICICI",
        area="Indiranagar",
        historical_risk_score=0.5,
    )
    db_session.add(atm)
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type="fraud",
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
        amount=10000.0,
    )
    db_session.add(crime)
    pred_run = Prediction(
        prediction_id=uuid.uuid4(),
        crime_id=crime.crime_id,
        generated_at=now,
        model_version="test_v1",
        status="ok",
    )
    db_session.add(pred_run)
    db_session.commit()

    # Case 1: High severity (risk >= 0.7, conf >= 0.5)
    res_high = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred_run.prediction_id,
        atm_id=atm.atm_id,
        risk_score=0.80,
        confidence=0.70,
        predicted_window_start=now,
        predicted_window_end=now,
    )
    alerts = evaluate_and_generate_alerts(db_session, pred_run, [res_high])
    assert len(alerts) == 1
    assert alerts[0].severity == "high"

    # Case 2: Low confidence (< 0.5) -> No alert even if high risk
    res_low_conf = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred_run.prediction_id,
        atm_id=uuid.uuid4(),
        risk_score=0.90,
        confidence=0.40,
        predicted_window_start=now,
        predicted_window_end=now,
    )
    alerts2 = evaluate_and_generate_alerts(db_session, pred_run, [res_low_conf])
    assert len(alerts2) == 0

    # Case 3: Medium severity (0.4 <= risk < 0.7, conf >= 0.5)
    res_med = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred_run.prediction_id,
        atm_id=uuid.uuid4(),
        risk_score=0.55,
        confidence=0.60,
        predicted_window_start=now,
        predicted_window_end=now,
    )
    alerts3 = evaluate_and_generate_alerts(db_session, pred_run, [res_med])
    assert len(alerts3) == 1
    assert alerts3[0].severity == "medium"


def test_intelligence_report_assembly(db_session):
    """Test /api/intelligence/{crime_id} assembly matching API_SPEC.md."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    # ATM co-located with crime (distance_from_crime ~0), historical_risk_score=0.90,
    # 8 txns within 1h -> real model: risk_score ~0.42, confidence ~0.85 -> alert triggered.
    atm = ATM(
        atm_id=uuid.uuid4(),
        latitude=12.9716,
        longitude=77.5946,
        bank="Canara Bank",
        area="Koramangala",
        historical_risk_score=0.90,
    )
    db_session.add(atm)
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type="identity_theft",
        timestamp=now,
        latitude=12.9716,
        longitude=77.5946,
        amount=120000.0,
    )
    db_session.add(crime)
    for i in range(8):
        db_session.add(Transaction(
            transaction_id=uuid.uuid4(),
            atm_id=atm.atm_id,
            timestamp=now - timedelta(minutes=5 * i),
            amount=20000.0,
            account_id=f"ACC-INTEL-{i:03d}",
        ))
    db_session.commit()

    # Run prediction
    run_prediction_pipeline(db_session, crime.crime_id)

    # Generate intelligence report
    intel = generate_intelligence_report(db_session, crime.crime_id)

    assert intel["crime_id"] == str(crime.crime_id)
    assert intel["crime"]["crime_type"] == "identity_theft"
    assert intel["latest_prediction"]["status"] == "ok"
    assert intel["latest_prediction"]["top_result"]["atm_id"] == str(atm.atm_id)
    assert len(intel["evidence"]) > 0
    assert len(intel["related_alerts"]) > 0
    assert "summary" in intel
    assert len(intel["summary"]) > 0
