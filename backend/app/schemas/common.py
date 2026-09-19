"""
app/schemas/common.py — Common reusable Pydantic schemas and error models.

Reference: API_SPEC.md §Conventions
"""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationSchema(BaseModel):
    """WGS84 lat/lng coordinate pair."""
    lat: float = Field(..., description="Latitude in decimal degrees")
    lng: float = Field(..., description="Longitude in decimal degrees")

    model_config = ConfigDict(from_attributes=True)


class PredictedWindow(BaseModel):
    """Predicted withdrawal time window (start and end in ISO 8601 UTC)."""
    start: datetime = Field(..., description="Window start time (UTC)")
    end: datetime = Field(..., description="Window end time (UTC)")

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error envelope matching API_SPEC.md: { error: { code, message, details } }"""
    error: ErrorDetail
