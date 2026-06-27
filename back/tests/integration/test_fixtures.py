"""Smoke tests for the shared HTTP/DB test harness (Step 1).

Proves the rollback ``session`` never leaks rows to Postgres (even after an
in-request ``.commit()``), that ``auth_client`` reaches a protected endpoint,
and that the bare ``client`` hits the real auth chain on a protected endpoint.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlmodel import Session, select

from app.database import engine
from app.models.db.user import User

pytestmark = pytest.mark.integration


def test_session_rollback_isolates_writes(session: Session, make_user: Callable[..., User]) -> None:
    make_user("leak-probe")
    session.commit()  # an in-request commit must not escape the outer transaction

    with Session(engine) as fresh:
        leaked = fresh.exec(select(User).where(User.username == "leak-probe")).first()
    assert leaked is None


def test_auth_client_reaches_protected_endpoint(auth_client: object) -> None:
    response = auth_client.get("/auth/me")
    assert response.status_code == 200


def test_bare_client_hits_real_auth_chain(client: object) -> None:
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)
