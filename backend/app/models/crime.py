"""
app/models/crime.py — SQLAlchemy ORM model for the `crimes` table.

Schema reference: DATA_SCHEMA.md §crimes
"""
import uuid
from sqlalchemy import Column, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TIMESTAMP

from app.core.db import Base


class Crime(Base):
    __tablename__ = "crimes"

    crime_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    crime_type = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    amount = Column(Numeric, nullable=False)
