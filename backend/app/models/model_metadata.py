"""
app/models/model_metadata.py — SQLAlchemy ORM model for `model_metadata`.

Schema reference: DATA_SCHEMA.md §model_metadata

MVP model versioning: a manually incremented string identifier set at training
time (e.g. rf_v1_20260917). Not a model registry.
Full MLOps (drift monitoring, auto-retraining, model registry service) = [FUTURE].
Reference: ML_SPEC.md §Model lifecycle, ARCHITECTURE.md §16 (Anti-overengineering).
"""
from sqlalchemy import Column, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TIMESTAMP

from app.core.db import Base


class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    # e.g. "rf_v1_20260917" — manually set at training time (ML_SPEC.md)
    model_version = Column(String, primary_key=True)
    trained_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # random_forest / xgboost
    algorithm = Column(String, nullable=True)
    # Offline evaluation metrics (precision@K, recall, calibration, etc.)
    eval_metrics = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
