"""
app/schemas/crime.py — Pydantic schemas for crime ingestion and retrieval.

Reference: API_SPEC.md §/api/crimes/*
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LocationSchema


class CrimeBase(BaseModel):
    crime_type: str = Field(..., description="Type of cyber financial crime / complaint")
    timestamp: datetime = Field(..., description="Incident timestamp (UTC)")
    location: LocationSchema = Field(..., description="WGS84 lat/lng coordinate")
    amount: float = Field(..., ge=0.0, description="Defrauded amount in INR")


class CrimeCreate(CrimeBase):
    pass


class CrimeResponse(CrimeBase):
    crime_id: str = Field(..., description="Unique UUID for the crime incident")

    model_config = ConfigDict(from_attributes=True)
