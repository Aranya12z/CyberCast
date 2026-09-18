"""
app/models/audit_log.py — SQLAlchemy ORM model for the `audit_logs` table.

Schema reference: DATA_SCHEMA.md §audit_logs
Architecture reference: ARCHITECTURE.md §8 (Security & Auditability)
  "Who did what, when, and to which intelligence record?"

Every state-changing or sensitive-read action must write a row here.
See BACKEND_SPEC.md §Audit logging for the pattern.
"""
import uuid
from sqlalchemy import Column, ForeignKey, JSON, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    event_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    # e.g. prediction_generated / alert_acknowledged / login / data_modification
    action = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    # e.g. crime_id or prediction_id affected
    resource = Column(String, nullable=True)
    # Arbitrary metadata (request IP, outcome, etc.)
    metadata_ = Column("metadata", JSON().with_variant(JSONB, "postgresql"), nullable=True)

    user = relationship("User")
