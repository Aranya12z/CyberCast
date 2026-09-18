"""
app/models/prediction.py — ORM models for predictions, prediction_results,
and prediction_features.

Schema reference: DATA_SCHEMA.md §predictions / §prediction_results / §prediction_features

KEY CORRECTNESS POINT (DATA_SCHEMA.md, prediction_features note):
  prediction_features.result_id  →  FK to prediction_results.result_id
  NOT to predictions.prediction_id.

  Each prediction *run* produces multiple Top-K ATM results (prediction_results
  rows). Explanation features are per candidate ATM result, not per run.
  Mixing them into one bucket (pointing at predictions) was an earlier draft
  error that DATA_SCHEMA.md explicitly corrects.

Relationships (DATA_SCHEMA.md §Key Relationships):
  Crime (1) ──< Prediction (run) (1) ──< PredictionResult (many, Top-K)
  PredictionResult (1) ──< PredictionFeature (many)
  Prediction (1) ──< Alert (many)
  ATM (1) ──< PredictionResult (many)
"""
import uuid
from sqlalchemy import Column, ForeignKey, Numeric, String, Uuid, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from app.core.db import Base


class Prediction(Base):
    """One row per prediction *run* (one POST /api/predictions/{crime_id} call)."""
    __tablename__ = "predictions"

    prediction_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    crime_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("crimes.crime_id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    # model_version references model_metadata.model_version
    model_version = Column(String, ForeignKey("model_metadata.model_version"), nullable=False)
    # ok / insufficient_confidence / insufficient_evidence
    status = Column(String, nullable=False)

    crime = relationship("Crime")
    results = relationship(
        "PredictionResult",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )
    alerts = relationship(
        "Alert",
        back_populates="prediction",
        cascade="all, delete-orphan",
    )


class PredictionResult(Base):
    """One row per Top-K candidate ATM within a prediction run."""
    __tablename__ = "prediction_results"

    result_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    prediction_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
        nullable=False,
    )
    atm_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("atms.atm_id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_score = Column(Numeric, nullable=False)
    confidence = Column(Numeric, nullable=False)
    # ADR-005: fixed 6-hour horizon for MVP
    predicted_window_start = Column(TIMESTAMP(timezone=True), nullable=False)
    predicted_window_end = Column(TIMESTAMP(timezone=True), nullable=False)

    prediction = relationship("Prediction", back_populates="results")
    atm = relationship("ATM")
    features = relationship(
        "PredictionFeature",
        back_populates="result",
        cascade="all, delete-orphan",
    )


class PredictionFeature(Base):
    """
    Feature contributions for one Top-K result.
    FK points to prediction_results, NOT predictions.
    See module docstring for the critical correctness note.
    """
    __tablename__ = "prediction_features"

    feature_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    # FK → prediction_results.result_id (not predictions.prediction_id)
    result_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("prediction_results.result_id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_name = Column(String, nullable=False)   # e.g. distance_from_crime
    feature_value = Column(Numeric, nullable=False)
    contribution = Column(String, nullable=False)    # high / medium / low

    result = relationship("PredictionResult", back_populates="features")
