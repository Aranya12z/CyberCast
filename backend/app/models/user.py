"""
app/models/user.py — SQLAlchemy ORM model for the `users` table.

Schema reference: DATA_SCHEMA.md §users

Roles (single text column, no separate roles table):
  investigator / bank_analyst / administrator

DATA_SCHEMA.md note: "there is deliberately no separate `roles` table for
MVP — three fixed roles don't justify a many-to-many join table."
If role permissions need to vary per-user beyond the fixed three, that is a
[FUTURE] schema change requiring an ADR.

Security: password_hash stores a bcrypt hash. Plaintext passwords must never
be stored or logged — see AGENTS.md §17 (Data and Privacy).
"""
import uuid
from sqlalchemy import Column, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(
        Uuid(as_uuid=True).with_variant(PG_UUID(as_uuid=True), "postgresql"),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = Column(String, nullable=False)
    # investigator / bank_analyst / administrator
    role = Column(String, nullable=False)
    # bcrypt hash — never store or log plaintext (AGENTS.md §17)
    password_hash = Column(String, nullable=False)
