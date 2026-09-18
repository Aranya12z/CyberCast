"""
app/models/transaction.py — SQLAlchemy ORM model for the `transactions` table.

Schema reference: DATA_SCHEMA.md §transactions
Note: account_id is synthetic/anonymized for MVP — no real personal data.
"""
import uuid
from sqlalchemy import Column, ForeignKey, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship

from app.core.db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    atm_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        ForeignKey("atms.atm_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    amount = Column(Numeric, nullable=False)
    # Synthetic/anonymized identifier for MVP (DATA_SCHEMA.md)
    account_id = Column(String, nullable=False)

    atm = relationship("ATM")
