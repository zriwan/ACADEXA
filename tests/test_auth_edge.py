# tests/test_auth_edge.py
from uuid import uuid4

def register(client, email, password, role="user"):
    return client.post("/auth/register", json={
        "name": "Edge User",
        "email": email,
        "password": password,
        "role": role,
    })

def login_form(client, email, password):
    # Your auth uses OAuth2-style form fields
    return client.post("/auth/login", data={"username": email, "password": password})

def test_duplicate_email_rejected(client):
    email = f"dup_{uuid4().hex[:6]}@ex.com"
    r1 = register(client, email, "P@ss12345")
    assert r1.status_code in (200, 201), r1.text
    r2 = register(client, email, "P@ss12345")
    # Your API returns 400 for duplicate. If you ever change, 409 is also common.
    assert r2.status_code in (400, 409), r2.text

def test_invalid_role_rejected(client):
    email = f"badrole_{uuid4().hex[:6]}@ex.com"
    r = client.post("/auth/register", json={
        "name": "X",
        "email": email,
        "password": "P@ss12345",
        "role": "student"  # your API expects 'admin' or 'user'
    })
    assert r.status_code in (400, 422), r.text

def test_token_required_for_me(client):
    # Try /auth/me then /users/me (depending on your app)
    r = client.get("/auth/me")
    if r.status_code == 404:
        r = client.get("/users/me")
    assert r.status_code in (401, 403), r.text

def test_invalid_token(client):
    headers = {"Authorization": "Bearer invalid.token.here"}
    r = client.get("/auth/me", headers=headers)
    if r.status_code == 404:
        r = client.get("/users/me", headers=headers)
    assert r.status_code in (401, 403), r.text
