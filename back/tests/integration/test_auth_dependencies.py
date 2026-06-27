"""Auth-dependency negatives over the real HTTP chain (needs Postgres).

Drives ``oauth2_scheme`` → ``get_current_user`` → ``get_current_active_user``
through ``GET /auth/me`` using the un-overridden ``client``, so every rejection
path (missing/malformed/expired/wrong-sig token, disabled user, unknown user) is
reachable and asserts the status the code actually returns.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_access_token
from app.models.db.user import User
from app.settings.config import get_settings

pytestmark = pytest.mark.integration

settings = get_settings()


def test_missing_authorization_is_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_malformed_bearer_is_401(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401


def test_expired_bearer_is_401(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user("expired-user")
    expired = create_access_token({"sub": user.username}, expires_delta=timedelta(seconds=-1))
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_wrong_signature_bearer_is_401(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user("wrong-sig-user")
    forged = jwt.encode({"sub": user.username}, "a-different-secret", algorithm=settings.auth_algorithm)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_disabled_user_is_400(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    user = make_user("disabled-user", disabled=True)
    response = client.get("/auth/me", headers=auth_token(user))
    assert response.status_code == 400


def test_unknown_user_is_401(client: TestClient) -> None:
    ghost = create_access_token({"sub": "ghost-who-was-never-created"})
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {ghost}"})
    assert response.status_code == 401
