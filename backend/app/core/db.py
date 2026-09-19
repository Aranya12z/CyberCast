"""
app/core/db.py — SQLAlchemy engine, session factory, and get_db() dependency.

Architecture reference: ARCHITECTURE.md §3 (L6 Data layer), BACKEND_SPEC.md §core/.
ADR-001: modular monolith — single engine, single database.
ADR-002: standard PostgreSQL, no PostGIS.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

from app.core.config import get_settings


class Base(DeclarativeBase):
    """
    Shared declarative base for all SQLAlchemy ORM models.
    All model files import and extend this Base so Alembic can discover every
    table through Base.metadata.
    """
    pass


def _make_engine():
    settings = get_settings()
    connect_args = {}
    # SQLite (used in tests only) requires check_same_thread=False
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


engine = _make_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and closes it on exit.

    Usage in a router:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
