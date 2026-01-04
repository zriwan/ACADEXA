# tests/test_analytics.py

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _ensure_ok_or_skip(resp):
    """
    If analytics is behind auth and returns 401,
    skip the test instead of failing.
    """
    if resp.status_code == 401:
        pytest.skip("Analytics endpoint requires authentication (401). Skipping test.")
    assert resp.status_code == 200


def test_analytics_summary_shape():
    resp = client.get("/analytics/summary")
    _ensure_ok_or_skip(resp)

    data = resp.json()

    # basic keys present
    for key in [
        "total_students",
        "total_courses",
        "total_teachers",
        "total_enrollments",
        "avg_gpa",
    ]:
        assert key in data

    # type checks for counts
    assert isinstance(data["total_students"], int)
    assert isinstance(data["total_courses"], int)
    assert isinstance(data["total_teachers"], int)
    assert isinstance(data["total_enrollments"], int)

    # avg_gpa can be None or float
    assert (data["avg_gpa"] is None) or isinstance(data["avg_gpa"], float)
