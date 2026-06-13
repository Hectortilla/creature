"""Exemplar API smoke test using FastAPI's ``TestClient``.

Boots the ASGI app and asserts the health endpoint responds. Entering the
``TestClient`` context runs the lifespan, which connects the broadcaster — a
real Redis connection whenever ``REDIS_URL`` is set (CI's backend job provides
one). The DB engine still connects lazily, so this route needs no Postgres.
New endpoint tests follow this shape; DB-backed ones live in
``tests/integration/`` behind the ``integration`` marker.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.unit


def test_root_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
