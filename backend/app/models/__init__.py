"""
app/models/__init__.py — Re-exports all SQLAlchemy ORM models and Base.
"""
from app.core.db import Base
from app.models.crime import Crime
from app.models.atm import ATM
from app.models.transaction import Transaction
from app.models.model_metadata import ModelMetadata
from app.models.prediction import Prediction, PredictionResult, PredictionFeature
from app.models.alert import Alert
from app.models.user import User
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "Crime",
    "ATM",
    "Transaction",
    "ModelMetadata",
    "Prediction",
    "PredictionResult",
    "PredictionFeature",
    "Alert",
    "User",
    "AuditLog",
]
