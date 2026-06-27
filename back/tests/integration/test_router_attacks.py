"""Attack-router HTTP tests: list, get-by-code/name, create + delete, and the
missing-auth negative. Uses the un-overridden ``client`` with a real token so
the auth chain runs (needs Postgres); seeds with high codes.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models.db.user import User

pytestmark = pytest.mark.integration


@pytest.fixture
def codes() -> Callable[[], int]:
    counter = iter(range(9_100_001, 9_110_000))
    return lambda: next(counter)


def test_attacks_require_auth(client: TestClient) -> None:
    assert client.get("/attacks").status_code == 401


def test_create_get_and_delete_attack(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    codes: Callable[[], int],
) -> None:
    header = auth_token(make_user("owner"))
    code = codes()

    created = client.post("/attacks", json={"code": code, "name": "Flamethrower", "damage": 40}, headers=header)
    assert created.status_code == 201
    attack_id = created.json()["id"]
    assert created.json()["damage"] == 40

    assert client.get(f"/attacks/{code}", headers=header).json()["name"] == "Flamethrower"
    assert client.get("/attacks/flamethrower", headers=header).json()["code"] == code
    assert any(a["code"] == code for a in client.get("/attacks", headers=header).json())

    assert client.delete(f"/attacks/{attack_id}", headers=header).status_code == 200
    assert client.delete(f"/attacks/{attack_id}", headers=header).status_code == 404


def test_get_unknown_attack_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    assert client.get("/attacks/no-such-attack", headers=header).status_code == 404
