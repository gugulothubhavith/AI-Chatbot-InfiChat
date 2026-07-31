"""Shared test fixtures for InfiChat backend.

Uses SQLite in-memory for fast, isolated tests.
No Docker or external services required.
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator

# Use SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///./test_infichat.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ALLOWED_ORIGINS"] = "http://testserver,http://localhost:5173"
os.environ["TRUSTED_HOSTS"] = '["testserver", "localhost", "127.0.0.1"]'

os.environ["ALLOWED_HOSTS"] = "*"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database.db import Base, get_db
from app.main import app


# ── In-memory SQLite engine for tests ─────────────────────────
_test_engine = create_engine(
    "sqlite:///./test_infichat.db",
    connect_args={"check_same_thread": False},
)

@event.listens_for(_test_engine, "connect")
def _set_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

_test_session = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def override_get_db():
    """Override the FastAPI dependency with test session."""
    db = _test_session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)

    # Close every pooled connection before touching the files. Windows refuses
    # to unlink a file that still has an open handle, so without this the
    # teardown raises PermissionError and the whole session exits non-zero even
    # when all tests passed.
    _test_engine.dispose()

    for path in (
        "./test_infichat.db",
        "./test_infichat.db-wal",
        "./test_infichat.db-shm",
    ):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except PermissionError:
            # A stray handle survived; leaving a stale test DB behind is
            # harmless (the next run recreates it) and must not fail the run.
            pass


@pytest.fixture
def db_session():
    """Get a fresh DB session for each test."""
    session = _test_session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client() -> Generator:
    """FastAPI TestClient for integration tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client) -> dict:
    """Create a test user and return auth headers."""
    from app.core.auth import create_access_token

    # Register a test user via API
    client.post("/api/v1/auth/register", json={
        "email": "test@test.com",
        "username": "testuser",
        "password": "TestPass123!",
    })

    # Login
    resp = client.post("/api/v1/auth/login", json={
        "email": "test@test.com",
        "password": "TestPass123!",
    })
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
