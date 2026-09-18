"""
backend/tests/test_auth.py — Tests for password hashing, JWT issue/verify, and /api/auth/* endpoints.

# [MVP TARGET] — Auth unit tests.
"""
from datetime import timedelta
import pytest
from fastapi import Depends, HTTPException
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    require_role,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User


def test_password_hashing():
    """Verify bcrypt password hashing and verification."""
    password = "secret_password_123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_create_and_decode():
    """Verify JWT token creation and payload extraction."""
    payload = {"sub": "11111111-1111-1111-1111-111111111111", "name": "Alice", "role": "investigator"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == payload["sub"]
    assert decoded["name"] == payload["name"]
    assert decoded["role"] == payload["role"]
    assert "exp" in decoded


def test_jwt_expired():
    """Verify expired token raises 401 HTTPException."""
    payload = {"sub": "11111111-1111-1111-1111-111111111111"}
    # Token expired 1 minute ago
    token = create_access_token(payload, expires_delta=timedelta(minutes=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_login_success(client, seed_users, db_session):
    """POST /api/auth/login with valid credentials returns JWT and writes audit log."""
    response = client.post(
        "/api/auth/login",
        json={"username": "Test Investigator", "password": "investigator_pass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "investigator"

    # Verify audit log was recorded
    audit_logs = db_session.query(AuditLog).filter(AuditLog.action == "login").all()
    assert len(audit_logs) == 1
    assert audit_logs[0].user_id == seed_users["investigator"].user_id


def test_login_invalid_password(client, seed_users):
    """POST /api/auth/login with wrong password returns 401 and standard error envelope."""
    response = client.post(
        "/api/auth/login",
        json={"username": "Test Investigator", "password": "wrong_password"},
    )
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["message"] == "Incorrect username or password"
    assert err["code"] == "HTTP_401"


def test_login_unknown_user(client, seed_users):
    """POST /api/auth/login with nonexistent user returns 401 and standard error envelope."""
    response = client.post(
        "/api/auth/login",
        json={"username": "Nonexistent User", "password": "password"},
    )
    assert response.status_code == 401
    err = response.json()["error"]
    assert err["message"] == "Incorrect username or password"
    assert err["code"] == "HTTP_401"


def test_get_me_authenticated(client, seed_users):
    """GET /api/auth/me returns current user details when valid token is provided."""
    # Login first
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "Test Analyst", "password": "analyst_pass"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(seed_users["bank_analyst"].user_id)
    assert data["name"] == "Test Analyst"
    assert data["role"] == "bank_analyst"


def test_get_me_unauthorized(client):
    """GET /api/auth/me returns 401 when token is missing."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "error" in response.json()


def test_logout(client, seed_users, db_session):
    """POST /api/auth/logout returns success and records audit log."""
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "Test Admin", "password": "admin_pass"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"

    # Check logout audit log
    logout_log = db_session.query(AuditLog).filter(AuditLog.action == "logout").first()
    assert logout_log is not None
    assert logout_log.user_id == seed_users["admin"].user_id


def test_require_role_dependency():
    """Verify require_role allows matching role and rejects forbidden role."""
    investigator_user = User(
        name="Investigator", role="investigator"
    )
    analyst_user = User(
        name="Analyst", role="bank_analyst"
    )

    # Allowed role
    checker = require_role("investigator", "administrator")
    result = checker(current_user=investigator_user)
    assert result == investigator_user

    # Forbidden role
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=analyst_user)
    assert exc_info.value.status_code == 403
    assert "Role 'bank_analyst' is not permitted" in exc_info.value.detail
