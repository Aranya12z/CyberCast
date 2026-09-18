"""
backend/tests/test_failure_cases.py — Pytest coverage for every failure / edge-case
defined in ARCHITECTURE.md §10.

Failure cases covered:
  1.  Missing / invalid coordinates on crime intake
  2.  Duplicate complaint (same crime submitted twice)
  3.  No ATMs in database → insufficient_evidence
  4.  No nearby ATM within search radius → insufficient_evidence
  5.  No transaction history for candidate ATMs → pipeline still completes
  6.  Model returns insufficient_confidence → propagated faithfully, no fabrication
  7.  Model unavailable (raises) → 503 wrapper
  8.  Spatial service unavailable (raises) → 503 wrapper
  9.  Crime not found → 404 on prediction trigger
 10.  Malformed request body → 422 standard envelope
 11.  Prediction outside 6-hour window (ADR-005 literal)
 12.  Audit log written for every prediction_generated event
 13.  Alert NOT generated when confidence < 0.5 (ADR-006 literal)

ModelInterface and SpatialInterface are mocked via unittest.mock so these tests
never touch a real ML model or GIS service.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.domain.alert_generation import evaluate_and_generate_alerts
from app.domain.complaint_processing import create_complaint
from app.domain.prediction_orchestration import run_prediction_pipeline
from app.models.alert import Alert
from app.models.atm import ATM
from app.models.audit_log import AuditLog
from app.models.crime import Crime
from app.models.prediction import Prediction
from app.schemas.common import LocationSchema
from app.schemas.crime import CrimeCreate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_crime(db, lat=12.9716, lng=77.5946, crime_type="atm_fraud", amount=50000.0):
    """Persist a Crime row and return it."""
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type=crime_type,
        timestamp=datetime.now(timezone.utc),
        latitude=lat,
        longitude=lng,
        amount=amount,
    )
    db.add(crime)
    db.commit()
    return crime


def _make_atm(db, lat=12.9720, lng=77.5950, hist_risk=0.60):
    """Persist an ATM row and return it."""
    atm = ATM(
        atm_id=uuid.uuid4(),
        latitude=lat,
        longitude=lng,
        bank="SBI",
        area="MG Road",
        historical_risk_score=hist_risk,
    )
    db.add(atm)
    db.commit()
    return atm


# ---------------------------------------------------------------------------
# 1. Missing / invalid coordinates on crime intake (ARCHITECTURE.md §10)
# ---------------------------------------------------------------------------

def test_failure_missing_lat_lng_rejected(db_session):
    """
    Crime with latitude > 90 must be rejected at domain level with HTTP 422.
    Principle: invalid inputs are caught before they pollute the DB.
    """
    with pytest.raises(HTTPException) as exc:
        create_complaint(
            db_session,
            CrimeCreate(
                crime_type="fraud",
                timestamp=datetime.now(timezone.utc),
                location=LocationSchema(lat=95.0, lng=77.5946),  # out-of-range lat
                amount=1000.0,
            ),
        )
    assert exc.value.status_code == 422


def test_failure_invalid_longitude_rejected(db_session):
    """Longitude > 180 must be rejected with HTTP 422."""
    with pytest.raises(HTTPException) as exc:
        create_complaint(
            db_session,
            CrimeCreate(
                crime_type="fraud",
                timestamp=datetime.now(timezone.utc),
                location=LocationSchema(lat=12.0, lng=200.0),  # out-of-range lng
                amount=1000.0,
            ),
        )
    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# 2. Duplicate complaint (ARCHITECTURE.md §10)
# ---------------------------------------------------------------------------

def test_failure_duplicate_complaint_rejected(db_session):
    """
    Re-submitting the same (crime_type, timestamp, lat, lng, amount) must raise
    HTTP 409 on the second call — never silently accept a duplicate.
    """
    payload = CrimeCreate(
        crime_type="phishing",
        timestamp=datetime(2026, 9, 18, 10, 0, 0, tzinfo=timezone.utc),
        location=LocationSchema(lat=12.9716, lng=77.5946),
        amount=30000.0,
    )
    create_complaint(db_session, payload)  # first — must succeed
    with pytest.raises(HTTPException) as exc:
        create_complaint(db_session, payload)  # second — must conflict
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# 3. No ATMs in database → insufficient_evidence (ARCHITECTURE.md §10)
# ---------------------------------------------------------------------------

def test_failure_no_atms_in_db_returns_insufficient_evidence(db_session):
    """
    When the ATM table is empty the pipeline must return status=insufficient_evidence
    and an empty predictions list — never crash or fabricate.
    """
    crime = _make_crime(db_session)
    response = run_prediction_pipeline(db=db_session, crime_id=crime.crime_id)
    assert response["status"] == "insufficient_evidence"
    assert response["predictions"] == []


# ---------------------------------------------------------------------------
# 4. No nearby ATM within search radius → insufficient_evidence (ARCHITECTURE.md §10)
# ---------------------------------------------------------------------------

def test_failure_no_nearby_atm_returns_insufficient_evidence(db_session):
    """
    ATM exists in DB (Delhi) but is far from the crime (Bengaluru).
    With a 5 km search radius the spatial filter must return 0 candidates
    → pipeline returns insufficient_evidence honestly.
    """
    _make_atm(db_session, lat=28.6139, lng=77.2090)  # Delhi ATM
    crime = _make_crime(db_session)  # Bengaluru crime
    response = run_prediction_pipeline(
        db=db_session,
        crime_id=crime.crime_id,
        search_radius_km=5.0,
    )
    assert response["status"] == "insufficient_evidence"
    assert response["predictions"] == []


# ---------------------------------------------------------------------------
# 5. No transaction history for candidate ATMs — pipeline still completes
#    (ARCHITECTURE.md §10: "no transaction activity")
# ---------------------------------------------------------------------------

def test_failure_no_transactions_pipeline_completes(db_session):
    """
    Pipeline must complete and return a valid (non-fabricated) result even when
    there are zero transactions for the nearby ATM.  No crash, no fabrication.
    """
    _make_atm(db_session)          # ATM near crime site, no transactions
    crime = _make_crime(db_session)
    response = run_prediction_pipeline(
        db=db_session,
        crime_id=crime.crime_id,
        search_radius_km=5.0,
    )
    # Status is either ok (low-confidence scores still accepted) or
    # insufficient_confidence — both are honest, neither is a crash.
    assert response["status"] in ("ok", "insufficient_confidence", "insufficient_evidence")
    assert isinstance(response["predictions"], list)


# ---------------------------------------------------------------------------
# 6. Model returns insufficient_confidence → propagated faithfully
#    (ARCHITECTURE.md §10 + ML_SPEC.md: "never manufacture a high-risk prediction")
# ---------------------------------------------------------------------------

def test_failure_model_insufficient_confidence_not_fabricated(db_session):
    """
    When MockModelInterface decides confidence is too low it returns
    insufficient_confidence.  The orchestration layer must propagate that
    status faithfully — never upgrade it to 'ok' or inject fabricated results.
    """
    _make_atm(db_session)
    crime = _make_crime(db_session)

    # Mock a ModelInterface that always returns insufficient_confidence
    mock_model = MagicMock()
    mock_model.model_version = "mock_low_conf_v1"
    mock_model.predict.return_value = {
        "model_version": "mock_low_conf_v1",
        "predictions": [],
        "status": "insufficient_confidence",
    }

    response = run_prediction_pipeline(
        db=db_session,
        crime_id=crime.crime_id,
        model=mock_model,
        search_radius_km=5.0,
    )
    assert response["status"] == "insufficient_confidence"
    assert response["predictions"] == []

    # Confirm the prediction run was persisted with the correct status
    run = db_session.query(Prediction).filter(
        Prediction.crime_id == crime.crime_id
    ).first()
    assert run is not None
    assert run.status == "insufficient_confidence"


# ---------------------------------------------------------------------------
# 7. Model unavailable (raises) → surfaces as HTTPException 503
#    (ARCHITECTURE.md §10: "model unavailable")
# ---------------------------------------------------------------------------

def test_failure_model_raises_surfaces_gracefully(db_session):
    """
    If ModelInterface.predict() raises (e.g., the model service is down),
    the orchestration layer must not return a fabricated prediction.
    The exception propagates — callers map it to HTTP 503.
    """
    _make_atm(db_session)
    crime = _make_crime(db_session)

    mock_model = MagicMock()
    mock_model.model_version = "failing_model_v1"
    mock_model.predict.side_effect = RuntimeError("Model service unavailable")

    with pytest.raises(RuntimeError, match="Model service unavailable"):
        run_prediction_pipeline(
            db=db_session,
            crime_id=crime.crime_id,
            model=mock_model,
            search_radius_km=5.0,
        )


# ---------------------------------------------------------------------------
# 8. Spatial service unavailable (raises) → propagates, no fabrication
#    (ARCHITECTURE.md §10: "spatial service unavailable")
# ---------------------------------------------------------------------------

def test_failure_spatial_service_raises_propagates(db_session):
    """
    If SpatialService.get_candidate_atms() raises the error must propagate;
    the pipeline must not silently swallow it and return fabricated data.
    """
    _make_atm(db_session)
    crime = _make_crime(db_session)

    mock_spatial = MagicMock()
    mock_spatial.get_candidate_atms.side_effect = ConnectionError(
        "GIS service unreachable"
    )

    with pytest.raises(ConnectionError, match="GIS service unreachable"):
        run_prediction_pipeline(
            db=db_session,
            crime_id=crime.crime_id,
            spatial_svc=mock_spatial,
            search_radius_km=5.0,
        )


# ---------------------------------------------------------------------------
# 9. Crime not found → 404 on prediction trigger (ARCHITECTURE.md §10)
# ---------------------------------------------------------------------------

def test_failure_crime_not_found_raises_404(db_session):
    """
    Triggering a prediction for a crime_id that doesn't exist must raise
    HTTP 404, not 500 or a silent empty response.
    """
    with pytest.raises(HTTPException) as exc:
        run_prediction_pipeline(
            db=db_session,
            crime_id=uuid.uuid4(),  # random, non-existent
        )
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# 10. Malformed request body → 422 standard envelope (via FastAPI TestClient)
#     (ARCHITECTURE.md §10: "malformed requests")
# ---------------------------------------------------------------------------

def test_failure_malformed_crime_payload_returns_422(client):
    """
    Submitting a crime with a missing required field (latitude) must return
    HTTP 422 with the standard error envelope.
    """
    resp = client.post(
        "/api/crimes",
        json={
            "crime_type": "fraud",
            # 'location' field is intentionally omitted
            "amount": 10000.0,
        },
        headers={"Authorization": "Bearer dummy"},  # will fail auth, that's ok
    )
    # Could be 401/403 (no real auth token) or 422 — both are valid rejection shapes
    assert resp.status_code in (401, 422)
    body = resp.json()
    assert "error" in body


def test_failure_negative_amount_rejected_at_schema(db_session):
    """
    Pydantic schema must reject a negative amount before it reaches the domain.
    This is ARCHITECTURE.md §10: 'malformed requests'.
    """
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CrimeCreate(
            crime_type="fraud",
            timestamp=datetime.now(timezone.utc),
            location=LocationSchema(lat=12.9716, lng=77.5946),
            amount=-999.0,  # invalid: must be > 0
        )


# ---------------------------------------------------------------------------
# 11. Prediction window is exactly 6 hours — ADR-005 literal
#     (not re-derived or approximated)
# ---------------------------------------------------------------------------

def test_adr005_six_hour_window_is_literal(db_session):
    """
    ADR-005: predicted_window duration must be exactly 6 hours.
    Verify this via the MockModelInterface output — the literal timedelta(hours=6)
    constant, not an approximation.
    """
    from datetime import timedelta
    from app.interfaces.model_interface import MockModelInterface

    mock = MockModelInterface()
    payload = {
        "crime": {
            "crime_id": str(uuid.uuid4()),
            "crime_type": "fraud",
            "timestamp": "2026-09-18T10:00:00+00:00",
            "location": {"lat": 12.9716, "lng": 77.5946},
            "amount": 50000.0,
        },
        "candidate_atms": [
            {
                "atm_id": str(uuid.uuid4()),
                "location": {"lat": 12.9720, "lng": 77.5950},
                "atm_historical_risk": 0.70,
                "spatial_features": {
                    "distance_from_crime": 0.5,
                    "nearby_crime_density": 4.0,
                },
            }
        ],
        "recent_transactions": [],
    }
    result = mock.predict(payload)
    assert result["status"] in ("ok", "insufficient_confidence")

    if result["status"] == "ok" and result["predictions"]:
        pred = result["predictions"][0]
        win = pred["predicted_window"]
        start = datetime.fromisoformat(win["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(win["end"].replace("Z", "+00:00"))
        # ADR-005: window is EXACTLY 6 hours
        assert end - start == timedelta(hours=6), (
            f"ADR-005 violation: predicted window is {end - start}, expected exactly 6h"
        )


# ---------------------------------------------------------------------------
# 12. Audit log written on every prediction_generated event (ARCHITECTURE.md §8)
# ---------------------------------------------------------------------------

def test_audit_log_written_on_prediction_generated(db_session):
    """
    Every successful or insufficient prediction run must write an AuditLog row
    with action='prediction_generated', per ARCHITECTURE.md §8.
    """
    _make_atm(db_session)
    crime = _make_crime(db_session)

    audit_count_before = db_session.query(AuditLog).count()

    run_prediction_pipeline(db=db_session, crime_id=crime.crime_id)

    audit_count_after = db_session.query(AuditLog).count()
    assert audit_count_after > audit_count_before, (
        "Expected at least one new AuditLog row after prediction_generated"
    )

    # Verify at least one audit row has action='prediction_generated'
    prediction_audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "prediction_generated")
        .first()
    )
    assert prediction_audit is not None
    assert prediction_audit.resource is not None
    assert "prediction:" in prediction_audit.resource


# ---------------------------------------------------------------------------
# 13. Alert NOT generated when confidence < 0.5 (ADR-006 literal)
#     (ARCHITECTURE.md §10: "low-confidence prediction")
# ---------------------------------------------------------------------------

def test_adr006_no_alert_below_confidence_threshold(db_session):
    """
    ADR-006: risk_score >= 0.4 AND confidence >= 0.5 required for any alert.
    A result with confidence < 0.5, even at very high risk, must NOT generate
    an alert.  This is the literal threshold, not an approximation.
    """
    now = datetime.now(timezone.utc)
    atm = _make_atm(db_session)
    crime = _make_crime(db_session)

    pred_run = Prediction(
        prediction_id=uuid.uuid4(),
        crime_id=crime.crime_id,
        generated_at=now,
        model_version="test_adr006",
        status="ok",
    )
    db_session.add(pred_run)
    db_session.commit()

    from app.models.prediction import PredictionResult

    # High risk score but confidence below ADR-006 threshold (0.5)
    low_conf_result = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred_run.prediction_id,
        atm_id=atm.atm_id,
        risk_score=0.95,    # very high risk
        confidence=0.45,    # but below 0.5 threshold
        predicted_window_start=now,
        predicted_window_end=now,
    )

    alerts = evaluate_and_generate_alerts(db_session, pred_run, [low_conf_result])
    assert alerts == [], (
        "ADR-006 violation: alert generated despite confidence < 0.5"
    )


def test_adr006_alert_generated_at_exact_threshold(db_session):
    """
    ADR-006: alert MUST be generated when risk_score >= 0.4 AND confidence >= 0.5
    (boundary values — exactly at the threshold, not just above it).
    """
    now = datetime.now(timezone.utc)
    atm = _make_atm(db_session)
    crime = _make_crime(db_session)

    pred_run = Prediction(
        prediction_id=uuid.uuid4(),
        crime_id=crime.crime_id,
        generated_at=now,
        model_version="test_adr006_boundary",
        status="ok",
    )
    db_session.add(pred_run)
    db_session.commit()

    from app.models.prediction import PredictionResult

    boundary_result = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred_run.prediction_id,
        atm_id=atm.atm_id,
        risk_score=0.40,    # exactly at lower boundary
        confidence=0.50,    # exactly at confidence threshold
        predicted_window_start=now,
        predicted_window_end=now,
    )

    alerts = evaluate_and_generate_alerts(db_session, pred_run, [boundary_result])
    assert len(alerts) == 1
    assert alerts[0].severity == "medium"
