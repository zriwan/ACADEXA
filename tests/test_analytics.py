import pytest
from fastapi.testclient import TestClient

from backend.main import app
from tests.utils_auth import get_auth_headers

client = TestClient(app)


def test_analytics_summary_shape():
    headers = get_auth_headers(client)  # ✅ login -> token -> Authorization header

    resp = client.get("/analytics/summary", headers=headers)
    assert resp.status_code == 200, resp.text

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
    