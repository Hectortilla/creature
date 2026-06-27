"""Regression: per-player event serialization must hide the opponent's drawn card.

`serialize_events_for_player` is the only filter between the engine's full event
stream and what a player's client receives; if its ownership check flips, an
opponent's `card_id` leaks. Mirrors the negative-assertion pattern in
`test_room_summary.py`.
"""

import json

import pytest

from app.models.game.events import CardDrawnEvent
from app.websocket.serialization import serialize_events, serialize_events_for_player

pytestmark = pytest.mark.unit

MY_CARD_ID = 42
OPPONENT_CARD_ID = 99


def _draws() -> list[CardDrawnEvent]:
    return [
        CardDrawnEvent(player_id="p1", instance_id="mine", card_id=MY_CARD_ID, cards_remaining=10),
        CardDrawnEvent(player_id="p2", instance_id="theirs", card_id=OPPONENT_CARD_ID, cards_remaining=10),
    ]


def test_opponent_drawn_card_id_is_masked():
    serialized = serialize_events_for_player(_draws(), "p1")
    mine, theirs = serialized
    assert mine["card_id"] == MY_CARD_ID  # own draw stays visible
    assert theirs["card_id"] == 0  # opponent identity hidden
    assert theirs["instance_id"] == "theirs"  # instance kept so the client can animate


def test_opponent_card_id_never_appears_in_player_payload():
    serialized = serialize_events_for_player(_draws(), "p1")
    for event in serialized:
        del event["timestamp"]  # volatile microseconds coincidentally contain the id digits
    assert str(OPPONENT_CARD_ID) not in json.dumps(serialized)


def test_unfiltered_serialization_does_expose_both():
    blob = json.dumps(serialize_events(_draws()))
    assert str(OPPONENT_CARD_ID) in blob  # proves the mask, not absence, hides it
