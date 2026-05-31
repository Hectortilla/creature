"""
WebSocket Serialization Utilities

Functions for serializing game data for WebSocket communication.
"""

from __future__ import annotations

from typing import Any


def serialize_events(events) -> list[dict[str, Any]]:
    """Serialize a list of game events using Pydantic's model_dump()."""
    return [event.model_dump(mode="json") for event in events]


def serialize_events_for_player(events, player_id: str) -> list[dict[str, Any]]:
    """Serialize events with per-player visibility filtering.

    Hides card identity in opponent's CardDrawnEvents but keeps
    instance_id so the client can animate the card movement.
    """
    result = []
    for event in events:
        data = event.model_dump(mode="json")
        if data.get("event_type") == "CardDrawnEvent" and data.get("player_id") != player_id:
            data["card_id"] = 0
        result.append(data)
    return result
