# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import get_db_connection
from backend.models import Base

# Test database (SQLite file)
SQLALCHEMY_TEST_DB_URL = "sqlite:///./test_db.sqlite3"

engine = create_engine(
    SQLALCHEMY_TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once, drop at end of test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ only DB dependency override
app.dependency_overrides[get_db_connection] = override_get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
