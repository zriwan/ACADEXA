# tests/conftest.py
import os
import pytest

# --- Load .env if present (so TEST_DATABASE_URL can be read) ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Test environment switches ---
# Mark we're in tests
os.environ.setdefault("ENV", "test")

# If you defined TEST_DATABASE_URL in your .env / system env, use it;
# otherwise fall back to a local SQLite file (simple and CI-friendly).
test_db_url = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
os.environ["DATABASE_URL"] = test_db_url  # <-- IMPORTANT: set BEFORE importing your app

# Now it's safe to import the app (it will see DATABASE_URL pointing to test DB)
from fastapi.testclient import TestClient
from backend.main import app
  # If you move app to backend/main.py, change to: from backend.main import app

@pytest.fixture(scope="session")
def client():
    """A reusable HTTP client for tests."""
    return TestClient(app)
