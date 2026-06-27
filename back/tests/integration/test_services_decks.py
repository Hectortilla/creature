"""DeckService tests: per-user scoping, the constructor's user-id assertion, and
the ``add_card_to_deck`` / ``remove_card_from_deck`` ``HTTPException`` edges
(missing deck, missing card, deck full, card-not-in-deck).

These are the authz + limit boundaries of the most security-sensitive service;
a dropped owner check or limit lets one user mutate another's deck. Needs
Postgres.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.models.db.card import Card
from app.models.db.deck_card import DeckCard
from app.models.db.user import User
from app.models.schemas.deck import DeckCreate
from app.services.decks import DeckService

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


def test_constructor_requires_user_id(session: Session) -> None:
    with pytest.raises(AssertionError):
        DeckService(session, None)


def test_get_user_deck_is_scoped_by_user(session: Session, make_user: Callable[..., User]) -> None:
    alice, bob = make_user("alice"), make_user("bob")
    deck = DeckService(session, alice.id).create(DeckCreate(name="d"))

    assert DeckService(session, alice.id).get_user_deck(deck.id).id == deck.id
    assert DeckService(session, bob.id).get_user_deck(deck.id) is None
    assert DeckService(session, bob.id).get_user_decks() == []


def test_add_card_to_missing_deck_raises_404(session: Session, make_user: Callable[..., User]) -> None:
    svc = DeckService(session, make_user("u").id)

    with pytest.raises(HTTPException) as exc:
        svc.add_card_to_deck(9_999_999, 1)
    assert exc.value.status_code == 404


def test_add_missing_card_raises_404(session: Session, make_user: Callable[..., User]) -> None:
    svc = DeckService(session, make_user("u").id)
    deck = svc.create(DeckCreate(name="d"))

    with pytest.raises(HTTPException) as exc:
        svc.add_card_to_deck(deck.id, 9_999_999)
    assert exc.value.status_code == 404


def test_add_card_to_full_deck_raises_400(
    session: Session, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    svc = DeckService(session, make_user("u").id)
    deck = svc.create(DeckCreate(name="d"))
    filler = make_card()
    for _ in range(svc.deck_size):
        session.add(DeckCard(deck_id=deck.id, card_id=filler.id))
    session.flush()

    with pytest.raises(HTTPException) as exc:
        svc.add_card_to_deck(deck.id, make_card().id)
    assert exc.value.status_code == 400


def test_remove_card_not_in_deck_raises_404(
    session: Session, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    svc = DeckService(session, make_user("u").id)
    deck = svc.create(DeckCreate(name="d"))

    with pytest.raises(HTTPException) as exc:
        svc.remove_card_from_deck(deck.id, make_card().id)
    assert exc.value.status_code == 404


def test_add_then_remove_card_roundtrips(
    session: Session, make_user: Callable[..., User], make_card: Callable[..., Card]
) -> None:
    svc = DeckService(session, make_user("u").id)
    deck = svc.create(DeckCreate(name="d"))
    card = make_card()

    assert svc.add_card_to_deck(deck.id, card.id) is True
    assert svc.get_deck_card_count(deck.id) == 1
    assert svc.remove_card_from_deck(deck.id, card.id) is True
    assert svc.get_deck_card_count(deck.id) == 0
