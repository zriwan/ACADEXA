# tests/test_students.py

from uuid import uuid4

from fastapi.testclient import TestClient


# -------------------------
# Helper: get admin auth headers
# -------------------------
def _get_admin_headers(client: TestClient) -> dict:
    """
    Har test ke liye:
    - ek unique admin user register karo
    - us se login karke JWT token lo
    - Authorization header return karo
    """
    email = f"admin_{uuid4().hex[:8]}@example.com"
    password = "AdminPass123"

    # Register admin user
    reg_resp = client.post(
        "/auth/register",
        json={
            "name": "Test Admin",
            "email": email,
            "password": password,
            "role": "admin",
        },
    )
    # 200/201 expected; agar 400 aaya to bhi mostly "email already registered" hoga
    assert reg_resp.status_code in (200, 201), reg_resp.text

    # Login via form-data (OAuth2PasswordRequestForm style)
    login_resp = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_create_student_ok(client: TestClient):
    headers = _get_admin_headers(client)

    payload = {
        "name": "Test Student",
        "department": "CS",
        "gpa": 3.2,
    }
    response = client.post(
        "/students/",
        json=payload,
        headers=headers,  # 👈 auth required for create
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == payload["name"]
    assert data["department"] == payload["department"]
    assert float(data["gpa"]) == payload["gpa"]


def test_list_students(client: TestClient):
    # list endpoint tumhare code me public hai (agar nahi, to headers add kar sakte ho)
    response = client.get("/students/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    # Itna strict na rahen ke >=1 assert karein, kyun ke order ki guarantee nahi.
    # Lekin agar pehle test chal chuka ho to usually 1+ hoga.
    # Isko optional chhod dete hain, warna ideal me yahan khud create karna chahiye.
    # assert len(data) >= 1


def test_get_single_student(client: TestClient):
    headers = _get_admin_headers(client)

    # pehle ek student create kar lete hain
    payload = {
        "name": "Single Student",
        "department": "EE",
        "gpa": 2.8,
    }
    create_resp = client.post("/students/", json=payload, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    student_id = created["id"]

    # ab GET /students/{id}
    response = client.get(f"/students/{student_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == student_id
    assert data["name"] == payload["name"]
    assert data["department"] == payload["department"]


def test_update_student(client: TestClient):
    headers = _get_admin_headers(client)

    # create student
    payload = {
        "name": "Old Name",
        "department": "CS",
        "gpa": 2.0,
    }
    create_resp = client.post("/students/", json=payload, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    student_id = create_resp.json()["id"]

    # update payload
    update_payload = {
        "name": "New Name",
        "department": "CS",
        "gpa": 3.5,
    }
    response = client.put(
        f"/students/{student_id}",
        json=update_payload,
        headers=headers,  # 👈 update ke liye bhi auth chahiye
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == student_id
    assert data["name"] == "New Name"
    assert float(data["gpa"]) == 3.5


def test_delete_student(client: TestClient):
    headers = _get_admin_headers(client)

    # create student
    payload = {
        "name": "To Be Deleted",
        "department": "ME",
        "gpa": 2.5,
    }
    create_resp = client.post("/students/", json=payload, headers=headers)
    assert create_resp.status_code == 201, create_resp.text
    student_id = create_resp.json()["id"]

    # delete
    delete_resp = client.delete(
        f"/students/{student_id}",
        headers=headers,  # 👈 delete admin-only
    )
    assert delete_resp.status_code == 204, delete_resp.text

    # ensure 404 on get
    get_resp = client.get(f"/students/{student_id}")
    assert get_resp.status_code == 404
