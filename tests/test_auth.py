# tests/test_auth.py
from uuid import uuid4


def login_and_get_token(client, email, password):
    # Your login expects form data with fields 'username' and 'password'
    # Try /auth/login first
    r = client.post("/auth/login", data={"username": email, "password": password})
    if r.status_code == 200 and r.json().get("access_token"):
        return r.json()["access_token"]

    # Fallback to /auth/token if you also expose it
    r = client.post("/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def get_me(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    # Try /auth/me first; fallback to /users/me
    r = client.get("/auth/me", headers=headers)
    if r.status_code != 404:
        return r
    return client.get("/users/me", headers=headers)


def test_register_login_and_access_protected_route(client):
    unique_email = f"user_{uuid4().hex[:8]}@example.com"

    # Register with required fields; role must be 'user' or 'admin'
    reg_payload = {
        "name": "User One",
        "email": unique_email,
        "password": "UserPass123",
        "role": "user",
    }
    r = client.post("/auth/register", json=reg_payload)
    assert r.status_code in (200, 201), r.text

    # Login (form-encoded)
    token = login_and_get_token(client, unique_email, "UserPass123")
    assert token, "No access_token returned from login"

    # Access protected route
    me = get_me(client, token)
    assert me.status_code == 200, me.text
    data = me.json()
    assert data.get("email") == unique_email


def test_login_wrong_password(client):
    # Create a user first
    email = f"user_{uuid4().hex[:8]}@example.com"
    client.post(
        "/auth/register",
        json={
            "name": "User Two",
            "email": email,
            "password": "RightPass123",
            "role": "user",
        },
    )

    # Wrong password using FORM data
    bad = client.post("/auth/login", data={"username": email, "password": "WrongPass"})
    # If you only expose /auth/token:
    if bad.status_code == 404:
        bad = client.post(
            "/auth/token", data={"username": email, "password": "WrongPass"}
        )
    assert bad.status_code in (400, 401), bad.text


def test_protected_without_token(client):
    # Try /auth/me, then fallback to /users/me
    r = client.get("/auth/me")
    if r.status_code == 404:
        r = client.get("/users/me")
    assert r.status_code in (401, 403), r.text
