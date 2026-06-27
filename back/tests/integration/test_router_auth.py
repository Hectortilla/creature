"""Auth-router HTTP tests: register/login/me happy paths, negatives, and the
cross-user authz-isolation pattern (seed two users, real per-user tokens, assert
each token only ever sees its own caller) reused by the deck/card router steps.

Uses the un-overridden ``client`` so the real ``oauth2_scheme`` chain runs and
asserts the status codes the routers actually return (needs Postgres).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models.db.user import User

pytestmark = pytest.mark.integration


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"username": "newbie", "email": "newbie@example.com", "password": "secret"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newbie"
    assert body["email"] == "newbie@example.com"
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_username_is_400(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user("taken")
    response = client.post("/auth/register", json={"username": "taken", "password": "secret"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_register_duplicate_email_is_400(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user("first", email="dup@example.com")
    response = client.post(
        "/auth/register",
        json={"username": "second", "email": "dup@example.com", "password": "secret"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_token_with_good_credentials_returns_bearer(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user("loginuser", password="hunter2")
    response = client.post("/auth/token", data={"username": "loginuser", "password": "hunter2"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_token_with_bad_password_is_401(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user("loginuser", password="hunter2")
    response = client.post("/auth/token", data={"username": "loginuser", "password": "wrong"})
    assert response.status_code == 401


def test_token_with_unknown_user_is_401(client: TestClient) -> None:
    response = client.post("/auth/token", data={"username": "ghost", "password": "secret"})
    assert response.status_code == 401


def test_me_with_real_bearer_returns_current_user(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    user = make_user("me-user", email="me@example.com")
    response = client.get("/auth/me", headers=auth_token(user))
    assert response.status_code == 200
    assert response.json()["username"] == "me-user"


def test_me_without_auth_is_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_isolates_users_by_token(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    alice = make_user("alice")
    bob = make_user("bob")

    assert client.get("/auth/me", headers=auth_token(alice)).json()["username"] == "alice"
    assert client.get("/auth/me", headers=auth_token(bob)).json()["username"] == "bob"
