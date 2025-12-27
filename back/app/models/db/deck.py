from sqlmodel import Field, Relationship
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base.deck import DeckBase
from app.models.db.deck_card import DeckCard

if TYPE_CHECKING:
    from app.models.db.user import User
    from app.models.db.card import Card


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

