"""
backend/tests/test_api_endpoints.py — Comprehensive tests for all REST API endpoints,
error envelope verification, and mock compatibility acceptance checks.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.atm import ATM
from app.models.crime import Crime
from app.models.transaction import Transaction


@pytest.fixture
def seed_pipeline_data(db_session):
    """Seed comprehensive test data mirroring frontend mocks for API verification."""
    now = datetime.now(timezone.utc)

    # ATMs matching frontend mock areas
    atm1 = ATM(
        atm_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        latitude=12.9341,
        longitude=77.6258,
        bank="HDFC Bank",
        area="Koramangala 4th Block",
        historical_risk_score=0.79,
    )
    atm2 = ATM(
        atm_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        latitude=12.9372,
        longitude=77.6289,
        bank="State Bank of India",
        area="Koramangala Sony World Signal",
        historical_risk_score=0.72,
    )
    db_session.add_all([atm1, atm2])

    # Transactions
    t1 = Transaction(
        transaction_id=uuid.uuid4(),
        atm_id=atm1.atm_id,
        timestamp=now,
        amount=10000.0,
        account_id="ACC-HDFC-991",
    )
    db_session.add(t1)

    # Crime matching frontend mock
    crime = Crime(
        crime_id=uuid.UUID("89021400-0000-0000-0000-000000000000"),
        crime_type="UPI Fraud / Social Engineering",
        timestamp=now,
        latitude=12.9352,
        longitude=77.6245,
        amount=125000.00,
    )
    db_session.add(crime)
    db_session.commit()

    return {
        "atm1": atm1,
        "atm2": atm2,
        "crime": crime,
        "txn": t1,
    }


def test_crimes_api_endpoints(client, seed_pipeline_data):
    """Test GET /api/crimes, GET /api/crimes/{id}, and POST /api/crimes."""
    # List crimes
    res = client.get("/api/crimes")
    assert res.status_code == 200
    crimes = res.json()
    assert len(crimes) >= 1
    item = crimes[0]
    assert "crime_id" in item
    assert "crime_type" in item
    assert "timestamp" in item
    assert "location" in item
    assert "lat" in item["location"]
    assert "lng" in item["location"]
    assert "amount" in item

    # Get single crime
    crime_id = str(seed_pipeline_data["crime"].crime_id)
    res_single = client.get(f"/api/crimes/{crime_id}")
    assert res_single.status_code == 200
    assert res_single.json()["crime_id"] == crime_id

    # Create new crime
    post_payload = {
        "crime_type": "ATM Card Skimming / Clone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {"lat": 12.9784, "lng": 77.6408},
        "amount": 68000.00,
    }
    res_post = client.post("/api/crimes", json=post_payload)
    assert res_post.status_code == 201
    created = res_post.json()
    assert created["crime_type"] == post_payload["crime_type"]
    assert created["amount"] == 68000.00


def test_atms_api_endpoints(client, seed_pipeline_data):
    """Test GET /api/atms (JSON and GeoJSON) and GET /api/atms/{id}."""
    # List ATMs JSON
    res = client.get("/api/atms")
    assert res.status_code == 200
    atms = res.json()
    assert len(atms) >= 2
    item = atms[0]
    assert "atm_id" in item
    assert "location" in item
    assert "bank" in item
    assert "area" in item
    assert "historical_risk_score" in item

    # List ATMs GeoJSON
    res_geo = client.get("/api/atms?format=geojson")
    assert res_geo.status_code == 200
    geo = res_geo.json()
    assert geo["type"] == "FeatureCollection"
    assert len(geo["features"]) >= 2
    feat = geo["features"][0]
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "Point"
    assert len(feat["geometry"]["coordinates"]) == 2  # [lng, lat]
    assert "atm_id" in feat["properties"]
    assert "risk_score" in feat["properties"]
    assert "confidence" in feat["properties"]
    assert "risk_category" in feat["properties"]

    # Get single ATM
    atm_id = str(seed_pipeline_data["atm1"].atm_id)
    res_single = client.get(f"/api/atms/{atm_id}")
    assert res_single.status_code == 200
    assert res_single.json()["atm_id"] == atm_id


def test_transactions_api_endpoint(client, seed_pipeline_data):
    """Test GET /api/transactions filtering."""
    res = client.get("/api/transactions")
    assert res.status_code == 200
    txns = res.json()
    assert len(txns) >= 1
    t = txns[0]
    assert "transaction_id" in t
    assert "atm_id" in t
    assert "timestamp" in t
    assert "amount" in t
    assert "account_id" in t


def test_prediction_and_alert_api_flow(client, seed_pipeline_data):
    """Test POST /api/predictions/{crime_id}, GET /api/predictions/{crime_id}, alerts, and intelligence."""
    crime_id = str(seed_pipeline_data["crime"].crime_id)

    # 1. Trigger prediction
    res_pred = client.post(f"/api/predictions/{crime_id}")
    assert res_pred.status_code == 200
    pred_data = res_pred.json()
    assert pred_data["crime_id"] == crime_id
    assert pred_data["status"] == "ok"
    assert len(pred_data["predictions"]) > 0
    top_pred = pred_data["predictions"][0]
    assert "atm_id" in top_pred
    assert "risk_score" in top_pred
    assert "confidence" in top_pred
    assert "predicted_window" in top_pred
    assert "start" in top_pred["predicted_window"]
    assert "end" in top_pred["predicted_window"]
    assert len(top_pred["explanation"]) > 0

    # 2. Get latest prediction
    res_get_pred = client.get(f"/api/predictions/{crime_id}")
    assert res_get_pred.status_code == 200
    assert res_get_pred.json()["crime_id"] == crime_id

    # 3. List Alerts
    res_alerts = client.get("/api/alerts")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert len(alerts) >= 1
    al = alerts[0]
    assert "alert_id" in al
    assert "crime_id" in al
    assert "atm_id" in al
    assert "severity" in al
    assert "status" in al
    assert "channel" in al

    # 4. Acknowledge Alert
    alert_id = al["alert_id"]
    res_ack = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert res_ack.status_code == 200
    ack_data = res_ack.json()
    assert ack_data["success"] is True
    assert ack_data["status"] == "acknowledged"

    # 5. Get Intelligence Dossier
    res_intel = client.get(f"/api/intelligence/{crime_id}")
    assert res_intel.status_code == 200
    intel = res_intel.json()
    assert intel["crime_id"] == crime_id
    assert intel["crime"]["crime_type"] == "UPI Fraud / Social Engineering"
    assert intel["latest_prediction"]["status"] == "ok"
    assert len(intel["evidence"]) > 0
    assert len(intel["related_alerts"]) > 0
    assert len(intel["summary"]) > 0

    # 6. Get Dashboard Summary
    res_dash = client.get("/api/dashboard/summary")
    assert res_dash.status_code == 200
    dash = res_dash.json()
    assert "active_alerts" in dash
    assert "high_risk_predictions" in dash
    assert "prediction_stats" in dash
    assert "total_predictions_run" in dash["prediction_stats"]
    assert "avg_confidence" in dash["prediction_stats"]
    assert "insufficient_evidence_rate" in dash["prediction_stats"]
    assert "recent_activity" in dash


def test_standard_error_envelope_404(client):
    """Verify 404 errors return the standard error envelope matching API_SPEC.md."""
    missing_id = "99999999-9999-9999-9999-999999999999"
    res = client.get(f"/api/crimes/{missing_id}")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "Crime incident not found" in data["error"]["message"]
    assert isinstance(data["error"]["details"], dict)


def test_standard_error_envelope_422_malformed_input(client):
    """Verify malformed input triggers 422 with standard error envelope."""
    # Invalid amount (string instead of float)
    res = client.post(
        "/api/crimes",
        json={"crime_type": "fraud", "amount": "invalid_number", "location": {"lat": 12.0, "lng": 77.0}},
    )
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Malformed request parameters" in data["error"]["message"]
    assert "errors" in data["error"]["details"]
