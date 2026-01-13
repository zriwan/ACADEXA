# tests/utils_auth.py
from __future__ import annotations

from uuid import uuid4
from typing import Dict


def register_user(client, role: str = "user") -> dict:
    """
    Registers a unique user and returns {email, password, role}.
    Uses the same payload structure as tests/test_auth.py.
    """
    email = f"user_{uuid4().hex[:8]}@example.com"
    password = "UserPass123"

    reg_payload = {
        "name": "Test User",
        "email": email,
        "password": password,
        "role": role,  # must be 'user' or 'admin'
    }

    r = client.post("/auth/register", json=reg_payload)
    assert r.status_code in (200, 201), r.text

    return {"email": email, "password": password, "role": role}


def login_and_get_token(client, email: str, password: str) -> str:
    """
    Logs in using FORM data with fields 'username' and 'password'
    (username == email), matching your test_auth.py.
    """
    r = client.post("/auth/login", data={"username": email, "password": password})
    if r.status_code == 200 and r.json().get("access_token"):
        return r.json()["access_token"]

    # Fallback if /auth/token exists
    r = client.post("/auth/token", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    assert r.json().get("access_token"), f"No access_token: {r.json()}"
    return r.json()["access_token"]


def get_auth_headers(client, role: str = "user") -> Dict[str, str]:
    """
    Registers a fresh user, logs in, returns Authorization header.
    Use role='admin' if the endpoint is admin-restricted.
    """
    user = register_user(client, role=role)
    token = login_and_get_token(client, user["email"], user["password"])
    return {"Authorization": f"Bearer {token}"}
