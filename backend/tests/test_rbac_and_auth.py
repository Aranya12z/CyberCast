"""
backend/tests/test_rbac_and_auth.py — Exhaustive RBAC and authentication test suite.

Tests all 12 protected routes for:
  1. 401 Unauthorized when request carries no Authorization header.
  2. 403 Forbidden when authenticated as a role lacking write permission (bank_analyst).
  3. 200/201 OK when authenticated as an authorized role (investigator, bank_analyst for reads, administrator).
  4. Audit attribution: non-null user_id matching the authenticated user is recorded on writes & audited reads.
"""
from datetime import datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.alert import Alert
from app.models.atm import ATM
from app.models.audit_log import AuditLog
from app.models.crime import Crime
from app.models.prediction import Prediction
from app.models.transaction import Transaction


@pytest.fixture
def test_data(db_session):
    """Seed prerequisite records for endpoint tests."""
    now = datetime.now(timezone.utc)

    atm = ATM(
        atm_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        latitude=31.3090,
        longitude=75.5792,
        bank="State Bank of India",
        area="Model Town, Jalandhar",
        historical_risk_score=0.88,
    )
    db_session.add(atm)

    crime = Crime(
        crime_id=uuid.UUID("89021400-0000-0000-0000-000000000000"),
        crime_type="UPI Fraud / Social Engineering",
        timestamp=now,
        latitude=31.3090,
        longitude=75.5792,
        amount=50000.0,
    )
    db_session.add(crime)

    txn = Transaction(
        transaction_id=uuid.uuid4(),
        atm_id=atm.atm_id,
        timestamp=now,
        amount=10000.0,
        account_id="ACC-TEST-001",
    )
    db_session.add(txn)

    pred = Prediction(
        prediction_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        crime_id=crime.crime_id,
        generated_at=now,
        model_version="rf_v1_20260917",
        status="ok",
    )
    db_session.add(pred)

    alert = Alert(
        alert_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        prediction_id=pred.prediction_id,
        atm_id=atm.atm_id,
        severity="high",
        created_at=now,
        status="new",
        channel="dashboard",
    )
    db_session.add(alert)
    db_session.commit()

    return {
        "atm": atm,
        "crime": crime,
        "txn": txn,
        "prediction": pred,
        "alert": alert,
    }


# ===========================================================================
# 1. 401 Unauthorized with no token — all 12 routes
# ===========================================================================

def test_unauthenticated_requests_return_401(client, test_data):
    crime_id = str(test_data["crime"].crime_id)
    atm_id = str(test_data["atm"].atm_id)
    alert_id = str(test_data["alert"].alert_id)

    endpoints = [
        ("GET", "/api/crimes"),
        ("GET", f"/api/crimes/{crime_id}"),
        ("POST", "/api/crimes", {"crime_type": "fraud", "location": {"lat": 31.3, "lng": 75.5}, "amount": 1000, "timestamp": datetime.now(timezone.utc).isoformat()}),
        ("GET", "/api/atms"),
        ("GET", f"/api/atms/{atm_id}"),
        ("GET", "/api/transactions"),
        ("GET", "/api/alerts"),
        ("POST", f"/api/alerts/{alert_id}/acknowledge", None),
        ("GET", "/api/dashboard/summary"),
        ("GET", f"/api/intelligence/{crime_id}"),
        ("GET", f"/api/predictions/{crime_id}"),
        ("POST", f"/api/predictions/{crime_id}", None),
    ]

    for method, path, *payload in endpoints:
        data = payload[0] if payload else None
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json=data) if data else client.post(path)

        assert res.status_code == 401, f"{method} {path} returned {res.status_code}, expected 401"


# ===========================================================================
# 2. 403 Forbidden for bank_analyst attempting write endpoints
# ===========================================================================

def test_bank_analyst_forbidden_on_write_endpoints(client, test_data, bank_analyst_headers):
    crime_id = str(test_data["crime"].crime_id)
    alert_id = str(test_data["alert"].alert_id)

    # POST /api/crimes
    res_crime = client.post(
        "/api/crimes",
        headers=bank_analyst_headers,
        json={
            "crime_type": "Unauthorized ATM Withdrawal",
            "location": {"lat": 31.3090, "lng": 75.5792},
            "amount": 25000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert res_crime.status_code == 403, f"POST /api/crimes returned {res_crime.status_code}, expected 403"

    # POST /api/alerts/{id}/acknowledge
    res_alert = client.post(
        f"/api/alerts/{alert_id}/acknowledge",
        headers=bank_analyst_headers,
    )
    assert res_alert.status_code == 403, f"POST /api/alerts/ack returned {res_alert.status_code}, expected 403"

    # POST /api/predictions/{crime_id}
    res_pred = client.post(
        f"/api/predictions/{crime_id}",
        headers=bank_analyst_headers,
    )
    assert res_pred.status_code == 403, f"POST /api/predictions returned {res_pred.status_code}, expected 403"


# ===========================================================================
# 3. Read endpoints permit all 3 roles (investigator, bank_analyst, admin)
# ===========================================================================

def test_read_endpoints_accessible_by_all_roles(
    client, test_data, investigator_headers, bank_analyst_headers, admin_headers
):
    crime_id = str(test_data["crime"].crime_id)
    atm_id = str(test_data["atm"].atm_id)

    get_routes = [
        "/api/crimes",
        f"/api/crimes/{crime_id}",
        "/api/atms",
        f"/api/atms/{atm_id}",
        "/api/transactions",
        "/api/alerts",
        "/api/dashboard/summary",
        f"/api/intelligence/{crime_id}",
        f"/api/predictions/{crime_id}",
    ]

    for role_name, headers in [
        ("investigator", investigator_headers),
        ("bank_analyst", bank_analyst_headers),
        ("administrator", admin_headers),
    ]:
        for route in get_routes:
            res = client.get(route, headers=headers)
            assert res.status_code == 200, f"{role_name} GET {route} failed with {res.status_code}"


# ===========================================================================
# 4. Write endpoints permitted for investigator and administrator
# ===========================================================================

def test_write_endpoints_permitted_for_investigator_and_admin(
    client, test_data, investigator_headers, admin_headers, db_session
):
    alert_id = str(test_data["alert"].alert_id)
    crime_id = str(test_data["crime"].crime_id)

    # 1. Investigator creates crime
    res_post_inv = client.post(
        "/api/crimes",
        headers=investigator_headers,
        json={
            "crime_type": "SIM Swap Fraud",
            "location": {"lat": 31.3090, "lng": 75.5792},
            "amount": 40000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert res_post_inv.status_code == 201

    # 2. Admin creates crime
    res_post_adm = client.post(
        "/api/crimes",
        headers=admin_headers,
        json={
            "crime_type": "Phishing Incident",
            "location": {"lat": 31.3195, "lng": 75.5841},
            "amount": 75000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert res_post_adm.status_code == 201

    # 3. Investigator acknowledges alert
    res_ack_inv = client.post(
        f"/api/alerts/{alert_id}/acknowledge",
        headers=investigator_headers,
    )
    assert res_ack_inv.status_code == 200

    # 4. Admin triggers prediction
    res_pred_adm = client.post(
        f"/api/predictions/{crime_id}",
        headers=admin_headers,
    )
    assert res_pred_adm.status_code == 200


# ===========================================================================
# 5. Audit log attribution verification (user_id is non-null & matches)
# ===========================================================================

def test_audit_log_attribution_on_authenticated_actions(
    client, test_data, seed_users, investigator_headers, db_session
):
    inv_user = seed_users["investigator"]
    crime_id = str(test_data["crime"].crime_id)
    alert_id = str(test_data["alert"].alert_id)

    # Action 1: Create Crime
    res_crime = client.post(
        "/api/crimes",
        headers=investigator_headers,
        json={
            "crime_type": "Vishing Attack",
            "location": {"lat": 31.2874, "lng": 75.6021},
            "amount": 35000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert res_crime.status_code == 201
    created_crime_id = res_crime.json()["crime_id"]

    audit_crime = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource == f"crime:{created_crime_id}", AuditLog.action == "complaint_created")
        .first()
    )
    assert audit_crime is not None
    assert audit_crime.user_id == inv_user.user_id, "AuditLog.user_id must match authenticated investigator"

    # Action 2: Acknowledge Alert
    res_ack = client.post(
        f"/api/alerts/{alert_id}/acknowledge",
        headers=investigator_headers,
    )
    assert res_ack.status_code == 200
    audit_alert = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource == f"alert:{alert_id}", AuditLog.action == "alert_acknowledged")
        .first()
    )
    assert audit_alert is not None
    assert audit_alert.user_id == inv_user.user_id, "AuditLog.user_id must match authenticated user"

    # Action 3: Trigger Prediction
    res_pred = client.post(
        f"/api/predictions/{created_crime_id}",
        headers=investigator_headers,
    )
    assert res_pred.status_code == 200
    audit_pred = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "prediction_generated")
        .order_by(AuditLog.timestamp.desc())
        .first()
    )
    assert audit_pred is not None
    assert audit_pred.user_id == inv_user.user_id

    # Action 4: View Prediction (GET)
    res_get_pred = client.get(
        f"/api/predictions/{created_crime_id}",
        headers=investigator_headers,
    )
    assert res_get_pred.status_code == 200
    audit_view = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource == f"crime:{created_crime_id}", AuditLog.action == "prediction_viewed")
        .first()
    )
    assert audit_view is not None
    assert audit_view.user_id == inv_user.user_id

    # Action 5: View Intelligence (GET)
    res_intel = client.get(
        f"/api/intelligence/{created_crime_id}",
        headers=investigator_headers,
    )
    assert res_intel.status_code == 200
    audit_intel = (
        db_session.query(AuditLog)
        .filter(AuditLog.resource == f"crime:{created_crime_id}", AuditLog.action == "intelligence_viewed")
        .first()
    )
    assert audit_intel is not None
    assert audit_intel.user_id == inv_user.user_id
