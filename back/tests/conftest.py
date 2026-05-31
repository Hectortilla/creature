"""Shared pytest fixtures for the backend test suite.

Unit tests build a ``GameState`` entirely in memory (no DB/Redis) via the
``empty_state`` and ``place_card`` factories below. Integration tests use
``db_session``, which is skipped unless ``DATABASE_URL`` points to a reachable
database. See ../AGENTS.md ("Writing tests") and ../../docs/harness.md.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.game.effects import build_effect_atoms
from app.models.game.card import EffectSpec, GameCard
from app.models.game.enums import Zone
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameState


@pytest.fixture
def empty_state() -> GameState:
    """A two-player game with empty zones and empty decks."""
    room = GameRoom(room_id="r", host_id="p1")
    room.add_player(PlayerState(player_id="p1", name="P1", deck=[]))
    room.add_player(PlayerState(player_id="p2", name="P2", deck=[]))
    return GameState.create(room)


@pytest.fixture
def place_card() -> Callable[..., GameCard]:
    """Factory that places a ``GameCard`` into a zone of ``state`` for ``owner_id``.

    Shared form of the inline helper in ``tests/unit/test_effects.py`` so new
    tests can build scenarios without copy-pasting the construction boilerplate.
    """

    def _place(
        state: GameState,
        owner_id: str,
        zone: Zone,
        specs: list[EffectSpec] | None = None,
        **fields: object,
    ) -> GameCard:
        card = GameCard.create(
            card_id=fields.pop("card_id", 1),
            owner_id=owner_id,
            name=fields.pop("name", "card"),
            health=fields.pop("health", 50),
            physical_defence=fields.pop("physical_defence", 5),
            magic_defence=fields.pop("magic_defence", 5),
            effect_atoms=build_effect_atoms(specs or []),
            **fields,
        )
        card.zone = zone
        state.cards[card.instance_id] = card
        if zone in (Zone.SUPPORTING, Zone.ATTACKING):
            state.room.players[owner_id].zones[zone.name].card_ids.append(card.instance_id)
        return card

    return _place


@pytest.fixture
def db_session() -> Iterator[Session]:
    """A real database session for integration tests.

    Skipped unless ``DATABASE_URL`` is set and reachable. The default
    ``make test`` excludes the ``integration`` marker, so this runs only in
    CI's integration job (with a Postgres service) or when explicitly selected
    with ``pytest -m integration``.
    """
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("integration test requires DATABASE_URL")

    from app.database import engine

    try:
        engine.connect().close()
    except OperationalError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"database not reachable: {exc}")

    with Session(engine) as session:
        yield session
