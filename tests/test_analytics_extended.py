import pytest
from fastapi.testclient import TestClient

from backend.main import app
from tests.utils_auth import get_auth_headers

client = TestClient(app)


def test_course_stats_shape():
    # Authenticate as NORMAL USER
    headers = get_auth_headers(client, role="user")

    resp = client.get("/analytics/course-stats", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert isinstance(data, list)

    if not data:
        # empty DB case is allowed
        return

    item = data[0]
    for key in [
        "id",
        "code",
        "title",
        "total_enrollments",
        "avg_grade",
        "pass_rate",
    ]:
        assert key in item

    assert isinstance(item["id"], int)
    assert isinstance(item["code"], str) or item["code"] is None
    assert isinstance(item["title"], str) or item["title"] is None
    assert isinstance(item["total_enrollments"], int)
    assert (item["avg_grade"] is None) or isinstance(item["avg_grade"], float)
    assert (item["pass_rate"] is None) or isinstance(item["pass_rate"], float)



def test_department_stats_shape():
    # Authenticate as NORMAL USER
    headers = get_auth_headers(client, role="user")

    resp = client.get("/analytics/department-stats", headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert isinstance(data, list)

    if not data:
        # empty DB allowed
        return

    item = data[0]
    for key in [
        "department",
        "total_students",
        "total_courses",
        "avg_gpa",
    ]:
        assert key in item

    assert isinstance(item["department"], str)
    assert isinstance(item["total_students"], int)
    assert isinstance(item["total_courses"], int)
    assert (item["avg_gpa"] is None) or isinstance(item["avg_gpa"], float)
