"""
WebSocket Serialization Utilities

Functions for serializing game data for WebSocket communication.
"""

from typing import Any

from app.models.game.card import GameCardInput


def serialize_events(events) -> list[dict[str, Any]]:
    """Serialize a list of game events using Pydantic's model_dump()."""
    return [event.model_dump(mode='json') for event in events]


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

