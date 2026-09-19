"""
backend/tests/conftest.py — Pytest fixtures for test database and FastAPI TestClient.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User

# In-memory SQLite database for fast unit testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_users(db_session):
    """Seed test users with the three distinct roles."""
    users = {
        "investigator": User(
            user_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            name="Test Investigator",
            role="investigator",
            password_hash=hash_password("investigator_pass"),
        ),
        "bank_analyst": User(
            user_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
            name="Test Analyst",
            role="bank_analyst",
            password_hash=hash_password("analyst_pass"),
        ),
        "admin": User(
            user_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
            name="Test Admin",
            role="administrator",
            password_hash=hash_password("admin_pass"),
        ),
    }
    for user in users.values():
        db_session.add(user)
    db_session.commit()
    return users


@pytest.fixture(scope="function")
def investigator_token(seed_users):
    u = seed_users["investigator"]
    return create_access_token({"sub": str(u.user_id), "name": u.name, "role": u.role})


@pytest.fixture(scope="function")
def bank_analyst_token(seed_users):
    u = seed_users["bank_analyst"]
    return create_access_token({"sub": str(u.user_id), "name": u.name, "role": u.role})


@pytest.fixture(scope="function")
def admin_token(seed_users):
    u = seed_users["admin"]
    return create_access_token({"sub": str(u.user_id), "name": u.name, "role": u.role})


@pytest.fixture(scope="function")
def investigator_headers(investigator_token):
    return {"Authorization": f"Bearer {investigator_token}"}


@pytest.fixture(scope="function")
def bank_analyst_headers(bank_analyst_token):
    return {"Authorization": f"Bearer {bank_analyst_token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def auth_client(client, investigator_headers):
    client.headers.update(investigator_headers)
    return client
