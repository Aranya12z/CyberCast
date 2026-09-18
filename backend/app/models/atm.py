"""
app/models/atm.py — SQLAlchemy ORM model for the `atms` table.

Schema reference: DATA_SCHEMA.md §atms
Note: historical_risk_score is a stored, offline-updated value.
  The backend reads it and attaches it per candidate ATM before calling ML.
  See ML_GIS_CONTRACTS.md §1 and DATA_SCHEMA.md §atms.
"""
import uuid
from sqlalchemy import Column, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.db import Base


class ATM(Base):
    __tablename__ = "atms"

    atm_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    bank = Column(String, nullable=False)
    area = Column(String, nullable=False)
    # Rolling risk score updated offline (not at request time).
    # This is the atm_historical_risk value the backend attaches to each
    # candidate before calling ModelInterface — see ML_GIS_CONTRACTS.md §1.
    historical_risk_score = Column(Numeric, nullable=False, default=0.0)
