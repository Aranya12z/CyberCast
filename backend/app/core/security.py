"""
app/core/security.py — Password hashing, JWT issue/verify, auth dependencies.

# [MVP TARGET] — This whole module is tagged [MVP TARGET].
# Do not describe auth as [IMPLEMENTED] in any doc, comment, or demo until
# it is fully wired end-to-end and tested against real DB users.

Architecture references:
  ARCHITECTURE.md §8 (Security & Auditability)
  BACKEND_SPEC.md §Auth & RBAC
  API_SPEC.md §/api/auth/*
  DATA_SCHEMA.md §users (roles: investigator / bank_analyst / administrator)
  ADRS.md — no new ADR needed; auth is an explicit MVP target in the architecture.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable
import uuid

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db

# ---------------------------------------------------------------------------
# Password hashing (using bcrypt directly for Python 3.12 compatibility)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """
    Hash a plaintext password with bcrypt.
    # [MVP TARGET]
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Return True if plain matches the stored bcrypt hash.
    # [MVP TARGET]
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed HS256 JWT containing the given payload.
    Adds a standard 'exp' claim.
    # [MVP TARGET]
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    Raises HTTPException 401 if the token is invalid or expired.
    # [MVP TARGET]
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency — decodes the Bearer token and returns the User ORM
    object from the database. Raises 401 if token is invalid or user is gone.
    # [MVP TARGET]
    """
    # Import here to avoid circular imports (models import db, db is imported above)
    from app.models.user import User  # noqa: PLC0415

    payload = decode_token(token)
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject identifier in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: str) -> Callable:
    """
    Return a FastAPI dependency that enforces role-based access control.

    Usage in a router:
        @router.get("/protected", dependencies=[Depends(require_role("investigator", "administrator"))])

    Raises HTTP 403 if the authenticated user's role is not in the allowed set.
    Allowed roles (DATA_SCHEMA.md §users): investigator / bank_analyst / administrator
    # [MVP TARGET]
    """
    def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not permitted for this resource. "
                       f"Required: {list(roles)}",
            )
        return current_user
    return _check
