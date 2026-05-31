from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, func, select

from app.models.base.deck import DeckBase
from app.models.db.deck_card import DeckCard
from app.models.game.state import GameConfiguration
from app.utils.time import utcnow

if TYPE_CHECKING:
    from sqlmodel import Session

    from app.models.db.card import Card
    from app.models.db.user import User


class Deck(DeckBase, table=True):
    """Deck database model."""

    __tablename__ = "decks"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="decks")
    # Read-only convenience view of this deck's cards (the writable path is the
    # DeckCard association object below). viewonly avoids overlap with deck_cards.
    cards: list["Card"] = Relationship(
        back_populates="decks",
        link_model=DeckCard,
        sa_relationship_kwargs={"lazy": "selectin", "viewonly": True},
    )
    deck_cards: list[DeckCard] = Relationship(back_populates="deck")

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
        card_count = db.exec(select(func.count(DeckCard.card_id)).where(DeckCard.deck_id == self.id)).one() or 0

        return card_count == GameConfiguration().deck_size
