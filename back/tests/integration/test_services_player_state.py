"""``build_player_state`` negatives: it raises ``ValueError`` for an unknown deck,
a deck owned by another user (cross-user isolation), and a deck that exists but is
not valid for play (wrong card count). These are the guards a game start relies
on. Needs Postgres.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from sqlmodel import Session

from app.models.db.user import User
from app.models.schemas.deck import DeckCreate
from app.services.decks import DeckService
from app.services.player_state import build_player_state

pytestmark = pytest.mark.integration


def test_unknown_deck_raises(session: Session, make_user: Callable[..., User]) -> None:
    with pytest.raises(ValueError, match="does not belong"):
        build_player_state(session, make_user("u"), 9_999_999)


def test_cross_user_deck_raises(session: Session, make_user: Callable[..., User]) -> None:
    alice, bob = make_user("alice"), make_user("bob")
    deck = DeckService(session, alice.id).create(DeckCreate(name="d"))

    with pytest.raises(ValueError, match="does not belong"):
        build_player_state(session, bob, deck.id)


def test_invalid_deck_raises(session: Session, make_user: Callable[..., User]) -> None:
    user = make_user("u")
    deck = DeckService(session, user.id).create(DeckCreate(name="d"))  # empty → invalid

    with pytest.raises(ValueError, match="not valid"):
        build_player_state(session, user, deck.id)
