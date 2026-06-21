"""Regression: `DeckService` must scope every read to the authenticated user.

If the `user_id` filter in `get_user_deck` drops, any user can load (and thus
play) another user's deck. Exercised against real Postgres via `db_session`.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session

from app.models.db.deck import Deck
from app.models.db.user import User
from app.services.decks import DeckService

pytestmark = pytest.mark.integration


def _user(db: Session, username: str) -> User:
    user = User(username=username, hashed_password="x")
    db.add(user)
    db.flush()
    return user


def test_get_user_deck_enforces_ownership(db_session: Session) -> None:
    owner = _user(db_session, "deck-owner")
    intruder = _user(db_session, "deck-intruder")
    deck = Deck(name="owners-deck", user_id=owner.id)
    db_session.add(deck)
    db_session.flush()

    assert DeckService(db_session, owner.id).get_user_deck(deck.id).id == deck.id
    assert DeckService(db_session, intruder.id).get_user_deck(deck.id) is None
    assert DeckService(db_session, intruder.id).get_user_decks() == []
