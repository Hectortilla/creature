from sqlmodel import Field, Relationship, select, func
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base.deck import DeckBase
from app.models.db.deck_card import DeckCard
from app.models.game.state import GameConfiguration

if TYPE_CHECKING:
    from app.models.db.user import User
    from app.models.db.card import Card
    from sqlmodel import Session


class Deck(DeckBase, table=True):
    """Deck database model."""
    __tablename__ = "decks"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="decks")
    cards: list["Card"] = Relationship(
        back_populates="decks",
        link_model=DeckCard,
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    deck_cards: list[DeckCard] = Relationship()
    
    def is_valid_for_playing(self, db: "Session") -> bool:
        """
        Check if the deck is valid for playing.
        
        Validates:
        - Deck has the correct number of cards (matches GameConfiguration.deck_size)
        
        Args:
            db: Database session to query deck card count
            
        Returns:
            True if deck is valid for playing, False otherwise
        """
        card_count = db.exec(
            select(func.count(DeckCard.card_id)).where(DeckCard.deck_id == self.id)
        ).one() or 0
        
        return card_count == GameConfiguration().deck_size

