# tests/test_students.py
from uuid import uuid4


def make_user_and_token(client, role="admin"):
    email = f"{role}_{uuid4().hex[:6]}@ex.com"
    # Register
    client.post(
        "/auth/register",
        json={"name": role.title(), "email": email, "password": "P@ss12345", "role": role},
    )
    # Login (OAuth2 form fields)
    t = client.post("/auth/login", data={"username": email, "password": "P@ss12345"})
    assert t.status_code == 200, t.text
    return t.json()["access_token"]


def test_create_get_student(client):
    token = make_user_and_token(client, role="admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create student — add required fields: department, gpa
    payload = {
        "name": "Alice",
        "email": f"alice_{uuid4().hex[:4]}@ex.com",
        "department": "CS",
        "gpa": 3.6,
    }
    r = client.post("/students", json=payload, headers=headers)
    assert r.status_code in (200, 201), r.text
    student = r.json()
    sid = student.get("id") or student.get("student_id")

    # Get by id
    g = client.get(f"/students/{sid}", headers=headers)
    assert g.status_code == 200, g.text
    body = g.json()
    assert body.get("name") == "Alice"
    # Optional extra checks if present in response:
    if "department" in body:
        assert body["department"] == "CS"
    if "gpa" in body:
        assert float(body["gpa"]) == 3.6


def test_list_students_pagination(client):
    token = make_user_and_token(client, role="admin")
    headers = {"Authorization": f"Bearer {token}"}

    # Create a few (with required fields)
    for i in range(3):
        client.post(
            "/students",
            json={
                "name": f"S{i}",
                "email": f"s{i}_{uuid4().hex[:4]}@ex.com",
                "department": "CS",
                "gpa": 3.0 + i * 0.1,
            },
            headers=headers,
        )

    # Adjust query params to match your API: ?skip=&limit=
    res = client.get("/students?skip=0&limit=2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 2
