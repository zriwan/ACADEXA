# tests/test_role.py
from uuid import uuid4

import pytest


def register_and_token(client, email, password, role):
    r = client.post(
        "/auth/register",
        json={
            "name": "X",
            "email": email,
            "password": password,
            "role": role,  # 'admin' or 'user'
        },
    )
    assert r.status_code in (200, 201), r.text

    # Your login expects FORM data
    t = client.post("/auth/login", data={"username": email, "password": password})
    if t.status_code == 404:
        t = client.post("/auth/token", data={"username": email, "password": password})
    assert t.status_code == 200, t.text
    return t.json()["access_token"]


def find_admin_route(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    # Add your actual admin path here if you know it
    candidates = ["/admin/dashboard", "/admin/overview", "/analytics/overview"]
    for path in candidates:
        r = client.get(path, headers=headers)
        if r.status_code in (200, 401, 403):  # route exists/responds
            return path
    return None


def test_admin_only_route(client):
    admin_email = f"admin_{uuid4().hex[:8]}@example.com"
    user_email = f"user_{uuid4().hex[:8]}@example.com"

    admin_token = register_and_token(client, admin_email, "AdminPass123", "admin")
    user_token = register_and_token(client, user_email, "UserPass123", "user")

    admin_path = find_admin_route(client, admin_token)
    if not admin_path:
        pytest.skip(
            "No admin-only route found. Add your admin endpoint to candidates in test_role.py"
        )

    ok = client.get(admin_path, headers={"Authorization": f"Bearer {admin_token}"})
    assert ok.status_code == 200, ok.text

    no = client.get(admin_path, headers={"Authorization": f"Bearer {user_token}"})
    assert no.status_code in (401, 403), no.text
