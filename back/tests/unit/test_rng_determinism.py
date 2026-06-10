"""Per-game seeded-RNG determinism: a fixed ``GameConfiguration.seed`` reproduces the
opening deal + first player; ``None``/different seeds don't.
"""

from __future__ import annotations

import pytest

from app.models.game.enums import Zone
from tests.unit.test_engine_smoke import _build_game

pytestmark = pytest.mark.unit


def _opening_deal(seed: int | None) -> tuple[str, list[int]]:
    """Start a game with ``seed``; return (first_player_id, hand ``card_id``s in draw order).

    Compared by ``card_id`` since ``instance_id`` is a non-reproducible uuid.
    """
    engine, state = _build_game(seed=seed)
    result = engine.start_game(state)
    assert result.success, result.error
    first_player_id = result.state.active_player_id
    assert first_player_id is not None
    hand_ids = result.state.room.players[first_player_id].zones[Zone.HAND.name].card_ids
    hand = [card.card_id for cid in hand_ids if (card := result.state.get_card(cid))]
    return first_player_id, hand


def test_same_seed_reproduces_opening_deal() -> None:
    assert _opening_deal(42) == _opening_deal(42)


def test_different_seeds_diverge() -> None:
    # Different seeds should disagree on the deal and/or first player.
    assert _opening_deal(1) != _opening_deal(2)


def test_unseeded_games_are_independent() -> None:
    # seed=None ⇒ system entropy; compare raw rng streams (not a deal) to avoid rare-collision flakiness.
    _, s1 = _build_game(seed=None)
    _, s2 = _build_game(seed=None)
    assert [s1.rng.random() for _ in range(32)] != [s2.rng.random() for _ in range(32)]


def test_rng_excluded_from_serialized_state() -> None:
    engine, state = _build_game(seed=7)
    engine.start_game(state)
    payload = state.serialize_for_player(state.active_player_id or "p1").model_dump()
    assert "rng" not in payload
    assert "_rng" not in payload
    assert "rng" not in (payload.get("config") or {})
