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
from hypothesis import settings as hypothesis_settings
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.game.effects import build_effect_atoms
from app.models.game.card import EffectSpec, GameCard
from app.models.game.enums import Zone
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameState

# derandomize → same examples every run, so mutmut classifies each mutant stably.
hypothesis_settings.register_profile("deterministic", derandomize=True)
hypothesis_settings.load_profile("deterministic")


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


@pytest.fixture
def session() -> Iterator[Session]:
    """Transactional DB session that rolls back even when routers ``.commit()``.

    Joins a ``Session`` to an external transaction over a single connection and
    restarts a SAVEPOINT after each in-request commit, so the outer transaction
    can be rolled back wholesale on teardown — no row ever reaches Postgres.
    """
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("integration test requires DATABASE_URL")

    from app.database import engine

    try:
        connection = engine.connect()
    except OperationalError as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"database not reachable: {exc}")

    trans = connection.begin()
    db = Session(bind=connection)
    db.begin_nested()

    @event.listens_for(db, "after_transaction_end")
    def _restart_savepoint(sess: Session, transaction: object) -> None:
        if connection.in_nested_transaction():
            return
        connection.begin_nested()

    try:
        yield db
    finally:
        event.remove(db, "after_transaction_end", _restart_savepoint)
        db.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client(session: Session) -> Iterator[object]:
    """``TestClient`` over the rollback ``session``, with NO auth override.

    The real ``oauth2_scheme`` → ``get_current_user`` chain runs, so negative
    auth paths (401/403/400) and real-token cross-user tests are reachable.
    """
    from fastapi.testclient import TestClient

    from app.database import get_db_session
    from app.main import app

    app.dependency_overrides[get_db_session] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(session: Session) -> Callable[..., object]:
    """Factory inserting a ``User`` with a real password hash into ``session``."""
    from app.auth.security import get_password_hash
    from app.models.db.user import User

    def _make(
        username: str = "user",
        password: str = "secret",
        *,
        email: str | None = None,
        disabled: bool = False,
    ) -> User:
        user = User(
            username=username,
            email=email,
            disabled=disabled,
            hashed_password=get_password_hash(password),
        )
        session.add(user)
        session.flush()
        return user

    return _make


@pytest.fixture
def auth_token() -> Callable[[object], dict[str, str]]:
    """Build a real ``Authorization: Bearer`` header for a given user."""
    from app.auth.security import create_access_token

    def _header(user: object) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token({'sub': user.username})}"}

    return _header


@pytest.fixture
def auth_client(client: object, make_user: Callable[..., object]) -> object:
    """Happy-path convenience: ``client`` with ``get_current_active_user`` forced.

    Do NOT use for 401/403 tests — it makes every negative auth path unreachable.
    """
    from app.auth.dependencies import get_current_active_user
    from app.main import app

    user = make_user("happy-path-user")
    app.dependency_overrides[get_current_active_user] = lambda: user
    return client
