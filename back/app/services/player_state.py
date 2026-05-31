"""
Player-state assembly.

Builds the in-memory PlayerState a game starts from: fetch a user's deck,
validate it, enrich it with full card relations, and serialize it into the
shape the game engine expects. This orchestration lives in the service layer
(not on the User model) so the data layer stays free of service/web imports.
"""

from typing import Any

from sqlmodel import Session

from app.models.db.user import User
from app.models.game.card import GameCardInput
from app.models.game.player import PlayerState
from app.models.schemas.card import CardReadWithRelations
from app.services.decks import DeckService


def serialize_deck_for_game(deck_cards: list[CardReadWithRelations]) -> list[dict[str, Any]]:
    """Serialize enriched deck cards into the format the game engine expects."""
    return [GameCardInput.from_card_read(card).model_dump(mode="json") for card in deck_cards]


def build_player_state(db: Session, user: User, deck_id: int) -> PlayerState:
    """Create a PlayerState from a user and one of their decks.

    Fetches, validates, enriches, and serializes the deck.

    Raises:
        ValueError: If the deck is not found, does not belong to the user, or is invalid.
    """
    deck_service = DeckService(db, user.id)
    deck = deck_service.get_user_deck(deck_id)
    if not deck:
        raise ValueError("Deck not found or does not belong to user")

    if not deck.is_valid_for_playing(db):
        raise ValueError("Deck is not valid for playing")

    enriched_deck = deck_service.get_enriched(deck_id)
    if not enriched_deck:
        raise ValueError("Failed to load deck")

    return PlayerState(
        player_id=str(user.id),
        name=user.full_name or user.username,
        deck=serialize_deck_for_game(enriched_deck.cards),
    )
