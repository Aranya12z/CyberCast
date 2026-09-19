"""
app/schemas/atm.py — Pydantic schemas for ATM resources and GeoJSON format.

Reference: API_SPEC.md §/api/atms/* and ML_GIS_CONTRACTS.md §2
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import LocationSchema


class ATMResponse(BaseModel):
    """ATM object schema matching API_SPEC.md §/api/atms/*"""
    atm_id: str = Field(..., description="Unique ATM identifier")
    location: LocationSchema = Field(..., description="WGS84 lat/lng coordinate")
    bank: str = Field(..., description="Bank name")
    area: str = Field(..., description="Area / locality name")
    historical_risk_score: Optional[float] = Field(
        default=0.0, description="Rolling historical risk score [0, 1]"
    )

    model_config = ConfigDict(from_attributes=True)


class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., description="[longitude, latitude]")


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
