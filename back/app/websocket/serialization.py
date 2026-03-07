"""
WebSocket Serialization Utilities

Functions for serializing game data for WebSocket communication.
"""

from typing import Any

from app.models.game.card import GameCardInput


def serialize_events(events) -> list[dict[str, Any]]:
    """Serialize a list of game events using Pydantic's model_dump()."""
    return [event.model_dump(mode='json') for event in events]


_HIDDEN_DRAW_FIELDS = {"instance_id": "", "card_id": 0}


def serialize_events_for_player(events, player_id: str) -> list[dict[str, Any]]:
    """Serialize events with per-player visibility filtering.

    Hides card identity in opponent's CardDrawnEvents so the receiving
    player cannot see what the other player drew.
    """
    result = []
    for event in events:
        data = event.model_dump(mode='json')
        if data.get("event_type") == "CardDrawnEvent" and data.get("player_id") != player_id:
            data.update(_HIDDEN_DRAW_FIELDS)
        result.append(data)
    return result


def serialize_deck_for_game(deck_cards: list) -> list[dict[str, Any]]:
    """
    Serialize deck cards to the format expected by the game engine.
    
    Uses Pydantic's GameCardInput model for proper serialization.
    
    Args:
        deck_cards: List of CardReadWithRelations from deck enrichment
        
    Returns:
        List of card dicts in game engine format
    """
    return [
        GameCardInput.from_card_read(card).model_dump(mode='json')
        for card in deck_cards
    ]

