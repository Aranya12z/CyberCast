"""
app/schemas/auth.py — Pydantic schemas for authentication requests & responses.

# [MVP TARGET] — Auth endpoints contract.
Reference: API_SPEC.md §/api/auth/*
"""
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Payload for POST /api/auth/login."""
    username: str = Field(..., description="User's unique username")
    password: str = Field(..., description="Plaintext password for verification")


class TokenResponse(BaseModel):
    """Response returned upon successful POST /api/auth/login."""
    access_token: str = Field(..., description="HS256 Bearer JWT")
    token_type: str = Field(default="bearer", description="Token type (bearer)")
    role: str = Field(..., description="Role: investigator | bank_analyst | administrator")

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    """Response returned from GET /api/auth/me."""
    user_id: str = Field(..., description="Unique UUID of the user")
    name: str = Field(..., description="Full display name of the user")
    role: str = Field(..., description="User's role")

    model_config = ConfigDict(from_attributes=True)
