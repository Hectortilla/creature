"""Card-router HTTP tests: list/get-by-code/handle/name, the ``by-*`` lookups,
create + delete, and the missing-auth negative (the factory-shared
``get_current_active_user`` dependency must reject an un-tokened request).

Uses the un-overridden ``client`` with real per-user tokens so the real auth
chain runs (needs Postgres). Reference rows are seeded through ``session`` with
high codes to avoid colliding with pre-seeded ``cards``/``attacks`` rows.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.db.ability import Ability
from app.models.db.association import Association
from app.models.db.attack import Attack
from app.models.db.card import Card
from app.models.db.user import User

pytestmark = pytest.mark.integration


@pytest.fixture
def codes() -> Callable[[], int]:
    counter = iter(range(9_000_001, 9_010_000))
    return lambda: next(counter)


def test_cards_require_auth(client: TestClient) -> None:
    assert client.get("/cards").status_code == 401


def test_create_get_and_delete_card(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    codes: Callable[[], int],
) -> None:
    header = auth_token(make_user("owner"))
    code = codes()

    created = client.post("/cards", json={"code": code, "name": "Pikastorm"}, headers=header)
    assert created.status_code == 201
    card_id = created.json()["id"]

    assert client.get(f"/cards/{code}", headers=header).json()[0]["name"] == "Pikastorm"
    assert client.get("/cards/pikastorm", headers=header).json()[0]["code"] == code
    assert any(c["code"] == code for c in client.get("/cards", headers=header).json())

    assert client.delete(f"/cards/{card_id}", headers=header).status_code == 200
    assert client.delete(f"/cards/{card_id}", headers=header).status_code == 404


def test_get_unknown_card_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    assert client.get("/cards/no-such-card", headers=header).status_code == 404


def test_cards_by_attack_ability_and_association(
    client: TestClient,
    session: Session,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    codes: Callable[[], int],
) -> None:
    header = auth_token(make_user("owner"))
    attack = Attack(code=codes(), name="Thunderbolt")
    ability = Ability(code=codes(), name="Static")
    association = Association(code=codes(), name="Gym")
    session.add_all([attack, ability, association])
    session.flush()

    card = Card(
        code=codes(),
        name="Voltcreature",
        first_attack_id=attack.id,
        ability_id=ability.id,
        association_id=association.id,
    )
    session.add(card)
    session.flush()

    assert client.get(f"/cards/by-attack/{attack.code}", headers=header).json()[0]["code"] == card.code
    assert client.get(f"/cards/by-ability/{ability.code}", headers=header).json()[0]["code"] == card.code
    assert client.get(f"/cards/by-association/{association.code}", headers=header).json()[0]["code"] == card.code
