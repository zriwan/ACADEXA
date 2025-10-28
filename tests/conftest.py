# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient

# --- Load .env if present (so TEST_DATABASE_URL can be read) ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Test environment switches ---
os.environ.setdefault("ENV", "test")

# Use TEST_DATABASE_URL if defined, else fall back to SQLite
test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url  # set BEFORE importing your app

# Now it’s safe to import the app (it will see DATABASE_URL pointing to test DB)
from backend.main import app
from backend.database import Base, engine


@pytest.fixture(scope="session")
def client():
    """Reusable HTTP client for tests."""
    return TestClient(app)


# ✅ Option 2: Drop & recreate tables before every test module (cleanest approach)
@pytest.fixture(scope="module", autouse=True)
def _clean_tables():
    """Reset all tables for each test module."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
