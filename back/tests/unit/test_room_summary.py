"""Regression: the lobby room listing must never leak hands, zones, or decks.

`GET /game/rooms` and the WS `list_rooms` reply both serialize `RoomSummary`;
a full `PlayerState` (hand + deck card ids) must never reach a lobby viewer.
"""

import json

import pytest

from app.models.game.enums import GameStatus, Zone
from app.models.game.player import PlayerState
from app.models.game.room import GameRoom
from app.models.game.state import GameState

pytestmark = pytest.mark.unit

SAFE_KEYS = {"room_id", "host_id", "created_at", "players", "is_full", "is_started", "can_join"}


def _room_with_hands() -> GameRoom:
    room = GameRoom(room_id="room-1", host_id="p1")
    alice = PlayerState(player_id="p1", name="Alice", deck=[])
    bob = PlayerState(player_id="p2", name="Bob", deck=[])
    alice.zones[Zone.HAND.name].card_ids.append("alice-secret-card")
    bob.zones[Zone.DECK.name].card_ids.append("bob-secret-card")
    room.add_player(alice)
    room.add_player(bob)
    return room


def test_summary_exposes_only_safe_fields():
    summary = _room_with_hands().to_summary()
    assert set(summary.model_dump().keys()) == SAFE_KEYS
    assert {p.name for p in summary.players} == {"Alice", "Bob"}
    assert summary.is_full is True
    assert summary.can_join is False


def test_summary_never_serializes_hands_or_zones():
    blob = json.dumps(_room_with_hands().to_summary().model_dump(mode="json"))
    for leak in ("alice-secret-card", "bob-secret-card", "zones", "deck", "element_pool", "card_ids"):
        assert leak not in blob


def test_started_room_summary_is_still_clean():
    room = _room_with_hands()
    room.state = GameState.create(room)
    room.state.status = GameStatus.IN_PROGRESS
    summary = room.to_summary()
    assert summary.is_started is True
    assert summary.can_join is False
    assert "card_ids" not in json.dumps(summary.model_dump(mode="json"))
