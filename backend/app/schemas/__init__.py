"""
app/schemas/__init__.py — Re-exports all Pydantic request and response schemas.
"""
from app.schemas.common import LocationSchema, PredictedWindow, ErrorDetail, ErrorResponse
from app.schemas.auth import LoginRequest, TokenResponse, MeResponse
from app.schemas.crime import CrimeBase, CrimeCreate, CrimeResponse
from app.schemas.atm import (
    ATMResponse,
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
)
from app.schemas.transaction import TransactionResponse
from app.schemas.prediction import (
    ExplanationItem,
    PredictionResultItem,
    PredictionResponse,
)
from app.schemas.alert import AlertResponse, AlertAcknowledgeResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PredictionStats,
    RecentActivityItem,
)
from app.schemas.intelligence import (
    IntelligenceResponse,
    LatestPredictionSummary,
    TopResultItem,
    RelatedAlertItem,
)

__all__ = [
    "LocationSchema",
    "PredictedWindow",
    "ErrorDetail",
    "ErrorResponse",
    "LoginRequest",
    "TokenResponse",
    "MeResponse",
    "CrimeBase",
    "CrimeCreate",
    "CrimeResponse",
    "ATMResponse",
    "GeoJSONGeometry",
    "GeoJSONFeature",
    "GeoJSONFeatureCollection",
    "TransactionResponse",
    "ExplanationItem",
    "PredictionResultItem",
    "PredictionResponse",
    "AlertResponse",
    "AlertAcknowledgeResponse",
    "DashboardSummaryResponse",
    "PredictionStats",
    "RecentActivityItem",
    "IntelligenceResponse",
    "LatestPredictionSummary",
    "TopResultItem",
    "RelatedAlertItem",
]
