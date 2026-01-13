# tests/test_voice_commands.py

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from tests.utils_auth import get_auth_headers

client = TestClient(app)


def test_voice_unknown_intent():
    headers = get_auth_headers(client, role="user")

    resp = client.post("/voice/command", json={"text": "open the door please"}, headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["parsed"]["intent"] == "unknown"
    assert "couldn't understand this command" in data["info"].lower()
    assert data["results_type"] is None or data["results_type"] == "" or data["results_type"] is False
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 0


def test_voice_list_courses():
    headers = get_auth_headers(client, role="user")

    resp = client.post("/voice/command", json={"text": "show all courses"}, headers=headers)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["parsed"]["intent"] == "list_courses"
    assert data["results_type"] == "courses"
    assert "course" in data["info"].lower()
    assert isinstance(data["results"], list)


def test_voice_list_students_in_course():
    headers = get_auth_headers(client, role="user")

    resp = client.post(
        "/voice/command",
        json={"text": "list students in course cs101"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["parsed"]["intent"] == "list_students"
    assert data["results_type"] == "students"
    assert isinstance(data["results"], list)
    # even if zero results, message should mention students / course
    assert "student" in data["info"].lower()


def test_voice_list_enrollments_for_student():
    headers = get_auth_headers(client, role="user")

    resp = client.post(
        "/voice/command",
        json={"text": "show enrollments for student 3"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["parsed"]["intent"] == "list_enrollments_for_student"
    assert data["results_type"] == "enrollments"
    assert isinstance(data["results"], list)
    # info should talk about enrollments
    assert "enrollment" in data["info"].lower()
