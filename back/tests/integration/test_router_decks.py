"""Deck-router HTTP tests: CRUD happy paths, cross-user authz isolation (B's
token never sees or mutates A's deck), and the add/remove-card edges
(non-owned deck, missing card, card-not-in-deck, deck-full).

Uses the un-overridden ``client`` with real per-user tokens (the Step 3
isolation pattern) so the real auth chain runs and the status codes asserted are
the ones the router actually returns (needs Postgres).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.db.card import Card
from app.models.db.deck_card import DeckCard
from app.models.db.user import User

pytestmark = pytest.mark.integration


@pytest.fixture
def make_card(session: Session) -> Callable[..., Card]:
    """Insert a minimal ``Card`` with a fresh high code (avoids seed-row codes)."""
    codes = iter(range(9_000_001, 9_001_000))

    def _make(name: str = "card") -> Card:
        card = Card(code=next(codes), name=name)
        session.add(card)
        session.flush()
        return card

    return _make


def _create_deck(client: TestClient, header: dict[str, str], name: str = "mydeck") -> int:
    response = client.post("/decks", json={"name": name}, headers=header)
    assert response.status_code == 201
    return response.json()["id"]


def test_decks_require_auth(client: TestClient) -> None:
    assert client.get("/decks").status_code == 401


def test_create_and_get_deck(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header, "starter")

    body = client.get(f"/decks/{deck_id}", headers=header).json()
    assert body["name"] == "starter"
    assert body["cards"] == []
    assert body["is_valid_for_playing"] is False


def test_list_and_summaries_return_only_owner_decks(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    alice, bob = auth_token(make_user("alice")), auth_token(make_user("bob"))
    _create_deck(client, alice, "alice-deck")

    assert [d["name"] for d in client.get("/decks", headers=bob).json()] == []
    assert [d["name"] for d in client.get("/decks/summaries", headers=bob).json()] == []
    assert [d["name"] for d in client.get("/decks", headers=alice).json()] == ["alice-deck"]


def test_update_and_delete_deck(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header)

    updated = client.put(f"/decks/{deck_id}", json={"name": "renamed"}, headers=header)
    assert updated.status_code == 200
    assert updated.json()["name"] == "renamed"

    assert client.delete(f"/decks/{deck_id}", headers=header).status_code == 204
    assert client.get(f"/decks/{deck_id}", headers=header).status_code == 404


def test_cross_user_deck_access_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    alice, bob = auth_token(make_user("alice")), auth_token(make_user("bob"))
    deck_id = _create_deck(client, alice, "private")

    assert client.get(f"/decks/{deck_id}", headers=bob).status_code == 404
    assert client.put(f"/decks/{deck_id}", json={"name": "hijack"}, headers=bob).status_code == 404
    assert client.delete(f"/decks/{deck_id}", headers=bob).status_code == 404


def test_add_and_remove_card(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    make_card: Callable[..., Card],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header)
    card_id = make_card().id

    assert client.post(f"/decks/{deck_id}/cards/{card_id}", headers=header).status_code == 204
    assert len(client.get(f"/decks/{deck_id}", headers=header).json()["cards"]) == 1

    assert client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=header).status_code == 204
    assert client.get(f"/decks/{deck_id}", headers=header).json()["cards"] == []


def test_add_card_to_non_owned_deck_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    make_card: Callable[..., Card],
) -> None:
    alice, bob = auth_token(make_user("alice")), auth_token(make_user("bob"))
    deck_id = _create_deck(client, alice)
    card_id = make_card().id

    response = client.post(f"/decks/{deck_id}/cards/{card_id}", headers=bob)
    assert response.status_code == 404
    assert response.json()["detail"] == "Deck not found"


def test_add_missing_card_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header)

    response = client.post(f"/decks/{deck_id}/cards/9999", headers=header)
    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found"


def test_remove_card_not_in_deck_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    make_card: Callable[..., Card],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header)
    card_id = make_card().id

    response = client.delete(f"/decks/{deck_id}/cards/{card_id}", headers=header)
    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found in deck"


def test_add_card_to_full_deck_is_400(
    client: TestClient,
    session: Session,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
    make_card: Callable[..., Card],
) -> None:
    header = auth_token(make_user("owner"))
    deck_id = _create_deck(client, header)
    filler = make_card()
    for _ in range(22):  # GameConfiguration().deck_size
        session.add(DeckCard(deck_id=deck_id, card_id=filler.id))
    session.flush()

    extra = make_card()
    response = client.post(f"/decks/{deck_id}/cards/{extra.id}", headers=header)
    assert response.status_code == 400
    assert "Deck is full" in response.json()["detail"]


def test_get_missing_deck_is_404(
    client: TestClient,
    make_user: Callable[..., User],
    auth_token: Callable[[User], dict[str, str]],
) -> None:
    header = auth_token(make_user("owner"))
    assert client.get("/decks/9999", headers=header).status_code == 404
