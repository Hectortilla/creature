from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.db.deck import Deck
    from app.models.db.card import Card


class DeckCard(SQLModel, table=True):
    """Association table for many-to-many relationship between Deck and Card."""
    __tablename__ = "deck_cards"
    
    deck_id: int = Field(foreign_key="decks.id", primary_key=True)
    card_id: int = Field(foreign_key="cards.id", primary_key=True)
    position: int | None = Field(default=None)  # Optional position/order in deck
    
    # Relationships
    deck: "Deck" = Relationship()
    card: "Card" = Relationship()

