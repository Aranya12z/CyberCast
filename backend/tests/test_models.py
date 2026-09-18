"""
backend/tests/test_models.py — Tests for SQLAlchemy ORM models and relationships.

Validates DATA_SCHEMA.md relationships:
- Crime (1) -> Prediction (many)
- Prediction (1) -> PredictionResult (many)
- PredictionResult (1) -> PredictionFeature (many) — FK points to prediction_results
- Prediction (1) -> Alert (many)
- ATM (1) -> Transaction (many)
- ATM (1) -> PredictionResult (many)
- User (1) -> AuditLog (many)
"""
from datetime import datetime, timezone
import uuid
import pytest
from app.models import (
    ATM,
    Alert,
    AuditLog,
    Crime,
    ModelMetadata,
    Prediction,
    PredictionFeature,
    PredictionResult,
    Transaction,
    User,
)


def test_models_and_relationships(db_session):
    """Verify that all ORM models create tables and link relationships correctly."""
    now = datetime.now(timezone.utc)

    # 1. User
    user = User(
        user_id=uuid.uuid4(),
        name="Officer Dave",
        role="investigator",
        password_hash="hashed_pw",
    )
    db_session.add(user)

    # 2. AuditLog
    audit = AuditLog(
        event_id=uuid.uuid4(),
        user_id=user.user_id,
        action="login",
        timestamp=now,
        resource="system",
        metadata_={"ip": "127.0.0.1"},
    )
    db_session.add(audit)

    # 3. ATM
    atm = ATM(
        atm_id=uuid.uuid4(),
        latitude=12.9716,
        longitude=77.5946,
        bank="State Bank",
        area="MG Road",
        historical_risk_score=0.35,
    )
    db_session.add(atm)

    # 4. Transaction
    txn = Transaction(
        transaction_id=uuid.uuid4(),
        atm_id=atm.atm_id,
        timestamp=now,
        amount=10000.0,
        account_id="ACC-9876",
    )
    db_session.add(txn)

    # 5. Crime
    crime = Crime(
        crime_id=uuid.uuid4(),
        crime_type="atm_fraud",
        timestamp=now,
        latitude=12.9720,
        longitude=77.5950,
        amount=50000.0,
    )
    db_session.add(crime)

    # 6. ModelMetadata
    model_meta = ModelMetadata(
        model_version="v1.0.0",
        trained_at=now,
        algorithm="random_forest",
        eval_metrics={"accuracy": 0.88, "f1": 0.85},
    )
    db_session.add(model_meta)

    # 7. Prediction Run
    pred = Prediction(
        prediction_id=uuid.uuid4(),
        crime_id=crime.crime_id,
        generated_at=now,
        model_version=model_meta.model_version,
        status="ok",
    )
    db_session.add(pred)

    # 8. Prediction Result (Top-K item)
    result = PredictionResult(
        result_id=uuid.uuid4(),
        prediction_id=pred.prediction_id,
        atm_id=atm.atm_id,
        risk_score=0.85,
        confidence=0.75,
        predicted_window_start=now,
        predicted_window_end=now,
    )
    db_session.add(result)

    # 9. Prediction Feature (FK points to result_id, NOT prediction_id)
    feature = PredictionFeature(
        feature_id=uuid.uuid4(),
        result_id=result.result_id,
        feature_name="distance_from_crime",
        feature_value=0.45,
        contribution="high",
    )
    db_session.add(feature)

    # 10. Alert
    alert = Alert(
        alert_id=uuid.uuid4(),
        prediction_id=pred.prediction_id,
        atm_id=atm.atm_id,
        severity="high",
        created_at=now,
        status="new",
        channel="dashboard",
    )
    db_session.add(alert)

    db_session.commit()

    # Query and assert relationships
    queried_pred = db_session.get(Prediction, pred.prediction_id)
    assert queried_pred is not None
    assert len(queried_pred.results) == 1
    assert float(queried_pred.results[0].risk_score) == 0.85
    assert len(queried_pred.results[0].features) == 1
    assert queried_pred.results[0].features[0].feature_name == "distance_from_crime"
    assert queried_pred.results[0].features[0].result_id == result.result_id
    assert len(queried_pred.alerts) == 1
    assert queried_pred.alerts[0].alert_id == alert.alert_id

    queried_atm = db_session.get(ATM, atm.atm_id)
    assert float(queried_atm.historical_risk_score) == 0.35
