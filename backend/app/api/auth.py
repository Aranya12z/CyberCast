"""
app/api/auth.py — Authentication endpoints.

# [MVP TARGET] — Tagged [MVP TARGET].
Endpoints:
  POST /api/auth/login  — Authenticate user, issue JWT access token
  POST /api/auth/logout — Invalidate session (writes audit log)
  GET  /api/auth/me     — Return current authenticated user's profile

Reference: API_SPEC.md §/api/auth/*
Architecture: ARCHITECTURE.md §8
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_access_token, get_current_user, verify_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT",
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user by username and password.
    Returns access token and role.
    # [MVP TARGET]
    """
    user = db.query(User).filter(User.name == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT with user_id as subject and role embedded in claims
    token_data = {
        "sub": str(user.user_id),
        "name": user.name,
        "role": user.role,
    }
    access_token = create_access_token(data=token_data)

    # Audit log entry for login
    audit_entry = AuditLog(
        user_id=user.user_id,
        action="login",
        timestamp=datetime.now(timezone.utc),
        resource=f"user:{user.user_id}",
        metadata_={"status": "success", "role": user.role},
    )
    db.add(audit_entry)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Log out current user",
)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Log out the current user and record an audit log entry.
    (JWTs are stateless; client should drop the token).
    # [MVP TARGET]
    """
    audit_entry = AuditLog(
        user_id=current_user.user_id,
        action="logout",
        timestamp=datetime.now(timezone.utc),
        resource=f"user:{current_user.user_id}",
        metadata_={"status": "success"},
    )
    db.add(audit_entry)
    db.commit()

    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user details",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the currently authenticated user.
    # [MVP TARGET]
    """
    return MeResponse(
        user_id=str(current_user.user_id),
        name=current_user.name,
        role=current_user.role,
    )
