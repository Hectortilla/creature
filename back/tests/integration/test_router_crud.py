"""Generic CRUD-factory router tests via one representative instance (elements):
list, get-by-id/label, create + delete, and the missing-auth negative — proving
every ``create_crud_router`` instance enforces ``get_current_active_user``.

Uses the un-overridden ``client`` with a real token (needs Postgres).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models.db.user import User

pytestmark = pytest.mark.integration


def test_crud_router_requires_auth(client: TestClient) -> None:
    assert client.get("/elements").status_code == 401


def test_crud_create_get_and_delete(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))

    created = client.post("/elements", json={"label": "Plasma"}, headers=header)
    assert created.status_code == 201
    element_id = created.json()["id"]

    assert client.get(f"/elements/{element_id}", headers=header).json()["label"] == "Plasma"
    assert client.get("/elements/plasma", headers=header).json()["id"] == element_id
    assert any(e["id"] == element_id for e in client.get("/elements", headers=header).json())

    assert client.delete(f"/elements/{element_id}", headers=header).status_code == 200
    assert client.delete(f"/elements/{element_id}", headers=header).status_code == 404


def test_crud_get_unknown_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    assert client.get("/elements/no-such-element", headers=header).status_code == 404
