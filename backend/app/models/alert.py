"""
app/models/alert.py — SQLAlchemy ORM model for the `alerts` table.

Schema reference: DATA_SCHEMA.md §alerts
Alert generation rule: ADRS.md ADR-006
  - risk_score >= 0.7 AND confidence >= 0.5 → severity: high
  - 0.4 <= risk_score < 0.7 AND confidence >= 0.5 → severity: medium
  - anything else → no alert created
Alert creation is handled by domain/alert_generation.py (a later task),
not by this model file.
"""
import uuid
from sqlalchemy import Column, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from app.core.db import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    # FK → predictions, per DATA_SCHEMA.md §alerts
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
    # low / medium / high — populated per ADR-006 mapping
    severity = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    # new / acknowledged / resolved
    status = Column(String, nullable=False, default="new")
    # dashboard / mock_sms / mock_email
    channel = Column(String, nullable=False, default="dashboard")

    prediction = relationship("Prediction", back_populates="alerts")
    atm = relationship("ATM")
